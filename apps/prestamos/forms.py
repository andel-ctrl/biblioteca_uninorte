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


class DevolucionForm(forms.ModelForm):
    class Meta:
        model = Devolucion
        fields = ['fecha_devolucion', 'observacion', 'detalle_observacion', 'multa_pagada']
        widgets = {
            'fecha_devolucion': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'observacion': forms.Select(attrs={'class': 'form-select'}),
            'detalle_observacion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2,
                                                         'placeholder': 'Detalles adicionales...'}),
            'multa_pagada': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # La pérdida se registra con su propio botón ("Reportar pérdida"), no como devolución
        campo = self.fields['observacion']
        campo.choices = [c for c in campo.choices if c[0] != 'perdido']
