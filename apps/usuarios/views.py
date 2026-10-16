from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.db.models import Count, ProtectedError, Q
from django.utils import timezone
from .models import Usuario
from apps.prestamos.models import Prestamo
from .forms import UsuarioForm, RegistroForm, ROL_CHOICES
from .decorators import bibliotecario_required


@bibliotecario_required
def usuario_list(request):
    # Lista de usuarios de la biblioteca (solo bibliotecario), con búsqueda y filtros
    query = request.GET.get('q', '').strip()
    rol = request.GET.get('rol', '')
    estado = request.GET.get('estado', '')

    # Los préstamos son del subtipo lector (un bibliotecario siempre tiene 0)
    usuarios = Usuario.objects.select_related('user', 'lector', 'bibliotecario').annotate(
        n_activos=Count('lector__prestamos', filter=Q(lector__prestamos__estado__in=['activo', 'vencido'])),
        n_vencidos=Count('lector__prestamos', filter=Q(lector__prestamos__estado='vencido')),
    )
    if query:
        usuarios = usuarios.filter(
            Q(user__first_name__unaccent__icontains=query) | Q(user__last_name__unaccent__icontains=query) |
            Q(user__username__icontains=query) | Q(user__email__icontains=query) |
            Q(codigo_universitario__icontains=query) | Q(identificacion__icontains=query)
        )
    if rol == 'bibliotecario':
        usuarios = usuarios.filter(tipo='bibliotecario')
    elif rol in dict(ROL_CHOICES):
        usuarios = usuarios.filter(lector__rol=rol)
    if estado in dict(Usuario.ESTADO_CHOICES):
        usuarios = usuarios.filter(estado=estado)

    return render(request, 'usuarios/usuario_list.html', {
        'usuarios': usuarios.order_by('user__last_name', 'user__first_name'),
        'query': query, 'rol': rol, 'estado': estado,
        'roles': ROL_CHOICES, 'estados': Usuario.ESTADO_CHOICES,
    })


@bibliotecario_required
def usuario_create(request):
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            messages.success(request, f'Usuario {usuario.user.get_full_name()} creado correctamente.')
            return redirect('usuarios:usuario_list')
    else:
        form = RegistroForm()
    return render(request, 'usuarios/usuario_form.html', {'form': form, 'titulo': 'Nuevo Usuario'})


@bibliotecario_required
def usuario_detail(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)
    Prestamo.actualizar_vencidos()
    lector = getattr(usuario, 'lector', None)
    prestamos = list(lector.prestamos.select_related('ejemplar__libro', 'devolucion__multa').order_by('-fecha_solicitud')) if lector else []
    multas = [p.devolucion for p in prestamos if hasattr(p, 'devolucion') and p.devolucion.monto_multa > 0]
    resumen = {
        'total': sum(1 for p in prestamos if p.fecha_prestamo),
        'en_curso': sum(1 for p in prestamos if p.estado in ('activo', 'vencido')),
        'vencidos': sum(1 for p in prestamos if p.estado == 'vencido'),
        'pendientes': sum(1 for p in prestamos if p.estado == 'pendiente'),
        'multas_por_pagar': sum((d.monto_multa for d in multas if not d.multa_pagada), 0),
    }
    return render(request, 'usuarios/usuario_detail.html', {'usuario': usuario, 'prestamos': prestamos, 'resumen': resumen})


@bibliotecario_required
def usuario_edit(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)
    if request.method == 'POST':
        form = UsuarioForm(request.POST, instance=usuario, editor=request.user)
        if form.is_valid():
            form.save()
            if form.es_su_propia_cuenta() and form.cleaned_data.get('nueva_password'):
                # Al cambiar la propia contraseña Django cierra la sesión; esto la mantiene abierta
                update_session_auth_hash(request, usuario.user)
            messages.success(request, 'Usuario actualizado.')
            return redirect('usuarios:usuario_detail', pk=pk)
    else:
        form = UsuarioForm(instance=usuario, editor=request.user)
    return render(request, 'usuarios/usuario_form.html', {
        'form': form, 'titulo': f'Editar Usuario: {usuario.get_nombre_completo()}', 'usuario': usuario,
    })


@bibliotecario_required
def usuario_delete(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)
    if usuario.user_id == request.user.pk:
        messages.error(request, 'No puedes eliminar tu propia cuenta.')
        return redirect('usuarios:usuario_detail', pk=pk)
    if request.method == 'POST':
        nombre = usuario.get_nombre_completo()
        try:
            usuario.user.delete()
        except ProtectedError:
            # PROTECT en prestamo.lector impide borrar lectores con historial de préstamos
            messages.error(request, f'No se puede eliminar a «{nombre}» porque tiene préstamos registrados. Puedes cambiar su estado a bloqueado.')
            return redirect('usuarios:usuario_detail', pk=pk)
        messages.success(request, f'Usuario «{nombre}» eliminado.')
        return redirect('usuarios:usuario_list')
    return render(request, 'usuarios/usuario_confirm_delete.html', {'usuario': usuario})


@login_required
def mi_historial(request):
    perfil = getattr(request.user, 'perfil', None)
    if perfil is None:
        messages.error(request, 'No tienes perfil de biblioteca asociado.')
        return redirect('catalogos:libro_list')
    if not perfil.es_lector():  # especialización disjunta: el bibliotecario no tiene préstamos propios
        messages.info(request, 'El personal bibliotecario no solicita préstamos.')
        return redirect('reportes:dashboard')
    Prestamo.actualizar_vencidos()
    prestamos = list(
        perfil.lector.prestamos.select_related('ejemplar__libro', 'devolucion__multa').prefetch_related('ejemplar__libro__autores')
        .order_by('-fecha_solicitud')
    )

    # Línea de tiempo de los préstamos en curso: qué parte del plazo ya pasó
    hoy = timezone.localdate()
    en_curso = sorted([p for p in prestamos if p.estado in ('activo', 'vencido')], key=lambda p: p.fecha_vencimiento)
    for p in en_curso:
        plazo = max((p.fecha_vencimiento - p.fecha_prestamo).days, 1)
        transcurrido = (hoy - p.fecha_prestamo).days
        p.progreso = min(100, max(0, round(transcurrido * 100 / plazo)))
        p.dias_restantes = (p.fecha_vencimiento - hoy).days

    historial = [p for p in prestamos if p.estado in ('devuelto', 'rechazado', 'perdido')]
    multas_pendientes = [p for p in historial if hasattr(p, 'devolucion') and p.devolucion.monto_multa > 0 and not p.devolucion.multa_pagada]

    pendientes = [p for p in prestamos if p.estado == 'pendiente']
    return render(request, 'usuarios/mi_historial.html', {
        'prestamos': prestamos,
        'perfil': perfil,
        'en_curso': en_curso,
        'pendientes': pendientes,
        'resumen': f'{len(en_curso)} en curso · {len(pendientes)} por aprobar · {len(historial)} en el historial',
        'historial': historial,
        'multas_pendientes_total': sum((p.devolucion.monto_multa for p in multas_pendientes), 0),
    })
