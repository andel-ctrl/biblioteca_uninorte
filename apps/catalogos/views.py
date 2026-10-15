from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum, ProtectedError
from .models import Libro, Ejemplar, Autor, Categoria
from apps.prestamos.models import Prestamo, Devolucion
from .forms import LibroForm, EjemplarForm, AutorForm
from apps.usuarios.decorators import bibliotecario_required


# ── Libros

LIBROS_POR_PAGINA = 12

# Ordenamientos disponibles en el catálogo: valor del parámetro -> (etiqueta, orden SQL)
ORDENES = {
    'titulo': ('Título (A–Z)', ['titulo']),
    'recientes': ('Incorporados recientemente', ['-creado_en', 'titulo']),
    'anio': ('Año de publicación (recientes)', ['-anio_publicacion', 'titulo']),
}


def libros_con_disponibilidad():
    """Libros con sus conteos de ejemplares en una sola consulta (evita una consulta por libro)."""
    return Libro.objects.select_related('categoria').prefetch_related('autores').annotate(
        n_ejemplares=Count('ejemplares', distinct=True),
        n_disponibles=Count('ejemplares', filter=Q(ejemplares__estado='disponible'), distinct=True),
    )


@login_required
def libro_list(request):
    query = request.GET.get('q', '').strip()
    categoria_id = request.GET.get('categoria', '')
    disponible = request.GET.get('disponible', '')
    orden = request.GET.get('orden', 'titulo')
    if orden not in ORDENES:
        orden = 'titulo'
    if not categoria_id.isdigit():  # evita error 500 con valores no numéricos en la URL
        categoria_id = ''

    libros = libros_con_disponibilidad()

    if query:
        libros = libros.filter(
            Q(titulo__icontains=query) |
            Q(isbn__icontains=query) |
            Q(autores__nombre__icontains=query) |
            Q(autores__apellido__icontains=query)
        ).distinct()

    if categoria_id:
        libros = libros.filter(categoria_id=categoria_id)

    if disponible == '1':
        libros = libros.filter(n_disponibles__gt=0)

    paginador = Paginator(libros.order_by(*ORDENES[orden][1]), LIBROS_POR_PAGINA)
    pagina = paginador.get_page(request.GET.get('pagina'))

    # Parámetros actuales sin la página: los enlaces de paginación conservan los filtros
    filtros = request.GET.copy()
    filtros.pop('pagina', None)

    context = {
        'libros': pagina,
        'pagina': pagina,
        'paginador': paginador,
        'numeros_pagina': list(paginador.get_elided_page_range(pagina.number, on_each_side=1, on_ends=1)),
        'filtros_url': filtros.urlencode(),
        'categorias': Categoria.objects.all(),
        'query': query,
        'categoria_id': categoria_id,
        'disponible': disponible,
        'orden': orden,
        'ordenes': [(clave, etiqueta) for clave, (etiqueta, _) in ORDENES.items()],
    }
    return render(request, 'catalogos/libro_list.html', context)


NOVEDADES = 5
SELECCION = 20


@login_required
def inicio(request):
    """Inicio del lector: bienvenida, búsqueda, su estado, novedades y una selección del catálogo."""
    novedades = list(libros_con_disponibilidad().order_by('-creado_en')[:NOVEDADES])
    total_titulos = Libro.objects.count()
    seleccion = libros_con_disponibilidad().order_by('titulo')
    if total_titulos > 12:  # con un catálogo pequeño se repiten las novedades para que la sección no quede vacía
        seleccion = seleccion.exclude(pk__in=[l.pk for l in novedades])
    seleccion = seleccion[:SELECCION]

    estado = None
    perfil = getattr(request.user, 'perfil', None)
    if perfil is not None:
        Prestamo.actualizar_vencidos()
        mios = perfil.prestamos.select_related('ejemplar__libro').order_by('fecha_vencimiento', '-fecha_solicitud')
        activos = [p for p in mios if p.estado == 'activo']
        vencidos = [p for p in mios if p.estado == 'vencido']
        pendientes = [p for p in mios if p.estado == 'pendiente']
        multas = Devolucion.objects.filter(prestamo__usuario=perfil, monto_multa__gt=0, multa_pagada=False)
        estado = {
            'perfil': perfil,
            'activos': activos,
            'vencidos': vencidos,
            'pendientes': pendientes,
            'multas': list(multas.select_related('prestamo__ejemplar__libro')),
            'multas_total': multas.aggregate(total=Sum('monto_multa'))['total'] or 0,
            'mora_total': sum((p.multa_estimada() for p in vencidos), 0),
        }

    return render(request, 'catalogos/inicio.html', {
        'novedades': novedades,
        'seleccion': seleccion,
        'total_titulos': total_titulos,
        'categorias': Categoria.objects.all(),
        'estado': estado,
    })


