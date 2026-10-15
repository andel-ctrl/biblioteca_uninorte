from django.urls import path
from . import views

app_name = 'catalogos'

urlpatterns = [
    path('inicio/', views.inicio, name='inicio'),
    # Libros
    path('libros/', views.libro_list, name='libro_list'),
    path('libros/nuevo/', views.libro_create, name='libro_create'),
    path('libros/<int:pk>/', views.libro_detail, name='libro_detail'),
    path('libros/<int:pk>/editar/', views.libro_edit, name='libro_edit'),
    path('libros/<int:pk>/eliminar/', views.libro_delete, name='libro_delete'),
    # Ejemplares
    path('libros/<int:libro_pk>/ejemplares/nuevo/', views.ejemplar_create, name='ejemplar_create'),
    path('ejemplares/<int:pk>/editar/', views.ejemplar_edit, name='ejemplar_edit'),
    path('ejemplares/<int:pk>/eliminar/', views.ejemplar_delete, name='ejemplar_delete'),
    # Autores
    path('autores/', views.autor_list, name='autor_list'),
    path('autores/nuevo/', views.autor_create, name='autor_create'),
    path('autores/<int:pk>/editar/', views.autor_edit, name='autor_edit'),
    path('autores/<int:pk>/eliminar/', views.autor_delete, name='autor_delete'),
    path('autores/rapido/', views.autor_rapido, name='autor_rapido'),
]
