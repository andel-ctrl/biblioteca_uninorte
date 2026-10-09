from django.contrib import admin
from .models import Prestamo, Devolucion, ConfiguracionMulta


@admin.register(ConfiguracionMulta)
class ConfiguracionMultaAdmin(admin.ModelAdmin):
    list_display = ('tarifa_por_dia', 'vigencia_desde', 'activa')
    list_filter = ('activa',)


@admin.register(Prestamo)
class PrestamoAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'ejemplar', 'estado', 'fecha_prestamo', 'fecha_vencimiento')
    list_filter = ('estado',)
    search_fields = ('usuario__user__first_name', 'ejemplar__libro__titulo')
    readonly_fields = ('fecha_solicitud',)


@admin.register(Devolucion)
class DevolucionAdmin(admin.ModelAdmin):
    list_display = ('prestamo', 'fecha_devolucion', 'monto_multa', 'multa_pagada', 'observacion')
    list_filter = ('multa_pagada', 'observacion')
