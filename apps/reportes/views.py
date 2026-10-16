from django.shortcuts import render
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from apps.prestamos.models import Prestamo, Devolucion
from apps.catalogos.models import Libro, Ejemplar
from apps.usuarios.models import Usuario
from apps.usuarios.decorators import bibliotecario_required
import datetime
from apps.catalogos.formato import formato_pesos


def _rango_fechas(request, dias_defecto=None):
    """Lee ?desde=AAAA-MM-DD&hasta=AAAA-MM-DD de la URL.
    Si no vienen, usa los últimos `dias_defecto` días (o sin rango si es None).
    Si vienen mal escritas o invertidas, avisa y usa el valor por defecto."""
    hoy = timezone.localdate()
    defecto = (hoy - datetime.timedelta(days=dias_defecto), hoy) if dias_defecto else (None, None)
    desde_txt = request.GET.get('desde', '').strip()
    hasta_txt = request.GET.get('hasta', '').strip()
    if not desde_txt and not hasta_txt:
        return defecto
    try:
        desde = datetime.date.fromisoformat(desde_txt) if desde_txt else None
        hasta = datetime.date.fromisoformat(hasta_txt) if hasta_txt else hoy
    except ValueError:
        messages.warning(request, 'Las fechas del filtro no son válidas. Se muestra el periodo por defecto.')
        return defecto
    if desde and desde > hasta:
        messages.warning(request, 'La fecha "Desde" no puede ser posterior a "Hasta". Se muestra el periodo por defecto.')
        return defecto
    return desde, hasta


def _atajos(incluir_historico=False):
    hoy = timezone.localdate()
    atajos = [(f'Últimos {d} días', hoy - datetime.timedelta(days=d), hoy) for d in (7, 30, 90)]
    atajos.append(('Último año', hoy - datetime.timedelta(days=365), hoy))
    if incluir_historico:
        atajos.append(('Histórico', None, None))
    return atajos


def _filtro_prestados(prefijo, desde, hasta):
    # Solo préstamos que realmente salieron: tienen fecha_prestamo (pendientes y rechazados no)
    filtro = Q(**{f'{prefijo}fecha_prestamo__isnull': False})
    if desde:
        filtro &= Q(**{f'{prefijo}fecha_prestamo__gte': desde})
    if hasta:
        filtro &= Q(**{f'{prefijo}fecha_prestamo__lte': hasta})
    return filtro


@bibliotecario_required
def dashboard(request):
    """Mesa de trabajo: lo que requiere acción primero, con acceso directo a cada tarea."""
    Prestamo.actualizar_vencidos()
    hoy = timezone.localdate()

    # Bandeja: solicitudes pendientes, la más antigua primero
    solicitudes = list(Prestamo.objects.filter(estado='pendiente')
                       .select_related('lector__usuario__user', 'ejemplar__libro').order_by('fecha_solicitud'))
    for p in solicitudes:
        # Mismas validaciones que hará la vista de aprobación, mostradas de antemano
        r = p.lector.restriccion_solicitudes()
        if r and r['tipo'] == 'bloqueada':
            p.bloqueo = 'El lector está bloqueado'
        elif r and r['tipo'] == 'vencidos':
            p.bloqueo = f"Tiene {r['n']} préstamo{'s' if r['n'] > 1 else ''} vencido{'s' if r['n'] > 1 else ''} sin devolver"
        elif r:
            p.bloqueo = f"Tiene {formato_pesos(r['monto'])} en multas sin pagar"
        else:
            p.bloqueo = 'El ejemplar ya no está disponible' if not p.ejemplar.esta_disponible() else ''

    vencidos = list(Prestamo.objects.filter(estado='vencido')
                    .select_related('lector__usuario__user', 'ejemplar__libro').order_by('fecha_vencimiento'))
    proximos = list(Prestamo.objects.filter(estado='activo', fecha_vencimiento__lte=hoy + datetime.timedelta(days=3))
                    .select_related('lector__usuario__user', 'ejemplar__libro').order_by('fecha_vencimiento'))
    for p in proximos:
        p.dias_restantes = (p.fecha_vencimiento - hoy).days

    # La colección hoy (una consulta por tabla)
    inventario = Ejemplar.objects.aggregate(
        total=Count('id'),
        disponible=Count('id', filter=Q(estado='disponible')),
        prestado=Count('id', filter=Q(estado='prestado')),
        mantenimiento=Count('id', filter=Q(estado='mantenimiento')),
        perdido=Count('id', filter=Q(estado='perdido')),
    )
    # La sección «Lectores» de la mesa cuenta solo el subtipo lector
    usuarios = Usuario.objects.filter(tipo='lector').aggregate(
        total=Count('id'), activos=Count('id', filter=Q(estado='activo')), bloqueados=Count('id', filter=Q(estado='bloqueado')),
    )
    prestamos_activos = Prestamo.objects.filter(estado='activo').count()

    # Actividad reciente: solicitudes y cierres (devoluciones o pérdidas) por fecha real
    eventos = [{'tipo': 'solicitud', 'fecha': p.fecha_solicitud, 'prestamo': p}
               for p in Prestamo.objects.select_related('lector__usuario__user', 'ejemplar__libro').order_by('-fecha_solicitud')[:8]]
    eventos += [{'tipo': 'perdida' if d.observacion == 'perdido' else 'devolucion', 'fecha': d.creado_en, 'prestamo': d.prestamo, 'devolucion': d}
                for d in Devolucion.objects.select_related('prestamo__lector__usuario__user', 'prestamo__ejemplar__libro').order_by('-creado_en')[:8]]
    eventos = sorted(eventos, key=lambda e: e['fecha'], reverse=True)[:8]

    context = {
        'hoy': hoy,
        'solicitudes': solicitudes,
        'vencidos_lista': vencidos,
        'proximos': proximos,
        'tareas': len(solicitudes) + len(vencidos) + len(proximos),
        'atencion': len(vencidos) + len(proximos),
        'fecha_aprobacion_defecto': hoy + datetime.timedelta(days=Prestamo.DIAS_PRESTAMO_DEFECTO),
        'dias_defecto': Prestamo.DIAS_PRESTAMO_DEFECTO,
        'inventario': inventario,
        'usuarios_resumen': usuarios,
        'eventos': eventos,
        # Variables anteriores (se conservan por compatibilidad)
        'total_libros': Libro.objects.count(),
        'total_ejemplares': inventario['total'],
        'disponibles': inventario['disponible'],
        'prestados': inventario['prestado'],
        'perdidos': inventario['perdido'],
        'pendientes': len(solicitudes),
        'activos': prestamos_activos,
        'vencidos': len(vencidos),
        'total_usuarios': usuarios['total'],
    }
    return render(request, 'reportes/dashboard.html', context)


