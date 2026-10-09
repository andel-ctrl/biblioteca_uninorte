from django.contrib import admin
from .models import Autor, Categoria, Libro, Ejemplar


@admin.register(Autor)
class AutorAdmin(admin.ModelAdmin):
    list_display = ('apellido', 'nombre')
    search_fields = ('nombre', 'apellido')


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)


class EjemplarInline(admin.TabularInline):
    model = Ejemplar
    extra = 1
    fields = ('codigo_barras', 'ubicacion', 'estado')


@admin.register(Libro)
class LibroAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'isbn', 'editorial', 'anio_publicacion', 'categoria', 'ejemplares_disponibles')
    list_filter = ('categoria', 'anio_publicacion')
    search_fields = ('titulo', 'isbn', 'autores__apellido')
    filter_horizontal = ('autores',)
    inlines = [EjemplarInline]


@admin.register(Ejemplar)
class EjemplarAdmin(admin.ModelAdmin):
    list_display = ('codigo_barras', 'libro', 'ubicacion', 'estado')
    list_filter = ('estado',)
    search_fields = ('codigo_barras', 'libro__titulo')
