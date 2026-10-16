from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def es_bibliotecario(user):
    """Puede usar las pantallas del personal solo quien está en la tabla bibliotecario: la misma
    a la que apuntan las llaves foráneas de aprobar, registrar y cobrar. La marca is_staff de
    Django no cuenta (solo da acceso al panel /admin/)."""
    if not user.is_authenticated:
        return False
    perfil = getattr(user, 'perfil', None)
    return perfil is not None and getattr(perfil, 'bibliotecario', None) is not None


def bibliotecario_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not es_bibliotecario(request.user):
            messages.error(request, 'Acceso restringido: no tienes permisos de bibliotecario para acceder a esta sección.')
            return redirect('catalogos:libro_list')
        return view_func(request, *args, **kwargs)
    return _wrapped_view
