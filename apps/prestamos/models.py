from django.db import models, transaction
from django.utils import timezone
from apps.usuarios.models import Lector, Bibliotecario
from apps.catalogos.models import Ejemplar
import datetime
from apps.catalogos.formato import formato_pesos


class TarifaMulta(models.Model):
    """Valor de la multa por día de retraso. Se guarda el historial: rige la activa más reciente,
    y cada multa queda enlazada a la tarifa con la que se calculó."""
    valor_dia = models.DecimalField(max_digits=8, decimal_places=2, verbose_name='Valor por día ($)')
    vigente_desde = models.DateField(default=datetime.date.today)
    activa = models.BooleanField(default=True)

    class Meta:
        db_table = 'tarifa_multa'
        verbose_name = 'Tarifa de multa'
        verbose_name_plural = 'Tarifas de multa'
        constraints = [
            models.CheckConstraint(condition=models.Q(valor_dia__gt=0), name='tarifa_multa_positiva',
                violation_error_message='La tarifa debe ser mayor que cero.'),
        ]

    def __str__(self):
        return f"{formato_pesos(self.valor_dia)}/día desde {self.vigente_desde}"

    @classmethod
    def vigente(cls):
        return cls.objects.filter(activa=True).order_by('-vigente_desde', '-pk').first()

    @classmethod
    def valor_vigente(cls):
        tarifa = cls.vigente()
        return tarifa.valor_dia if tarifa else 0


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

    # Solo un lector solicita; solo un bibliotecario aprueba (las llaves foráneas lo garantizan)
    lector = models.ForeignKey(
        Lector, on_delete=models.PROTECT, related_name='prestamos'
    )
    ejemplar = models.ForeignKey(
        Ejemplar, on_delete=models.PROTECT, related_name='prestamos'
    )
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    fecha_prestamo = models.DateField(null=True, blank=True, verbose_name='Fecha de préstamo')
    fecha_vencimiento = models.DateField(null=True, blank=True, verbose_name='Fecha de vencimiento')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    aprobado_por = models.ForeignKey(
        Bibliotecario, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='prestamos_aprobados'
    )
    observaciones = models.TextField(blank=True)

    class Meta:
        db_table = 'prestamo'
        verbose_name = 'Préstamo'
        verbose_name_plural = 'Préstamos'
        ordering = ['-fecha_solicitud']
        constraints = [
            models.CheckConstraint(
                condition=models.Q(estado__in=['pendiente', 'activo', 'vencido', 'devuelto', 'rechazado', 'perdido']),
                name='prestamo_estado_valido',
                violation_error_message='El estado del préstamo no es válido.'),
            # El vencimiento nunca es anterior al día del préstamo
            models.CheckConstraint(
                condition=models.Q(fecha_prestamo__isnull=True) | models.Q(fecha_vencimiento__isnull=True)
                | models.Q(fecha_vencimiento__gte=models.F('fecha_prestamo')),
                name='prestamo_vencimiento_posterior',
                violation_error_message='La fecha de vencimiento no puede ser anterior a la fecha del préstamo.'),
            # Un préstamo aprobado (no pendiente ni rechazado) tiene sus dos fechas
            models.CheckConstraint(
                condition=models.Q(estado__in=['pendiente', 'rechazado'])
                | models.Q(fecha_prestamo__isnull=False, fecha_vencimiento__isnull=False),
                name='prestamo_aprobado_con_fechas',
                violation_error_message='Un préstamo aprobado necesita fecha de préstamo y de vencimiento.'),
        ]

    def __str__(self):
        return f"Préstamo #{self.pk} — {self.lector} — {self.ejemplar.libro.titulo}"

    @property
    def usuario(self):
        """Datos comunes (nombre, código, estado) del lector que pidió el préstamo."""
        return self.lector.usuario

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
        return self.dias_retraso() * TarifaMulta.valor_vigente()

    def aprobar(self, bibliotecario, fecha_vencimiento=None):
        # Aprueba el préstamo, cambia estado del ejemplar y pone lo de las fechas.
        # atomic: o se guardan préstamo y ejemplar juntos, o ninguno
        # Devuelve cuántas otras solicitudes del mismo ejemplar se rechazaron automáticamente.
        with transaction.atomic():
            # Bloquea la fila del ejemplar: dos aprobaciones simultáneas no pueden prestarlo dos veces
            ejemplar = Ejemplar.objects.select_for_update().get(pk=self.ejemplar_id)
            if not ejemplar.esta_disponible():
                raise ValueError('El ejemplar ya no está disponible.')
            self.estado = 'activo'
            self.aprobado_por = bibliotecario
            self.fecha_prestamo = timezone.localdate()
            self.fecha_vencimiento = fecha_vencimiento or (
                self.fecha_prestamo + datetime.timedelta(days=self.DIAS_PRESTAMO_DEFECTO)
            )
            self.save()
            ejemplar.estado = 'prestado'
            ejemplar.save()
            self.ejemplar = ejemplar
            # Las demás solicitudes de ese ejemplar ya no pueden atenderse: se cierran en vez de quedar pendientes
            return Prestamo.objects.filter(ejemplar=ejemplar, estado='pendiente').exclude(pk=self.pk).update(
                estado='rechazado', aprobado_por=bibliotecario,
                observaciones='Rechazada automáticamente: el ejemplar se prestó a otra solicitud.',
            )

    def puede_ampliarse(self):
        # Solo un préstamo activo y que aún no llegó al máximo de días desde que se prestó.
        # Uno vencido no se amplía: borraría la mora ya acumulada.
        return (self.estado == 'activo' and self.fecha_prestamo and self.fecha_vencimiento
                and self.fecha_vencimiento < self.fecha_limite_ampliacion())

    def fecha_limite_ampliacion(self):
        return self.fecha_prestamo + datetime.timedelta(days=self.DIAS_PRESTAMO_MAXIMO)

    def ampliar_plazo(self, nueva_fecha, bibliotecario):
        # Mueve la fecha de vencimiento y deja constancia en las observaciones del préstamo
        anterior = self.fecha_vencimiento
        self.fecha_vencimiento = nueva_fecha
        quien = bibliotecario.get_nombre_completo() if bibliotecario else 'el personal'
        nota = f'Plazo ampliado del {anterior:%d/%m/%Y} al {nueva_fecha:%d/%m/%Y} por {quien} el {timezone.localdate():%d/%m/%Y}.'
        self.observaciones = f'{self.observaciones}\n{nota}'.strip()
        self.save(update_fields=['fecha_vencimiento', 'observaciones'])

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
    registrado_por = models.ForeignKey(
        Bibliotecario, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='devoluciones_registradas'
    )
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'devolucion'
        verbose_name = 'Devolución'
        verbose_name_plural = 'Devoluciones'

    def __str__(self):
        return f"Devolución del Préstamo #{self.prestamo.pk} — {self.fecha_devolucion}"

    def dias_retraso(self):
        if self.prestamo.fecha_vencimiento:
            return max(0, (self.fecha_devolucion - self.prestamo.fecha_vencimiento).days)
        return 0

    def es_perdida(self):
        return self.observacion == 'perdido'

    def estado_ejemplar_resultante(self):
        if self.es_perdida():
            return 'perdido'
        return 'mantenimiento' if self.observacion in self.OBSERVACIONES_MANTENIMIENTO else 'disponible'

    # La multa vive en su propia tabla; estos atajos permiten leerla desde la devolución
    @property
    def multa_registrada(self):
        return getattr(self, 'multa', None)

    @property
    def monto_multa(self):
        multa = self.multa_registrada
        return multa.monto if multa else 0

    @property
    def multa_pagada(self):
        multa = self.multa_registrada
        return multa.pagada if multa else False

    def save(self, *args, multa_pagada=False, **kwargs):
        """Al registrar la devolución: cierra el préstamo, actualiza el ejemplar y, si hubo
        retraso, crea la multa con la tarifa vigente (días de retraso × valor por día)."""
        es_nueva = self.pk is None
        with transaction.atomic():
            super().save(*args, **kwargs)
            if es_nueva:
                self.prestamo.estado = 'perdido' if self.es_perdida() else 'devuelto'
                self.prestamo.save()
                self.prestamo.ejemplar.estado = self.estado_ejemplar_resultante()
                self.prestamo.ejemplar.save()
                dias = self.dias_retraso()
                tarifa = TarifaMulta.vigente()
                if dias > 0 and tarifa:
                    Multa.objects.create(
                        devolucion=self, tarifa=tarifa, monto=dias * tarifa.valor_dia,
                        pagada=multa_pagada,
                        fecha_pago=self.fecha_devolucion if multa_pagada else None,
                        cobrada_por=self.registrado_por if multa_pagada else None,
                    )


