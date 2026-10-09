from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def es_bibliotecario_o_staff(user):
    if not user.is_authenticated:
        return False
    if user.is_staff:
        return True
    return hasattr(user, 'perfil') and user.perfil.es_bibliotecario()


def bibliotecario_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not es_bibliotecario_o_staff(request.user):
            messages.error(request, 'Acceso restringido: no tienes permisos de bibliotecario para acceder a esta sección.')
            return redirect('catalogos:libro_list')
        return view_func(request, *args, **kwargs)
    return _wrapped_view
