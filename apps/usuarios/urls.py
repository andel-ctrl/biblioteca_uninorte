from django.urls import path
from . import views

app_name = 'usuarios'

urlpatterns = [
    path('', views.usuario_list, name='usuario_list'),
    path('nuevo/', views.usuario_create, name='usuario_create'),
    path('<int:pk>/', views.usuario_detail, name='usuario_detail'),
    path('<int:pk>/editar/', views.usuario_edit, name='usuario_edit'),
    path('<int:pk>/eliminar/', views.usuario_delete, name='usuario_delete'),
    path('mi-historial/', views.mi_historial, name='mi_historial'),
]
