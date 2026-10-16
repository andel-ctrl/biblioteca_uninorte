from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Usuario, Lector, Bibliotecario


class PerfilInline(admin.StackedInline):
    model = Usuario
    can_delete = False
    verbose_name_plural = 'Perfil de biblioteca'


class UserAdmin(BaseUserAdmin):
    inlines = (PerfilInline,)


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


class LectorInline(admin.StackedInline):
    model = Lector
    can_delete = False


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ('get_nombre_completo', 'codigo_universitario', 'identificacion', 'tipo', 'estado')
    list_filter = ('tipo', 'estado')
    search_fields = ('user__first_name', 'user__last_name', 'codigo_universitario', 'identificacion')


@admin.register(Lector)
class LectorAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'rol', 'carrera')
    list_filter = ('rol',)


@admin.register(Bibliotecario)
class BibliotecarioAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'turno')
    list_filter = ('turno',)
