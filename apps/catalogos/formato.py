"""Formatos de presentación compartidos por vistas, modelos y plantillas."""
from decimal import Decimal, InvalidOperation


def formato_pesos(valor):
    """$1.500 o $1.500,50: separador de miles con punto y centavos solo si existen (formato colombiano)."""
    try:
        numero = Decimal(str(valor or 0)).quantize(Decimal('0.01'))
    except (InvalidOperation, ValueError):
        return f'${valor}'
    entero, centavos = divmod(abs(numero), 1)
    texto = f'{int(entero):,}'.replace(',', '.')
    if centavos:
        texto += ',' + f'{centavos:.2f}'[2:]
    return ('-$' if numero < 0 else '$') + texto