@login_required
def libro_detail(request, pk):
    libro = get_object_or_404(Libro, pk=pk)
    ejemplares = libro.ejemplares.all()
    return render(request, 'catalogos/libro_detail.html', {'libro': libro, 'ejemplares': ejemplares})


@bibliotecario_required
def libro_create(request):
    if request.method == 'POST':
        form = LibroForm(request.POST, request.FILES)
        if form.is_valid():
            libro = form.save()
            messages.success(request, f'Libro "{libro.titulo}" creado correctamente.')
            return redirect('catalogos:libro_detail', pk=libro.pk)
    else:
        form = LibroForm()
    return render(request, 'catalogos/libro_form.html', {'form': form, 'titulo': 'Nuevo Libro'})


@bibliotecario_required
def libro_edit(request, pk):
    libro = get_object_or_404(Libro, pk=pk)
    if request.method == 'POST':
        form = LibroForm(request.POST, request.FILES, instance=libro)
        if form.is_valid():
            form.save()
            messages.success(request, 'Libro actualizado.')
            return redirect('catalogos:libro_detail', pk=pk)
    else:
        form = LibroForm(instance=libro)
    return render(request, 'catalogos/libro_form.html', {'form': form, 'titulo': 'Editar Libro', 'libro': libro})


@bibliotecario_required
def libro_delete(request, pk):
    libro = get_object_or_404(Libro, pk=pk)
    if request.method == 'POST':
        titulo = libro.titulo
        try:
            libro.delete()
        except ProtectedError:
            # PROTECT en Prestamo.ejemplar impide borrar ejemplares con historial de préstamos
            messages.error(request, f'No se puede eliminar "{titulo}" porque sus ejemplares tienen préstamos registrados. Esto protege el historial.')
            return redirect('catalogos:libro_detail', pk=pk)
        messages.success(request, f'Libro "{titulo}" eliminado.')
        return redirect('catalogos:libro_list')
    return render(request, 'catalogos/libro_confirm_delete.html', {'libro': libro})


#  Ejemplares

@bibliotecario_required
def ejemplar_create(request, libro_pk):
    libro = get_object_or_404(Libro, pk=libro_pk)
    if request.method == 'POST':
        form = EjemplarForm(request.POST)
        if form.is_valid():
            ejemplar = form.save(commit=False)
            ejemplar.libro = libro
            ejemplar.save()
            messages.success(request, 'Ejemplar agregado correctamente.')
            return redirect('catalogos:libro_detail', pk=libro_pk)
    else:
        form = EjemplarForm()
    return render(request, 'catalogos/ejemplar_form.html', {'form': form, 'libro': libro})


@bibliotecario_required
def ejemplar_edit(request, pk):
    ejemplar = get_object_or_404(Ejemplar, pk=pk)
    if request.method == 'POST':
        form = EjemplarForm(request.POST, instance=ejemplar)
        if form.is_valid():
            form.save()
            messages.success(request, 'Ejemplar actualizado.')
            return redirect('catalogos:libro_detail', pk=ejemplar.libro.pk)
    else:
        form = EjemplarForm(instance=ejemplar)
    return render(request, 'catalogos/ejemplar_form.html', {'form': form, 'libro': ejemplar.libro})


@bibliotecario_required
def ejemplar_delete(request, pk):
    ejemplar = get_object_or_404(Ejemplar, pk=pk)
    libro_pk = ejemplar.libro.pk
    if request.method == 'POST':
        try:
            ejemplar.delete()
        except ProtectedError:
            messages.error(request, f'No se puede eliminar el ejemplar {ejemplar.codigo_barras} porque tiene préstamos registrados. Si ya no está en circulación, márquelo como perdido.')
            return redirect('catalogos:libro_detail', pk=libro_pk)
        messages.success(request, 'Ejemplar eliminado.')
        return redirect('catalogos:libro_detail', pk=libro_pk)
    return render(request, 'catalogos/ejemplar_confirm_delete.html', {'ejemplar': ejemplar})


# Autores

@login_required
def autor_list(request):
    autores = Autor.objects.annotate(total_libros=Count('libros'))
    return render(request, 'catalogos/autor_list.html', {'autores': autores})


@bibliotecario_required
def autor_create(request):
    if request.method == 'POST':
        form = AutorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Autor creado.')
            return redirect('catalogos:autor_list')
    else:
        form = AutorForm()
    return render(request, 'catalogos/autor_form.html', {'form': form})
