from django.contrib import admin
from .models import Prestamo, Devolucion, Multa, TarifaMulta


@admin.register(TarifaMulta)
class TarifaMultaAdmin(admin.ModelAdmin):
    list_display = ('valor_dia', 'vigente_desde', 'activa')
    list_filter = ('activa',)


@admin.register(Prestamo)
class PrestamoAdmin(admin.ModelAdmin):
    list_display = ('id', 'lector', 'ejemplar', 'estado', 'fecha_prestamo', 'fecha_vencimiento')
    list_filter = ('estado',)
    search_fields = ('lector__usuario__user__first_name', 'ejemplar__libro__titulo')
    readonly_fields = ('fecha_solicitud',)


@admin.register(Devolucion)
class DevolucionAdmin(admin.ModelAdmin):
    list_display = ('prestamo', 'fecha_devolucion', 'observacion', 'registrado_por')
    list_filter = ('observacion',)


@admin.register(Multa)
class MultaAdmin(admin.ModelAdmin):
    list_display = ('devolucion', 'monto', 'tarifa', 'pagada', 'fecha_pago', 'cobrada_por')
    list_filter = ('pagada',)
