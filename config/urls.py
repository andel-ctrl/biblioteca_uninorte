from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.contrib.auth import logout
from django.contrib.auth import views as auth_views
from apps.usuarios.decorators import es_bibliotecario_o_staff


def home_redirect(request):
    if not request.user.is_authenticated:
        return redirect('login')
    if es_bibliotecario_o_staff(request.user):
        return redirect('reportes:dashboard')
    return redirect('catalogos:inicio')


def logout_view(request):
    # Solo por POST (con CSRF): un enlace o imagen de otra página no puede cerrar la sesión.
    # Si alguien abre /logout/ escribiéndolo, vuelve a su inicio sin cerrar sesión.
    if request.method != 'POST':
        return redirect('home')
    logout(request)
    return redirect('login')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_redirect, name='home'),
    path('logout/', logout_view, name='logout'),
    path('catalogos/', include('apps.catalogos.urls', namespace='catalogos')),
    path('usuarios/', include('apps.usuarios.urls', namespace='usuarios')),
    path('prestamos/', include('apps.prestamos.urls', namespace='prestamos')),
    path('reportes/', include('apps.reportes.urls', namespace='reportes')),
    # Login: si ya hay sesión (p. ej. al volver con "atrás") redirige al inicio de su rol en vez de mostrar el formulario
    path('login/', auth_views.LoginView.as_view(redirect_authenticated_user=True), name='login'),
    # Sin las rutas de contraseña de Django (password_reset, password_change): no hay correo configurado
    # y las contraseñas se restablecen en el mostrador, desde "Editar usuario".
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    # Vista previa de la página 404 en desarrollo (con DEBUG=True Django muestra su página de diagnóstico)
    from django.views.defaults import page_not_found
    urlpatterns += [path('404/', lambda request: page_not_found(request, Exception('Vista previa')), name='vista_previa_404')]
