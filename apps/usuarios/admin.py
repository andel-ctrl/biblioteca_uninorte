from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import UsuarioBiblioteca


class PerfilInline(admin.StackedInline):
    model = UsuarioBiblioteca
    can_delete = False
    verbose_name_plural = 'Perfil Biblioteca'


class UserAdmin(BaseUserAdmin):
    inlines = (PerfilInline,)


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(UsuarioBiblioteca)
class UsuarioBibliotecaAdmin(admin.ModelAdmin):
    list_display = ('get_nombre_completo', 'codigo_universitario', 'identificacion', 'rol', 'estado')
    list_filter = ('rol', 'estado')
    search_fields = ('user__first_name', 'user__last_name', 'codigo_universitario', 'identificacion')
