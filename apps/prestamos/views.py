from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.db import transaction
from .models import Prestamo, Devolucion, ConfiguracionMulta
from .forms import AprobarPrestamoForm, AmpliarPlazoForm, DevolucionForm, TarifaMultaForm
from apps.catalogos.models import Ejemplar
from apps.usuarios.models import UsuarioBiblioteca
from apps.usuarios.decorators import bibliotecario_required, es_bibliotecario_o_staff
from apps.catalogos.formato import formato_pesos


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

    # Cuenta bloqueada, préstamos vencidos o multas sin pagar: primero ponerse al día
    restriccion = perfil.mensaje_restriccion()
    if restriccion:
        messages.error(request, restriccion)
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

    # Se valida otra vez: desde la solicitud el lector pudo ser bloqueado, vencer un préstamo o recibir una multa
    if not prestamo.usuario.esta_activo():
        messages.error(request, f'No se puede aprobar: el usuario {prestamo.usuario.get_nombre_completo()} está bloqueado.')
        return redirect('prestamos:prestamo_list')
    restriccion = prestamo.usuario.mensaje_restriccion(para_el_lector=False)
    if restriccion:
        messages.error(request, f'No se puede aprobar todavía: {restriccion} Debe ponerse al día primero.')
        return redirect('prestamos:prestamo_list')

    if request.method == 'POST':
        form = AprobarPrestamoForm(request.POST)
        if form.is_valid():
            try:
                perfil = request.user.perfil
            except UsuarioBiblioteca.DoesNotExist:
                perfil = None
            try:
                otras = prestamo.aprobar(perfil, form.cleaned_data['fecha_vencimiento'])
            except ValueError as e:
                messages.error(request, str(e))
                return redirect('prestamos:prestamo_list')
            messages.success(request, f'Préstamo #{prestamo.pk} aprobado. Vence el {prestamo.fecha_vencimiento:%d/%m/%Y}.')
            if otras:
                messages.info(request, f'Se rechazaron automáticamente {otras} solicitud{"es" if otras > 1 else ""} más de este ejemplar, porque ya quedó prestado.')
            # Volver a la pantalla desde donde se aprobó (p. ej. la mesa de trabajo), solo si es del propio sitio
            destino = request.POST.get('next', '')
            if destino and url_has_allowed_host_and_scheme(destino, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
                return redirect(destino)
            return redirect('prestamos:prestamo_list')
    else:
        form = AprobarPrestamoForm()

    return render(request, 'prestamos/prestamo_aprobar.html', {'prestamo': prestamo, 'form': form})


@bibliotecario_required
def prestamo_ampliar(request, pk):
    # Ampliar el plazo de un préstamo activo (renovación): solo cambia la fecha de vencimiento
    prestamo = get_object_or_404(Prestamo, pk=pk)
    if not prestamo.puede_ampliarse():
        if prestamo.estado == 'vencido':
            messages.error(request, 'Un préstamo vencido no se puede ampliar: primero registra la devolución.')
        elif prestamo.estado == 'activo':
            messages.error(request, f'Este préstamo ya llegó al máximo de {Prestamo.DIAS_PRESTAMO_MAXIMO} días.')
        else:
            messages.error(request, 'Solo se puede ampliar el plazo de un préstamo activo.')
        return redirect('prestamos:prestamo_detail', pk=prestamo.pk)

    if request.method == 'POST':
        form = AmpliarPlazoForm(request.POST, prestamo=prestamo)
        if form.is_valid():
            try:
                perfil = request.user.perfil
            except UsuarioBiblioteca.DoesNotExist:
                perfil = None
            anterior = prestamo.fecha_vencimiento
            prestamo.ampliar_plazo(form.cleaned_data['fecha_vencimiento'], perfil)
            messages.success(request, f'Plazo ampliado: vencía el {anterior:%d/%m/%Y} y ahora vence el {prestamo.fecha_vencimiento:%d/%m/%Y}.')
            return redirect('prestamos:prestamo_detail', pk=prestamo.pk)
    else:
        form = AmpliarPlazoForm(prestamo=prestamo)

    return render(request, 'prestamos/prestamo_ampliar.html', {'prestamo': prestamo, 'form': form})


@bibliotecario_required
def multa_pagar(request, pk):
    # Registrar en el mostrador el pago de una multa que quedó pendiente al devolver
    prestamo = get_object_or_404(Prestamo.objects.select_related('devolucion', 'usuario__user', 'ejemplar__libro'), pk=pk)
    devolucion = getattr(prestamo, 'devolucion', None)
    if not devolucion or devolucion.monto_multa <= 0 or devolucion.multa_pagada:
        messages.info(request, 'Este préstamo no tiene una multa pendiente de pago.')
        return redirect('prestamos:prestamo_detail', pk=prestamo.pk)
    if request.method == 'POST':
        devolucion.multa_pagada = True
        devolucion.save(update_fields=['multa_pagada'])
        messages.success(request, f'Pago de {formato_pesos(devolucion.monto_multa)} registrado para {prestamo.usuario.get_nombre_completo()}.')
        destino = request.POST.get('next', '')
        if destino and url_has_allowed_host_and_scheme(destino, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
            return redirect(destino)
        return redirect('prestamos:prestamo_detail', pk=prestamo.pk)
    return render(request, 'prestamos/multa_pagar.html', {'prestamo': prestamo, 'devolucion': devolucion, 'siguiente': request.GET.get('next', '')})


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
        form = DevolucionForm(request.POST, prestamo=prestamo)
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
                f'Devolución registrada. Multa: {formato_pesos(devolucion.monto_multa)}'
                if devolucion.monto_multa > 0 else 'Devolución registrada sin multa.'
            )
            if devolucion.estado_ejemplar_resultante() == 'mantenimiento':
                messages.warning(
                    request,
                    f'El ejemplar {prestamo.ejemplar.codigo_barras} quedó en mantenimiento por la observación '
                    f'«{devolucion.get_observacion_display()}». Cuando sea revisado, edítalo y márcalo como disponible.'
                )
            return redirect('prestamos:prestamo_list')
    else:
        form = DevolucionForm(prestamo=prestamo)

    multa_estimada = prestamo.multa_estimada()
    return render(request, 'prestamos/devolucion_form.html', {
        'tarifa': ConfiguracionMulta.tarifa_vigente(),
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
            + (f' Multa por mora: {formato_pesos(devolucion.monto_multa)}.' if devolucion.monto_multa > 0 else ' Sin multa por mora.')
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
                messages.info(request, f'La tarifa ya es {formato_pesos(nueva_tarifa)} por día. No se hicieron cambios.')
                return redirect('prestamos:multa_config')
            # No se sobrescribe la tarifa anterior: se desactiva y se crea un registro nuevo (queda el historial)
            with transaction.atomic():
                ConfiguracionMulta.objects.filter(activa=True).update(activa=False)
                ConfiguracionMulta.objects.create(
                    tarifa_por_dia=nueva_tarifa, vigencia_desde=timezone.localdate(), activa=True
                )
            messages.success(request, f'Nueva tarifa de multa: {formato_pesos(nueva_tarifa)} por día, vigente desde hoy.')
            return redirect('prestamos:multa_config')
    else:
        form = TarifaMultaForm(initial={'tarifa_por_dia': vigente.tarifa_por_dia if vigente else None})

    historial = ConfiguracionMulta.objects.order_by('-vigencia_desde', '-pk')
    return render(request, 'prestamos/multa_config.html', {
        'form': form,
        'vigente': vigente,
        'historial': historial,
    })
