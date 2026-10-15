"""Personaje ilustrado (libro) de la ficha de cuenta del lector.

Se elige al azar en cada inicio de sesión y se guarda en la sesión: no se almacena nada en la BD.
Los docentes reciben uno de los libros con birrete; los estudiantes, uno de los demás.
Archivos en static/img/personajes/ (ver static/img/CREDITOS.txt).
"""
import random

PERSONAJES = {
    'docente': [f'img/personajes/docente-{i:02d}.webp' for i in range(1, 5)],
    'estudiante': [f'img/personajes/estudiante-{i:02d}.webp' for i in range(1, 15)],
}
CLAVE_SESION = 'personaje'


def elegir(user):
    perfil = getattr(user, 'perfil', None)
    grupo = 'docente' if perfil and perfil.rol == 'docente' else 'estudiante'
    return random.choice(PERSONAJES[grupo])


def del_usuario(request):
    """El personaje de esta sesión; si la sesión es anterior a esta función, se asigna uno ahora."""
    if CLAVE_SESION not in request.session:
        request.session[CLAVE_SESION] = elegir(request.user)
    return request.session[CLAVE_SESION]
