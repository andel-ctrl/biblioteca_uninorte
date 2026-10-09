from django import forms
from django.contrib.auth.models import User
from .models import UsuarioBiblioteca


class UsuarioBibliotecaForm(forms.ModelForm):
    class Meta:
        model = UsuarioBiblioteca
        fields = ['codigo_universitario', 'identificacion', 'rol', 'carrera', 'estado', 'telefono']
        widgets = {
            'codigo_universitario': forms.TextInput(attrs={'class': 'form-control'}),
            'identificacion': forms.TextInput(attrs={'class': 'form-control'}),
            'rol': forms.Select(attrs={'class': 'form-select'}),
            'carrera': forms.TextInput(attrs={'class': 'form-control'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
        }


class RegistroForm(forms.Form):
    """Formulario que crea User + UsuarioBiblioteca al mismo tiempo."""
    first_name = forms.CharField(max_length=150, label='Nombres', widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=150, label='Apellidos', widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(label='Correo electrónico', widget=forms.EmailInput(attrs={'class': 'form-control'}))
    username = forms.CharField(max_length=150, label='Usuario', widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), label='Contraseña')
    codigo_universitario = forms.CharField(max_length=20, label='Código universitario', widget=forms.TextInput(attrs={'class': 'form-control'}))
    identificacion = forms.CharField(max_length=20, label='Identificación', widget=forms.TextInput(attrs={'class': 'form-control'}))
    rol = forms.ChoiceField(choices=UsuarioBiblioteca.ROL_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    carrera = forms.CharField(max_length=150, required=False, label='Carrera', widget=forms.TextInput(attrs={'class': 'form-control'}))
    telefono = forms.CharField(max_length=20, required=False, label='Teléfono', widget=forms.TextInput(attrs={'class': 'form-control'}))

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Ya existe un usuario con ese correo.')
        return email

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('Ese nombre de usuario ya está en uso.')
        return username

    def save(self):
        data = self.cleaned_data
        user = User.objects.create_user(
            username=data['username'],
            email=data['email'],
            password=data['password'],
            first_name=data['first_name'],
            last_name=data['last_name'],
        )
        perfil = UsuarioBiblioteca.objects.create(
            user=user,
            codigo_universitario=data['codigo_universitario'],
            identificacion=data['identificacion'],
            rol=data['rol'],
            carrera=data.get('carrera', ''),
            telefono=data.get('telefono', ''),
        )
        return perfil
