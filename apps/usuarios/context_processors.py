from .decorators import es_bibliotecario_o_staff


def navegacion(request):
    """Datos que necesita la navegación en todas las plantillas."""
    user = getattr(request, 'user', None)
    if user is None or not user.is_authenticated:
        return {'es_bibliotecario': False}

    es_bib = es_bibliotecario_o_staff(user)
    datos = {'es_bibliotecario': es_bib}
    if es_bib:
        # Import local: evita dependencia circular entre apps al cargar la configuración
        from apps.prestamos.models import Prestamo
        datos['nav_pendientes'] = Prestamo.objects.filter(estado='pendiente').count()
    return datos
