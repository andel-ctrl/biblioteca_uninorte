from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.db.models import ProtectedError
from .models import UsuarioBiblioteca
from apps.prestamos.models import Prestamo
from .forms import UsuarioBibliotecaForm, RegistroForm
from .decorators import bibliotecario_required


@bibliotecario_required
def usuario_list(request):
    # Lista de usuarios de la biblioteca (solo bibliotecario)
    usuarios = UsuarioBiblioteca.objects.select_related('user').all()
    return render(request, 'usuarios/usuario_list.html', {'usuarios': usuarios})


@bibliotecario_required
def usuario_create(request):
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            messages.success(request, f'Usuario {usuario.user.get_full_name()} creado correctamente.')
            return redirect('usuarios:usuario_list')
    else:
        form = RegistroForm()
    return render(request, 'usuarios/usuario_form.html', {'form': form, 'titulo': 'Nuevo Usuario'})


@bibliotecario_required
def usuario_detail(request, pk):
    usuario = get_object_or_404(UsuarioBiblioteca, pk=pk)
    Prestamo.actualizar_vencidos()
    prestamos = usuario.prestamos.select_related('ejemplar__libro').order_by('-fecha_solicitud')
    return render(request, 'usuarios/usuario_detail.html', {'usuario': usuario, 'prestamos': prestamos})


@bibliotecario_required
def usuario_edit(request, pk):
    usuario = get_object_or_404(UsuarioBiblioteca, pk=pk)
    if request.method == 'POST':
        form = UsuarioBibliotecaForm(request.POST, instance=usuario, editor=request.user)
        if form.is_valid():
            form.save()
            if form.es_su_propia_cuenta() and form.cleaned_data.get('nueva_password'):
                # Al cambiar la propia contraseña Django cierra la sesión; esto la mantiene abierta
                update_session_auth_hash(request, usuario.user)
            messages.success(request, 'Usuario actualizado.')
            return redirect('usuarios:usuario_detail', pk=pk)
    else:
        form = UsuarioBibliotecaForm(instance=usuario, editor=request.user)
    return render(request, 'usuarios/usuario_form.html', {
        'form': form, 'titulo': f'Editar Usuario: {usuario.get_nombre_completo()}', 'usuario': usuario,
    })


@bibliotecario_required
def usuario_delete(request, pk):
    usuario = get_object_or_404(UsuarioBiblioteca, pk=pk)
    if usuario.user_id == request.user.pk:
        messages.error(request, 'No puede eliminar su propia cuenta.')
        return redirect('usuarios:usuario_detail', pk=pk)
    if request.method == 'POST':
        nombre = usuario.get_nombre_completo()
        try:
            usuario.user.delete()
        except ProtectedError:
            # PROTECT en Prestamo.usuario impide borrar usuarios con historial de préstamos
            messages.error(request, f'No se puede eliminar a "{nombre}" porque tiene préstamos registrados. Puede cambiar su estado a bloqueado.')
            return redirect('usuarios:usuario_detail', pk=pk)
        messages.success(request, f'Usuario "{nombre}" eliminado.')
        return redirect('usuarios:usuario_list')
    return render(request, 'usuarios/usuario_confirm_delete.html', {'usuario': usuario})


@login_required
def mi_historial(request):
    try:
        perfil = request.user.perfil
    except UsuarioBiblioteca.DoesNotExist:
        messages.error(request, 'No tienes perfil de biblioteca asociado.')
        return redirect('catalogos:libro_list')
    Prestamo.actualizar_vencidos()
    prestamos = perfil.prestamos.select_related('ejemplar__libro').order_by('-fecha_solicitud')
    return render(request, 'usuarios/mi_historial.html', {'prestamos': prestamos, 'perfil': perfil})
