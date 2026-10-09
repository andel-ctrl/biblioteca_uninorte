from django.shortcuts import render
from django.db.models import Count, Q
from django.utils import timezone
from apps.prestamos.models import Prestamo
from apps.catalogos.models import Libro, Ejemplar
from apps.usuarios.models import UsuarioBiblioteca
from apps.usuarios.decorators import bibliotecario_required
import datetime


@bibliotecario_required
def dashboard(request):
    hoy = timezone.now().date()

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
    prestamos = Prestamo.objects.filter(
        estado__in=['activo', 'vencido']
    ).select_related('usuario__user', 'ejemplar__libro').order_by('fecha_vencimiento')
    return render(request, 'reportes/prestamos_activos.html', {'prestamos': prestamos})


@bibliotecario_required
def libros_mas_prestados(request):
    periodo = request.GET.get('periodo', '30')  # días
    desde = timezone.now().date() - datetime.timedelta(days=int(periodo))

    libros = Libro.objects.annotate(
        total_prestamos=Count(
            'ejemplares__prestamos',
            filter=Q(ejemplares__prestamos__fecha_prestamo__gte=desde)
        )
    ).order_by('-total_prestamos')[:20]

    return render(request, 'reportes/libros_mas_prestados.html', {
        'libros': libros,
        'periodo': periodo,
    })


@bibliotecario_required
def usuarios_mas_prestamos(request):
    usuarios = UsuarioBiblioteca.objects.annotate(
        total_prestamos=Count('prestamos')
    ).order_by('-total_prestamos')[:20]
    return render(request, 'reportes/usuarios_mas_prestamos.html', {'usuarios': usuarios})


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
