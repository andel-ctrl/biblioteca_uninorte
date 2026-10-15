from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.contrib.auth import logout
from apps.usuarios.decorators import es_bibliotecario_o_staff


def home_redirect(request):
    if not request.user.is_authenticated:
        return redirect('login')
    if es_bibliotecario_o_staff(request.user):
        return redirect('reportes:dashboard')
    return redirect('catalogos:inicio')


def logout_view(request):
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
    # Auth (login, password reset, etc.)
    path('', include('django.contrib.auth.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
