from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Libro, Ejemplar, Autor, Categoria
from .forms import LibroForm, EjemplarForm, AutorForm
from apps.usuarios.decorators import bibliotecario_required


# ── Libros

@login_required
def libro_list(request):
    query = request.GET.get('q', '')
    categoria_id = request.GET.get('categoria', '')
    disponible = request.GET.get('disponible', '')

    libros = Libro.objects.prefetch_related('autores', 'ejemplares').select_related('categoria')

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
        libros = libros.filter(ejemplares__estado='disponible').distinct()

    categorias = Categoria.objects.all()
    context = {
        'libros': libros,
        'categorias': categorias,
        'query': query,
        'categoria_id': categoria_id,
        'disponible': disponible,
    }
    return render(request, 'catalogos/libro_list.html', context)


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
        libro.delete()
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
        ejemplar.delete()
        messages.success(request, 'Ejemplar eliminado.')
        return redirect('catalogos:libro_detail', pk=libro_pk)
    return render(request, 'catalogos/ejemplar_confirm_delete.html', {'ejemplar': ejemplar})


# Autores

@login_required
def autor_list(request):
    autores = Autor.objects.all()
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
