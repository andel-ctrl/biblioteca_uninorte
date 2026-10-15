from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from .models import Prestamo, Devolucion, ConfiguracionMulta
from .forms import AprobarPrestamoForm, DevolucionForm, TarifaMultaForm
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
    Prestamo.actualizar_vencidos()
    prestamos = Prestamo.objects.select_related(
        'usuario__user', 'ejemplar__libro', 'aprobado_por__user'
    ).order_by('-fecha_solicitud')

    if estado:
        prestamos = prestamos.filter(estado=estado)

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

    # Se valida otra vez: el usuario pudo ser bloqueado después de hacer la solicitud
    if not prestamo.usuario.esta_activo():
        messages.error(request, f'No se puede aprobar: el usuario {prestamo.usuario.get_nombre_completo()} está bloqueado.')
        return redirect('prestamos:prestamo_list')

    if request.method == 'POST':
        form = AprobarPrestamoForm(request.POST)
        if form.is_valid():
            try:
                perfil = request.user.perfil
            except UsuarioBiblioteca.DoesNotExist:
                perfil = None
            prestamo.aprobar(perfil, form.cleaned_data['fecha_vencimiento'])
            messages.success(request, f'Préstamo #{prestamo.pk} aprobado. Vence el {prestamo.fecha_vencimiento:%d/%m/%Y}.')
            return redirect('prestamos:prestamo_list')
    else:
        form = AprobarPrestamoForm()

    return render(request, 'prestamos/prestamo_aprobar.html', {'prestamo': prestamo, 'form': form})


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
            if devolucion.estado_ejemplar_resultante() == 'mantenimiento':
                messages.warning(
                    request,
                    f'El ejemplar {prestamo.ejemplar.codigo_barras} quedó en mantenimiento por la observación '
                    f'"{devolucion.get_observacion_display()}". Cuando sea revisado, edítelo y márquelo como disponible.'
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


@bibliotecario_required
def prestamo_reportar_perdida(request, pk):
    prestamo = get_object_or_404(Prestamo, pk=pk, estado__in=['activo', 'vencido'])

    if request.method == 'POST':
        try:
            perfil = request.user.perfil
        except UsuarioBiblioteca.DoesNotExist:
            perfil = None
        devolucion = prestamo.reportar_perdida(perfil)
        messages.warning(
            request,
            f'Préstamo #{prestamo.pk} cerrado por pérdida. El ejemplar {prestamo.ejemplar.codigo_barras} quedó como perdido.'
            + (f' Multa por mora: ${devolucion.monto_multa}.' if devolucion.monto_multa > 0 else ' Sin multa por mora.')
        )
        return redirect('prestamos:prestamo_detail', pk=prestamo.pk)

    return render(request, 'prestamos/prestamo_perdida.html', {
        'prestamo': prestamo,
        'multa_estimada': prestamo.multa_estimada(),
    })

# Tarifa de multa (solo bibliotecario)

@bibliotecario_required
def multa_config(request):
    vigente = ConfiguracionMulta.objects.filter(activa=True).order_by('-vigencia_desde', '-pk').first()

    if request.method == 'POST':
        form = TarifaMultaForm(request.POST)
        if form.is_valid():
            nueva_tarifa = form.cleaned_data['tarifa_por_dia']
            if vigente and vigente.tarifa_por_dia == nueva_tarifa:
                messages.info(request, f'La tarifa ya es ${nueva_tarifa} por día. No se hicieron cambios.')
                return redirect('prestamos:multa_config')
            # No se sobrescribe la tarifa anterior: se desactiva y se crea un registro nuevo (queda el historial)
            with transaction.atomic():
                ConfiguracionMulta.objects.filter(activa=True).update(activa=False)
                ConfiguracionMulta.objects.create(
                    tarifa_por_dia=nueva_tarifa, vigencia_desde=timezone.localdate(), activa=True
                )
            messages.success(request, f'Nueva tarifa de multa: ${nueva_tarifa} por día, vigente desde hoy.')
            return redirect('prestamos:multa_config')
    else:
        form = TarifaMultaForm(initial={'tarifa_por_dia': vigente.tarifa_por_dia if vigente else None})

    historial = ConfiguracionMulta.objects.order_by('-vigencia_desde', '-pk')
    return render(request, 'prestamos/multa_config.html', {
        'form': form,
        'vigente': vigente,
        'historial': historial,
    })