class Multa(models.Model):
    """Sanción por entregar tarde: existe solo si hubo retraso (0 o 1 por devolución).
    Guarda la tarifa con la que se calculó y el monto de ese momento; los días de retraso
    no se guardan porque se calculan con las fechas del préstamo y de la devolución."""
    devolucion = models.OneToOneField(Devolucion, on_delete=models.PROTECT, related_name='multa')
    tarifa = models.ForeignKey(TarifaMulta, on_delete=models.PROTECT, related_name='multas')
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    pagada = models.BooleanField(default=False)
    fecha_pago = models.DateField(null=True, blank=True)
    cobrada_por = models.ForeignKey(
        Bibliotecario, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='multas_cobradas'
    )

    class Meta:
        db_table = 'multa'
        verbose_name = 'Multa'
        verbose_name_plural = 'Multas'
        constraints = [
            models.CheckConstraint(condition=models.Q(monto__gt=0), name='multa_monto_positivo',
                violation_error_message='El monto de la multa debe ser mayor que cero.'),
            # Pagada si y solo si tiene fecha de pago
            models.CheckConstraint(
                condition=models.Q(pagada=True, fecha_pago__isnull=False) | models.Q(pagada=False, fecha_pago__isnull=True),
                name='multa_pago_coherente',
                violation_error_message='Una multa pagada necesita fecha de pago, y una pendiente no la tiene.'),
        ]

    def __str__(self):
        return f"Multa de {formato_pesos(self.monto)} — préstamo #{self.devolucion.prestamo_id}"

    def dias_retraso(self):
        return self.devolucion.dias_retraso()

    def registrar_pago(self, bibliotecario, fecha=None):
        from django.utils import timezone
        self.pagada = True
        self.fecha_pago = fecha or timezone.localdate()
        self.cobrada_por = bibliotecario
        self.save(update_fields=['pagada', 'fecha_pago', 'cobrada_por'])
