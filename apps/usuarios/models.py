from django.db import models
from django.contrib.auth.models import User


class UsuarioBiblioteca(models.Model):
    ROL_CHOICES = [
        ('estudiante', 'Estudiante'),
        ('docente', 'Docente'),
        ('bibliotecario', 'Bibliotecario'),
    ]
    ESTADO_CHOICES = [
        ('activo', 'Activo'),
        ('bloqueado', 'Bloqueado'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    codigo_universitario = models.CharField(max_length=20, unique=True, verbose_name='Código universitario')
    identificacion = models.CharField(max_length=20, unique=True, verbose_name='Número de identificación')
    rol = models.CharField(max_length=20, choices=ROL_CHOICES, default='estudiante')
    carrera = models.CharField(max_length=150, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='activo')
    telefono = models.CharField(max_length=20, blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Usuario de Biblioteca'
        verbose_name_plural = 'Usuarios de Biblioteca'

    def __str__(self):
        return f"{self.user.get_full_name()} [{self.codigo_universitario}]"

    def esta_activo(self):
        return self.estado == 'activo'

    def es_bibliotecario(self):
        return self.rol == 'bibliotecario'

    def prestamos_activos(self):
        return self.prestamos.filter(estado__in=['activo', 'vencido']).count()

    def get_nombre_completo(self):
        return self.user.get_full_name() or self.user.username
