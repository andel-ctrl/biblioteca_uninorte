from django.db import models
from django.utils import timezone
from apps.usuarios.models import UsuarioBiblioteca
from apps.catalogos.models import Ejemplar
import datetime


class ConfiguracionMulta(models.Model):
    tarifa_por_dia = models.DecimalField(max_digits=8, decimal_places=2, verbose_name='Tarifa por día ($)')
    vigencia_desde = models.DateField(default=datetime.date.today)
    activa = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Configuración de Multa'
        verbose_name_plural = 'Configuraciones de Multa'

    def __str__(self):
        return f"${self.tarifa_por_dia}/día desde {self.vigencia_desde}"

    @classmethod
    def tarifa_vigente(cls):
        config = cls.objects.filter(activa=True).order_by('-vigencia_desde').first()
        return config.tarifa_por_dia if config else 0


class Prestamo(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente de aprobación'),
        ('activo', 'Activo'),
        ('vencido', 'Vencido'),
        ('devuelto', 'Devuelto'),
        ('rechazado', 'Rechazado'),
    ]

    usuario = models.ForeignKey(
        UsuarioBiblioteca, on_delete=models.PROTECT, related_name='prestamos'
    )
    ejemplar = models.ForeignKey(
        Ejemplar, on_delete=models.PROTECT, related_name='prestamos'
    )
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    fecha_prestamo = models.DateField(null=True, blank=True, verbose_name='Fecha de préstamo')
    fecha_vencimiento = models.DateField(null=True, blank=True, verbose_name='Fecha de vencimiento')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    aprobado_por = models.ForeignKey(
        UsuarioBiblioteca, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='prestamos_aprobados'
    )
    observaciones = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Préstamo'
        verbose_name_plural = 'Préstamos'
        ordering = ['-fecha_solicitud']

    def __str__(self):
        return f"Préstamo #{self.pk} — {self.usuario} — {self.ejemplar.libro.titulo}"

    def esta_vencido(self):
        if self.fecha_vencimiento and self.estado == 'activo':
            return timezone.now().date() > self.fecha_vencimiento
        return False

    def dias_retraso(self):
        if self.fecha_vencimiento and self.estado in ['activo', 'vencido']:
            delta = timezone.now().date() - self.fecha_vencimiento
            return max(0, delta.days)
        return 0

    def multa_estimada(self):
        tarifa = ConfiguracionMulta.tarifa_vigente()
        return self.dias_retraso() * tarifa

    def aprobar(self, bibliotecario, dias_prestamo=15):
        # Aprueba el préstamo, cambia estado del ejemplar y pone lo de las fechas
        self.estado = 'activo'
        self.aprobado_por = bibliotecario
        self.fecha_prestamo = timezone.now().date()
        self.fecha_vencimiento = self.fecha_prestamo + datetime.timedelta(days=dias_prestamo)
        self.save()
        self.ejemplar.estado = 'prestado'
        self.ejemplar.save()

    def rechazar(self, bibliotecario):
        self.estado = 'rechazado'
        self.aprobado_por = bibliotecario
        self.save()


class Devolucion(models.Model):
    OBSERVACION_CHOICES = [
        ('', 'Sin observaciones'),
        ('bueno', 'En buen estado'),
        ('danado', 'Dañado'),
        ('paginas_faltantes', 'Páginas faltantes'),
        ('otro', 'Otro'),
    ]

    prestamo = models.OneToOneField(Prestamo, on_delete=models.PROTECT, related_name='devolucion')
    fecha_devolucion = models.DateField(default=datetime.date.today)
    observacion = models.CharField(max_length=50, choices=OBSERVACION_CHOICES, blank=True)
    detalle_observacion = models.TextField(blank=True)
    monto_multa = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    multa_pagada = models.BooleanField(default=False)
    registrado_por = models.ForeignKey(
        UsuarioBiblioteca, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='devoluciones_registradas'
    )
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Devolución'
        verbose_name_plural = 'Devoluciones'

    def __str__(self):
        return f"Devolución del Préstamo #{self.prestamo.pk} — {self.fecha_devolucion}"

    def calcular_multa(self):
        # Calcula la multa automáticamente según días de retraso.
        tarifa = ConfiguracionMulta.tarifa_vigente()
        if self.prestamo.fecha_vencimiento:
            dias = (self.fecha_devolucion - self.prestamo.fecha_vencimiento).days
            self.monto_multa = max(0, dias) * tarifa
        else:
            self.monto_multa = 0
        return self.monto_multa

    def save(self, *args, **kwargs):
        if not self.pk:
            self.calcular_multa()
        super().save(*args, **kwargs)
        # Marcar préstamo como devuelto y ejemplar como disponible
        self.prestamo.estado = 'devuelto'
        self.prestamo.save()
        self.prestamo.ejemplar.estado = 'disponible'
        self.prestamo.ejemplar.save()
