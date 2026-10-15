from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver

from .personajes import CLAVE_SESION, elegir


@receiver(user_logged_in)
def asignar_personaje(sender, request, user, **kwargs):
    # Cada inicio de sesión trae un personaje nuevo al azar
    request.session[CLAVE_SESION] = elegir(user)
