from django.urls import path
from . import views

app_name = 'reportes'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('prestamos-activos/', views.prestamos_activos, name='prestamos_activos'),
    path('libros-mas-prestados/', views.libros_mas_prestados, name='libros_mas_prestados'),
    path('usuarios-mas-prestamos/', views.usuarios_mas_prestamos, name='usuarios_mas_prestamos'),
    path('inventario/', views.inventario, name='inventario'),
]
