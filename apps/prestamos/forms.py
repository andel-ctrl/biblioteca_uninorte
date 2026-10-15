import datetime
from django import forms
from django.utils import timezone
from .models import Prestamo, Devolucion, ConfiguracionMulta


class TarifaMultaForm(forms.ModelForm):
    class Meta:
        model = ConfiguracionMulta
        fields = ['tarifa_por_dia']
        widgets = {
            'tarifa_por_dia': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'step': '50'}),
        }

    def clean_tarifa_por_dia(self):
        tarifa = self.cleaned_data['tarifa_por_dia']
        if tarifa <= 0:
            raise forms.ValidationError('La tarifa debe ser mayor que cero.')
        return tarifa


class AprobarPrestamoForm(forms.Form):
    fecha_vencimiento = forms.DateField(
        label='Fecha de vencimiento',
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        hoy = timezone.localdate()
        self.minimo = hoy + datetime.timedelta(days=1)
        self.maximo = hoy + datetime.timedelta(days=Prestamo.DIAS_PRESTAMO_MAXIMO)
        campo = self.fields['fecha_vencimiento']
        campo.initial = hoy + datetime.timedelta(days=Prestamo.DIAS_PRESTAMO_DEFECTO)
        campo.widget.attrs.update({'min': self.minimo.isoformat(), 'max': self.maximo.isoformat()})
        campo.help_text = f'Por defecto {Prestamo.DIAS_PRESTAMO_DEFECTO} días. Máximo {Prestamo.DIAS_PRESTAMO_MAXIMO} días.'

    def clean_fecha_vencimiento(self):
        # Se valida también en el servidor: los atributos min/max del navegador se pueden saltar
        fecha = self.cleaned_data['fecha_vencimiento']
        if fecha < self.minimo:
            raise forms.ValidationError('La fecha de vencimiento debe ser posterior a hoy.')
        if fecha > self.maximo:
            raise forms.ValidationError(f'El préstamo no puede superar {Prestamo.DIAS_PRESTAMO_MAXIMO} días.')
        return fecha


class AmpliarPlazoForm(forms.Form):
    fecha_vencimiento = forms.DateField(
        label='Nueva fecha de vencimiento',
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
    )

    def __init__(self, *args, prestamo, **kwargs):
        super().__init__(*args, **kwargs)
        self.minimo = max(prestamo.fecha_vencimiento, timezone.localdate()) + datetime.timedelta(days=1)
        self.maximo = prestamo.fecha_limite_ampliacion()
        campo = self.fields['fecha_vencimiento']
        campo.initial = min(prestamo.fecha_vencimiento + datetime.timedelta(days=Prestamo.DIAS_PRESTAMO_DEFECTO), self.maximo)
        campo.widget.attrs.update({'min': self.minimo.isoformat(), 'max': self.maximo.isoformat()})
        campo.help_text = f'Entre el {self.minimo:%d/%m/%Y} y el {self.maximo:%d/%m/%Y} ({Prestamo.DIAS_PRESTAMO_MAXIMO} días desde el préstamo).'

    def clean_fecha_vencimiento(self):
        # También en el servidor: el calendario del navegador se puede saltar
        fecha = self.cleaned_data['fecha_vencimiento']
        if fecha < self.minimo:
            raise forms.ValidationError(f'La nueva fecha debe ser posterior al vencimiento actual (desde el {self.minimo:%d/%m/%Y}).')
        if fecha > self.maximo:
            raise forms.ValidationError(f'El préstamo no puede pasar de {Prestamo.DIAS_PRESTAMO_MAXIMO} días: como máximo hasta el {self.maximo:%d/%m/%Y}.')
        return fecha


class DevolucionForm(forms.ModelForm):
    class Meta:
        model = Devolucion
        fields = ['fecha_devolucion', 'observacion', 'detalle_observacion', 'multa_pagada']
        labels = {
            'fecha_devolucion': 'Fecha de devolución',
            'observacion': 'Observación del ejemplar',
            'detalle_observacion': 'Detalle de la observación',
            'multa_pagada': 'La multa se pagó en este momento',
        }
        widgets = {
            # format ISO: el selector de fecha del navegador solo entiende AAAA-MM-DD
            'fecha_devolucion': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
            'observacion': forms.Select(attrs={'class': 'form-select'}),
            'detalle_observacion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2,
                                                         'placeholder': 'Detalles adicionales...'}),
            'multa_pagada': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, prestamo=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.prestamo = prestamo
        # La pérdida se registra con su propio botón ("Reportar pérdida"), no como devolución
        campo = self.fields['observacion']
        campo.choices = [c for c in campo.choices if c[0] != 'perdido']
        # La fecha va entre el día del préstamo y hoy (el calendario del navegador también lo limita)
        fecha = self.fields['fecha_devolucion']
        fecha.widget.attrs['max'] = timezone.localdate().isoformat()
        if prestamo and prestamo.fecha_prestamo:
            fecha.widget.attrs['min'] = prestamo.fecha_prestamo.isoformat()

    def clean_fecha_devolucion(self):
        # Una devolución futura cobraría multa por días que no han pasado; una anterior al préstamo es imposible
        fecha = self.cleaned_data['fecha_devolucion']
        if fecha > timezone.localdate():
            raise forms.ValidationError('La fecha de devolución no puede ser posterior a hoy.')
        if self.prestamo and self.prestamo.fecha_prestamo and fecha < self.prestamo.fecha_prestamo:
            raise forms.ValidationError(f'La fecha de devolución no puede ser anterior al préstamo ({self.prestamo.fecha_prestamo:%d/%m/%Y}).')
        return fecha
