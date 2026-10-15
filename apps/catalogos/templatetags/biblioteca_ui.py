"""
Componentes visuales compartidos por todas las plantillas.

Uso:
    {% load biblioteca_ui %}
    {% estado prestamo.estado 'prestamo' %}
    {% estado ejemplar.estado 'ejemplar' %}
    {% estado usuario.estado 'usuario' %}
    {% estado 'pendiente' 'multa' %}
"""
from django import template
from django.utils.html import format_html

from apps.catalogos.formato import formato_pesos

register = template.Library()

# (texto, ícono de Bootstrap Icons, tono). El tono define el color en componentes.css (.estado--<tono>).
# Cada estado lleva texto e ícono: no depende solo del color.
ESTADOS = {
    # Disponibilidad de un título (se calcula a partir de sus ejemplares; no es un estado guardado)
    'libro': {
        'disponible': ('Disponible', 'bi-check2-circle', 'verde'),
        'agotado': ('No disponible', 'bi-slash-circle', 'piedra'),
    },
    'ejemplar': {
        'disponible': ('Disponible', 'bi-check2-circle', 'verde'),
        'prestado': ('Prestado', 'bi-arrow-up-right-circle', 'tinta'),
        'perdido': ('Perdido', 'bi-question-octagon', 'grafito'),
        'mantenimiento': ('En mantenimiento', 'bi-tools', 'lila'),
    },
    'prestamo': {
        'pendiente': ('Pendiente', 'bi-hourglass-split', 'dorado'),
        'activo': ('Activo', 'bi-bookmark-check', 'tinta'),
        'vencido': ('Vencido', 'bi-exclamation-triangle', 'alerta'),
        'devuelto': ('Devuelto', 'bi-check2-all', 'verde'),
        'rechazado': ('Rechazado', 'bi-x-circle', 'piedra'),
        'perdido': ('Perdido', 'bi-question-octagon', 'grafito'),
    },
    'usuario': {
        'activo': ('Activo', 'bi-person-check', 'verde'),
        'bloqueado': ('Bloqueado', 'bi-person-lock', 'alerta'),
    },
    'multa': {
        'pagada': ('Multa pagada', 'bi-check2-circle', 'verde'),
        'pendiente': ('Multa pendiente', 'bi-cash-coin', 'alerta'),
        'mora': ('Mora acumulada', 'bi-clock-history', 'dorado'),
    },
}


@register.simple_tag
def estado(valor, tipo='prestamo', texto=None):
    texto_def, icono, tono = ESTADOS.get(tipo, {}).get(valor, (str(valor).capitalize(), 'bi-dot', 'piedra'))
    return format_html(
        '<span class="estado estado--{}"><i class="bi {}" aria-hidden="true"></i>{}</span>',
        tono, icono, texto or texto_def,
    )


@register.filter
def pesos(valor):
    """{{ monto|pesos }} → $1.500"""
    return formato_pesos(valor)


@register.filter
def faltan(fecha):
    """Tiempo hasta una fecha en días naturales: «hoy», «mañana», «en 12 días» o «hace 3 días»."""
    from django.utils import timezone
    if not fecha:
        return ''
    dias = (fecha - timezone.localdate()).days
    if dias == 0:
        return 'hoy'
    if dias == 1:
        return 'mañana'
    if dias > 1:
        return f'en {dias} días'
    return f'hace {-dias} día{"s" if dias < -1 else ""}'
