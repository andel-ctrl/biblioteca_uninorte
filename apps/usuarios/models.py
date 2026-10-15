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
        constraints = [
            models.CheckConstraint(condition=models.Q(rol__in=['estudiante', 'docente', 'bibliotecario']), name='usuario_rol_valido',
                violation_error_message='El rol no es válido.'),
            models.CheckConstraint(condition=models.Q(estado__in=['activo', 'bloqueado']), name='usuario_estado_valido',
                violation_error_message='El estado de la cuenta no es válido.'),
        ]

    def __str__(self):
        return f"{self.user.get_full_name()} [{self.codigo_universitario}]"

    def esta_activo(self):
        return self.estado == 'activo'

    def es_bibliotecario(self):
        return self.rol == 'bibliotecario'

    def restriccion_solicitudes(self):
        """Por qué no puede pedir libros ahora (o None si puede): cuenta bloqueada,
        préstamos vencidos sin devolver o multas sin pagar. Se pone al día y queda libre."""
        from django.db.models import Q, Sum
        from django.utils import timezone
        if not self.esta_activo():
            return {'tipo': 'bloqueada'}
        hoy = timezone.localdate()
        vencidos = self.prestamos.filter(Q(estado='vencido') | Q(estado='activo', fecha_vencimiento__lt=hoy)).count()
        if vencidos:
            return {'tipo': 'vencidos', 'n': vencidos}
        deuda = self.prestamos.filter(devolucion__monto_multa__gt=0, devolucion__multa_pagada=False).aggregate(
            total=Sum('devolucion__monto_multa'))['total']
        if deuda:
            return {'tipo': 'multas', 'monto': deuda}
        return None

    def mensaje_restriccion(self, para_el_lector=True):
        from apps.catalogos.formato import formato_pesos
        r = self.restriccion_solicitudes()
        if not r:
            return ''
        if r['tipo'] == 'bloqueada':
            return ('Tu cuenta está bloqueada. Contacta al personal bibliotecario.' if para_el_lector
                    else f'{self.get_nombre_completo()} tiene la cuenta bloqueada.')
        if r['tipo'] == 'vencidos':
            n, s = r['n'], 's' if r['n'] > 1 else ''
            return (f'Tienes {n} préstamo{s} vencido{s}. Devuélvelo{s} para volver a solicitar libros.' if para_el_lector
                    else f'{self.get_nombre_completo()} tiene {n} préstamo{s} vencido{s} sin devolver.')
        monto = formato_pesos(r['monto'])
        return (f'Tienes {monto} en multas sin pagar. Págalas en el mostrador de la biblioteca para volver a solicitar libros.'
                if para_el_lector else f'{self.get_nombre_completo()} tiene {monto} en multas sin pagar.')

    def prestamos_activos(self):
        return self.prestamos.filter(estado__in=['activo', 'vencido']).count()

    def get_nombre_completo(self):
        return self.user.get_full_name() or self.user.username
