from django.urls import path
from . import views

app_name = 'prestamos'

urlpatterns = [
    path('', views.prestamo_list, name='prestamo_list'),
    path('<int:pk>/', views.prestamo_detail, name='prestamo_detail'),
    path('solicitar/<int:ejemplar_pk>/', views.prestamo_solicitar, name='prestamo_solicitar'),
    path('<int:pk>/aprobar/', views.prestamo_aprobar, name='prestamo_aprobar'),
    path('<int:pk>/rechazar/', views.prestamo_rechazar, name='prestamo_rechazar'),
    path('<int:prestamo_pk>/devolver/', views.devolucion_registrar, name='devolucion_registrar'),
]
