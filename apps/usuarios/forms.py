from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from .models import UsuarioBiblioteca


class UsuarioBibliotecaForm(forms.ModelForm):
    """Edita User (nombres, correo, contraseña) + UsuarioBiblioteca en un solo formulario."""
    first_name = forms.CharField(max_length=150, label='Nombres', widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=150, label='Apellidos', widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(label='Correo electrónico', widget=forms.EmailInput(attrs={'class': 'form-control'}))
    nueva_password = forms.CharField(
        required=False, label='Nueva contraseña',
        help_text='Déjela vacía para conservar la contraseña actual.',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}),
    )

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

    field_order = ['first_name', 'last_name', 'email', 'codigo_universitario', 'identificacion',
                   'rol', 'carrera', 'estado', 'telefono', 'nueva_password']

    def __init__(self, *args, editor=None, **kwargs):
        # editor: el User que está editando, para impedir que se bloquee o se quite el rol a sí mismo
        super().__init__(*args, **kwargs)
        self.editor = editor
        user = self.instance.user
        self.fields['first_name'].initial = user.first_name
        self.fields['last_name'].initial = user.last_name
        self.fields['email'].initial = user.email

    def es_su_propia_cuenta(self):
        return self.editor is not None and self.editor.pk == self.instance.user_id

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.user_id).exists():
            raise forms.ValidationError('Ya existe otro usuario con ese correo.')
        return email

    def clean_estado(self):
        estado = self.cleaned_data['estado']
        if self.es_su_propia_cuenta() and estado != 'activo':
            raise forms.ValidationError('No puede bloquear su propia cuenta.')
        return estado

    def clean_rol(self):
        rol = self.cleaned_data['rol']
        if self.es_su_propia_cuenta() and self.instance.rol == 'bibliotecario' and rol != 'bibliotecario':
            raise forms.ValidationError('No puede quitarse a sí mismo el rol de bibliotecario.')
        return rol

    def clean_nueva_password(self):
        password = self.cleaned_data.get('nueva_password')
        if password:
            validate_password(password, self.instance.user)
        return password

    def save(self, commit=True):
        with transaction.atomic():
            perfil = super().save(commit=commit)
            user = perfil.user
            user.first_name = self.cleaned_data['first_name']
            user.last_name = self.cleaned_data['last_name']
            user.email = self.cleaned_data['email']
            if self.cleaned_data.get('nueva_password'):
                user.set_password(self.cleaned_data['nueva_password'])
            user.save()
        return perfil


class RegistroForm(forms.Form):
    """Formulario que crea User + UsuarioBiblioteca al mismo tiempo."""
    first_name = forms.CharField(max_length=150, label='Nombres', widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=150, label='Apellidos', widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(label='Correo electrónico', widget=forms.EmailInput(attrs={'class': 'form-control'}))
    username = forms.CharField(max_length=150, label='Usuario', widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}), label='Contraseña')
    codigo_universitario = forms.CharField(max_length=20, label='Código universitario', widget=forms.TextInput(attrs={'class': 'form-control'}))
    identificacion = forms.CharField(max_length=20, label='Identificación', widget=forms.TextInput(attrs={'class': 'form-control'}))
    rol = forms.ChoiceField(choices=UsuarioBiblioteca.ROL_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    carrera = forms.CharField(max_length=150, required=False, label='Carrera', widget=forms.TextInput(attrs={'class': 'form-control'}))
    estado = forms.ChoiceField(choices=UsuarioBiblioteca.ESTADO_CHOICES, initial='activo', label='Estado', widget=forms.Select(attrs={'class': 'form-select'}))
    telefono = forms.CharField(max_length=20, required=False, label='Teléfono', widget=forms.TextInput(attrs={'class': 'form-control'}))

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Ya existe un usuario con ese correo.')
        return email

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('Ese nombre de usuario ya está en uso.')
        return username

    def clean_codigo_universitario(self):
        codigo = self.cleaned_data['codigo_universitario']
        if UsuarioBiblioteca.objects.filter(codigo_universitario=codigo).exists():
            raise forms.ValidationError('Ya existe un usuario con ese código universitario.')
        return codigo

    def clean_identificacion(self):
        identificacion = self.cleaned_data['identificacion']
        if UsuarioBiblioteca.objects.filter(identificacion=identificacion).exists():
            raise forms.ValidationError('Ya existe un usuario con esa identificación.')
        return identificacion

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get('password')
        if password:
            # Valida contra los AUTH_PASSWORD_VALIDATORS de settings (longitud, comunes, solo números, parecida al usuario)
            usuario_tmp = User(username=cleaned.get('username', ''), email=cleaned.get('email', ''),
                               first_name=cleaned.get('first_name', ''), last_name=cleaned.get('last_name', ''))
            try:
                validate_password(password, usuario_tmp)
            except forms.ValidationError as e:
                self.add_error('password', e)
        return cleaned

    def save(self):
        data = self.cleaned_data
        # atomic: si falla el perfil, tampoco queda creado el login
        with transaction.atomic():
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
                estado=data['estado'],
                telefono=data.get('telefono', ''),
            )
        return perfil
