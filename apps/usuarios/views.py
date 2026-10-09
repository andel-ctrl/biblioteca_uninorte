from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import UsuarioBiblioteca
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
    prestamos = usuario.prestamos.select_related('ejemplar__libro').order_by('-fecha_solicitud')
    return render(request, 'usuarios/usuario_detail.html', {'usuario': usuario, 'prestamos': prestamos})


@bibliotecario_required
def usuario_edit(request, pk):
    usuario = get_object_or_404(UsuarioBiblioteca, pk=pk)
    if request.method == 'POST':
        form = UsuarioBibliotecaForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, 'Usuario actualizado.')
            return redirect('usuarios:usuario_list')
    else:
        form = UsuarioBibliotecaForm(instance=usuario)
    return render(request, 'usuarios/usuario_form.html', {'form': form, 'titulo': 'Editar Usuario'})


@bibliotecario_required
def usuario_delete(request, pk):
    usuario = get_object_or_404(UsuarioBiblioteca, pk=pk)
    if request.method == 'POST':
        nombre = usuario.get_nombre_completo()
        usuario.user.delete()
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
    prestamos = perfil.prestamos.select_related('ejemplar__libro').order_by('-fecha_solicitud')
    return render(request, 'usuarios/mi_historial.html', {'prestamos': prestamos, 'perfil': perfil})
