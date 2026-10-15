from django.shortcuts import render
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from apps.prestamos.models import Prestamo
from apps.catalogos.models import Libro, Ejemplar
from apps.usuarios.models import UsuarioBiblioteca
from apps.usuarios.decorators import bibliotecario_required
import datetime


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
    Prestamo.actualizar_vencidos()

    total_libros = Libro.objects.count()
    total_ejemplares = Ejemplar.objects.count()
    ejemplares_disponibles = Ejemplar.objects.filter(estado='disponible').count()
    ejemplares_prestados = Ejemplar.objects.filter(estado='prestado').count()
    ejemplares_perdidos = Ejemplar.objects.filter(estado='perdido').count()

    prestamos_pendientes = Prestamo.objects.filter(estado='pendiente').count()
    prestamos_activos = Prestamo.objects.filter(estado='activo').count()
    prestamos_vencidos = Prestamo.objects.filter(estado='vencido').count()
    total_usuarios = UsuarioBiblioteca.objects.count()

    ultimos_prestamos = Prestamo.objects.select_related(
        'usuario__user', 'ejemplar__libro'
    ).order_by('-fecha_solicitud')[:10]

    context = {
        'total_libros': total_libros,
        'total_ejemplares': total_ejemplares,
        'disponibles': ejemplares_disponibles,
        'prestados': ejemplares_prestados,
        'perdidos': ejemplares_perdidos,
        'pendientes': prestamos_pendientes,
        'activos': prestamos_activos,
        'vencidos': prestamos_vencidos,
        'total_usuarios': total_usuarios,
        'ultimos_prestamos': ultimos_prestamos,
    }
    return render(request, 'reportes/dashboard.html', context)


@bibliotecario_required
def prestamos_activos(request):
    Prestamo.actualizar_vencidos()
    prestamos = Prestamo.objects.filter(
        estado__in=['activo', 'vencido']
    ).select_related('usuario__user', 'ejemplar__libro').order_by('fecha_vencimiento')
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

    filtro = _filtro_prestados('prestamos__', desde, hasta)
    usuarios = UsuarioBiblioteca.objects.select_related('user').annotate(
        total_prestamos=Count('prestamos', filter=filtro),
        total_activos=Count('prestamos', filter=filtro & Q(prestamos__estado='activo')),
        total_vencidos=Count('prestamos', filter=filtro & Q(prestamos__estado='vencido')),
        total_devueltos=Count('prestamos', filter=filtro & Q(prestamos__estado='devuelto')),
        total_perdidos=Count('prestamos', filter=filtro & Q(prestamos__estado='perdido')),
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
