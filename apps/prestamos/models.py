from django.db import models, transaction
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
    DIAS_PRESTAMO_DEFECTO = 15
    DIAS_PRESTAMO_MAXIMO = 60

    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente de aprobación'),
        ('activo', 'Activo'),
        ('vencido', 'Vencido'),
        ('devuelto', 'Devuelto'),
        ('rechazado', 'Rechazado'),
        ('perdido', 'Perdido'),
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

    @classmethod
    def actualizar_vencidos(cls):
        # Un solo UPDATE: pasa a 'vencido' todo préstamo activo cuya fecha de vencimiento ya pasó
        hoy = timezone.localdate()
        return cls.objects.filter(estado='activo', fecha_vencimiento__lt=hoy).update(estado='vencido')

    def esta_vencido(self):
        if self.fecha_vencimiento and self.estado in ['activo', 'vencido']:
            return timezone.localdate() > self.fecha_vencimiento
        return False

    def dias_retraso(self):
        if self.fecha_vencimiento and self.estado in ['activo', 'vencido']:
            delta = timezone.localdate() - self.fecha_vencimiento
            return max(0, delta.days)
        return 0

    def multa_estimada(self):
        tarifa = ConfiguracionMulta.tarifa_vigente()
        return self.dias_retraso() * tarifa

    def aprobar(self, bibliotecario, fecha_vencimiento=None):
        # Aprueba el préstamo, cambia estado del ejemplar y pone lo de las fechas.
        # atomic: o se guardan préstamo y ejemplar juntos, o ninguno
        with transaction.atomic():
            self.estado = 'activo'
            self.aprobado_por = bibliotecario
            self.fecha_prestamo = timezone.localdate()
            self.fecha_vencimiento = fecha_vencimiento or (
                self.fecha_prestamo + datetime.timedelta(days=self.DIAS_PRESTAMO_DEFECTO)
            )
            self.save()
            self.ejemplar.estado = 'prestado'
            self.ejemplar.save()

    def reportar_perdida(self, bibliotecario):
        # Se registra como una devolución con observación 'perdido': así queda la fecha,
        # quién lo registró y la multa por la mora acumulada hasta hoy (ver Devolucion.save)
        return Devolucion.objects.create(
            prestamo=self,
            fecha_devolucion=timezone.localdate(),
            observacion='perdido',
            registrado_por=bibliotecario,
        )

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
        ('perdido', 'Ejemplar perdido'),
    ]
    # Con estas observaciones el ejemplar no vuelve a circular hasta ser revisado
    OBSERVACIONES_MANTENIMIENTO = ('danado', 'paginas_faltantes')

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

    def es_perdida(self):
        return self.observacion == 'perdido'

    def estado_ejemplar_resultante(self):
        if self.es_perdida():
            return 'perdido'
        return 'mantenimiento' if self.observacion in self.OBSERVACIONES_MANTENIMIENTO else 'disponible'

    def save(self, *args, **kwargs):
        es_nueva = self.pk is None
        with transaction.atomic():
            if es_nueva:
                self.calcular_multa()
            super().save(*args, **kwargs)
            # Solo al registrar la devolución: cerrar préstamo y liberar (o enviar a mantenimiento) el ejemplar
            if es_nueva:
                self.prestamo.estado = 'perdido' if self.es_perdida() else 'devuelto'
                self.prestamo.save()
                self.prestamo.ejemplar.estado = self.estado_ejemplar_resultante()
                self.prestamo.ejemplar.save()
