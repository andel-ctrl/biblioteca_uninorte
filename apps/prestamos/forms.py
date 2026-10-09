from django import forms
from .models import Devolucion


class PrestamoForm(forms.Form):
    pass


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