@bibliotecario_required
def prestamos_activos(request):
    Prestamo.actualizar_vencidos()
    prestamos = Prestamo.objects.filter(
        estado__in=['activo', 'vencido']
    ).select_related('lector__usuario__user', 'ejemplar__libro').order_by('fecha_vencimiento')
    return render(request, 'reportes/prestamos_activos.html', {'prestamos': prestamos})


@bibliotecario_required
def libros_mas_prestados(request):
    desde, hasta = _rango_fechas(request, dias_defecto=30)

    libros = Libro.objects.annotate(
        total_prestamos=Count('ejemplares__prestamos', filter=_filtro_prestados('ejemplares__prestamos__', desde, hasta))
    ).filter(total_prestamos__gt=0).select_related('categoria').prefetch_related('autores').order_by('-total_prestamos', 'titulo')[:20]

    return render(request, 'reportes/libros_mas_prestados.html', {
        'libros': libros,
        'desde': desde,
        'hasta': hasta,
        'atajos': _atajos(),
    })


@bibliotecario_required
def usuarios_mas_prestamos(request):
    desde, hasta = _rango_fechas(request)
    Prestamo.actualizar_vencidos()

    # Solo los lectores piden préstamos (subtipo lector)
    filtro = _filtro_prestados('lector__prestamos__', desde, hasta)
    usuarios = Usuario.objects.select_related('user', 'lector').annotate(
        total_prestamos=Count('lector__prestamos', filter=filtro),
        total_activos=Count('lector__prestamos', filter=filtro & Q(lector__prestamos__estado='activo')),
        total_vencidos=Count('lector__prestamos', filter=filtro & Q(lector__prestamos__estado='vencido')),
        total_devueltos=Count('lector__prestamos', filter=filtro & Q(lector__prestamos__estado='devuelto')),
        total_perdidos=Count('lector__prestamos', filter=filtro & Q(lector__prestamos__estado='perdido')),
    ).filter(total_prestamos__gt=0).order_by('-total_prestamos', 'user__last_name')[:20]

    return render(request, 'reportes/usuarios_mas_prestamos.html', {
        'usuarios': usuarios,
        'desde': desde,
        'hasta': hasta,
        'atajos': _atajos(incluir_historico=True),
    })


@bibliotecario_required
def inventario(request):
    ejemplares = Ejemplar.objects.select_related('libro').order_by('estado', 'libro__titulo')
    por_estado = {
        'disponible': ejemplares.filter(estado='disponible'),
        'prestado': ejemplares.filter(estado='prestado'),
        'perdido': ejemplares.filter(estado='perdido'),
        'mantenimiento': ejemplares.filter(estado='mantenimiento'),
    }
    return render(request, 'reportes/inventario.html', {'por_estado': por_estado, 'ejemplares': ejemplares})
