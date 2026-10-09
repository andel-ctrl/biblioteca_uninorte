from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Prestamo, Devolucion
from .forms import PrestamoForm, DevolucionForm
from apps.catalogos.models import Ejemplar
from apps.usuarios.models import UsuarioBiblioteca
from apps.usuarios.decorators import bibliotecario_required, es_bibliotecario_o_staff


# Solicitar prestamo

@login_required
def prestamo_solicitar(request, ejemplar_pk):
    # El usuario solicita el préstamo de un ejemplar específico.
    ejemplar = get_object_or_404(Ejemplar, pk=ejemplar_pk)

    # Validaciones
    if not ejemplar.esta_disponible():
        messages.error(request, 'Este ejemplar no está disponible.')
        return redirect('catalogos:libro_detail', pk=ejemplar.libro.pk)

    try:
        perfil = request.user.perfil
    except UsuarioBiblioteca.DoesNotExist:
        messages.error(request, 'No tienes perfil de biblioteca activo para solicitar libros.')
        return redirect('catalogos:libro_list')

    if not perfil.esta_activo():
        messages.error(request, 'Tu cuenta está bloqueada. Contacta al personal bibliotecario.')
        return redirect('catalogos:libro_detail', pk=ejemplar.libro.pk)

    # Verificar que no tenga ya ese ejemplar solicitado o activo
    if Prestamo.objects.filter(usuario=perfil, ejemplar=ejemplar, estado__in=['pendiente', 'activo', 'vencido']).exists():
        messages.warning(request, 'Ya tienes una solicitud o préstamo activo para este ejemplar.')
        return redirect('catalogos:libro_detail', pk=ejemplar.libro.pk)

    if request.method == 'POST':
        prestamo = Prestamo.objects.create(usuario=perfil, ejemplar=ejemplar)
        messages.success(request, 'Solicitud de préstamo enviada. Espera la aprobación del bibliotecario.')
        return redirect('usuarios:mi_historial')

    return render(request, 'prestamos/prestamo_confirmar.html', {'ejemplar': ejemplar})


# Lista de prestamos (solo bibliotecario)

@bibliotecario_required
def prestamo_list(request):
    estado = request.GET.get('estado', '')
    prestamos = Prestamo.objects.select_related(
        'usuario__user', 'ejemplar__libro', 'aprobado_por__user'
    ).order_by('-fecha_solicitud')

    if estado:
        prestamos = prestamos.filter(estado=estado)

    # Actualizar estado a vencido si aplica
    for p in prestamos:
        if p.esta_vencido():
            p.estado = 'vencido'
            p.save()

    return render(request, 'prestamos/prestamo_list.html', {
        'prestamos': prestamos,
        'estado_filtro': estado,
        'estados': Prestamo.ESTADO_CHOICES,
    })


@login_required
def prestamo_detail(request, pk):
    prestamo = get_object_or_404(Prestamo, pk=pk)
    # Si no es bibliotecario ni staff, solo puede ver su propio préstamo
    if not es_bibliotecario_o_staff(request.user):
        if not hasattr(request.user, 'perfil') or prestamo.usuario != request.user.perfil:
            messages.error(request, 'No tienes permiso para ver este préstamo.')
            return redirect('usuarios:mi_historial')
    return render(request, 'prestamos/prestamo_detail.html', {'prestamo': prestamo})


# Aprobar o rechazar prestamos (solo bibliotecario)

@bibliotecario_required
def prestamo_aprobar(request, pk):
    prestamo = get_object_or_404(Prestamo, pk=pk, estado='pendiente')

    if not prestamo.ejemplar.esta_disponible():
        messages.error(request, 'El ejemplar ya no está disponible.')
        return redirect('prestamos:prestamo_list')

    if request.method == 'POST':
        try:
            perfil = request.user.perfil
        except UsuarioBiblioteca.DoesNotExist:
            perfil = None
        prestamo.aprobar(perfil)
        messages.success(request, f'Préstamo #{prestamo.pk} aprobado. Vence el {prestamo.fecha_vencimiento}.')
        return redirect('prestamos:prestamo_list')

    return render(request, 'prestamos/prestamo_aprobar.html', {'prestamo': prestamo})


@bibliotecario_required
def prestamo_rechazar(request, pk):
    prestamo = get_object_or_404(Prestamo, pk=pk, estado='pendiente')

    if request.method == 'POST':
        try:
            perfil = request.user.perfil
        except UsuarioBiblioteca.DoesNotExist:
            perfil = None
        prestamo.rechazar(perfil)
        messages.warning(request, f'Préstamo #{prestamo.pk} rechazado.')
        return redirect('prestamos:prestamo_list')

    return render(request, 'prestamos/prestamo_rechazar.html', {'prestamo': prestamo})


# El manejo de las devoluciones (solo bibliotecario)

@bibliotecario_required
def devolucion_registrar(request, prestamo_pk):
    prestamo = get_object_or_404(Prestamo, pk=prestamo_pk, estado__in=['activo', 'vencido'])

    if request.method == 'POST':
        form = DevolucionForm(request.POST)
        if form.is_valid():
            devolucion = form.save(commit=False)
            devolucion.prestamo = prestamo
            try:
                devolucion.registrado_por = request.user.perfil
            except UsuarioBiblioteca.DoesNotExist:
                pass
            devolucion.save()
            messages.success(
                request,
                f'Devolución registrada. Multa: ${devolucion.monto_multa}'
                if devolucion.monto_multa > 0 else 'Devolución registrada sin multa.'
            )
            return redirect('prestamos:prestamo_list')
    else:
        form = DevolucionForm()

    multa_estimada = prestamo.multa_estimada()
    return render(request, 'prestamos/devolucion_form.html', {
        'form': form,
        'prestamo': prestamo,
        'multa_estimada': multa_estimada,
    })
