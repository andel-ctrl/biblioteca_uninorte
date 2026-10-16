from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from .models import Usuario, Lector, Bibliotecario

# Un solo selector «Rol» en pantalla; por dentro se traduce a la especialización:
# bibliotecario → usuario tipo bibliotecario + fila en bibliotecario;
# estudiante / docente → usuario tipo lector + fila en lector con ese rol.
ROL_CHOICES = Lector.ROL_CHOICES + [('bibliotecario', 'Bibliotecario')]
TURNO_OPCIONES = [('', 'Sin asignar')] + Bibliotecario.TURNO_CHOICES


class UsuarioForm(forms.ModelForm):
    """Edita la cuenta (nombres, correo, contraseña), el usuario y su subtipo en un solo formulario.
    El tipo (lector o bibliotecario) no cambia al editar: un lector puede pasar de estudiante a
    docente, pero no a bibliotecario (su historial de préstamos es de lector)."""
    first_name = forms.CharField(max_length=150, label='Nombres', widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=150, label='Apellidos', widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(label='Correo electrónico', widget=forms.EmailInput(attrs={'class': 'form-control'}))
    rol = forms.ChoiceField(choices=ROL_CHOICES, label='Rol', widget=forms.Select(attrs={'class': 'form-select'}))
    carrera = forms.CharField(max_length=150, required=False, label='Carrera',
                              widget=forms.TextInput(attrs={'class': 'form-control'}))
    turno = forms.ChoiceField(choices=TURNO_OPCIONES, required=False, label='Turno',
                              widget=forms.Select(attrs={'class': 'form-select'}))
    nueva_password = forms.CharField(
        required=False, label='Nueva contraseña',
        help_text='Déjala vacía para conservar la contraseña actual.',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}),
    )

    class Meta:
        model = Usuario
        fields = ['codigo_universitario', 'identificacion', 'estado', 'telefono']
        labels = {'telefono': 'Teléfono'}
        error_messages = {
            'codigo_universitario': {'unique': 'Ya existe un usuario con ese código universitario.'},
            'identificacion': {'unique': 'Ya existe un usuario con esa identificación.'},
        }
        widgets = {
            'codigo_universitario': forms.TextInput(attrs={'class': 'form-control'}),
            'identificacion': forms.TextInput(attrs={'class': 'form-control'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
        }

    field_order = ['first_name', 'last_name', 'email', 'codigo_universitario', 'identificacion',
                   'rol', 'carrera', 'turno', 'estado', 'telefono', 'nueva_password']

    def __init__(self, *args, editor=None, **kwargs):
        # editor: el User que está editando, para impedir que se bloquee o se quite el rol a sí mismo
        super().__init__(*args, **kwargs)
        self.editor = editor
        user = self.instance.user
        self.fields['first_name'].initial = user.first_name
        self.fields['last_name'].initial = user.last_name
        self.fields['email'].initial = user.email
        # El rol ofrece solo opciones del mismo subtipo
        if self.instance.es_bibliotecario():
            self.fields['rol'].choices = [('bibliotecario', 'Bibliotecario')]
            self.fields['rol'].initial = 'bibliotecario'
            del self.fields['carrera']  # la carrera es del lector
            self.fields['turno'].initial = self.instance.bibliotecario.turno
        else:
            self.fields['rol'].choices = Lector.ROL_CHOICES
            self.fields['rol'].initial = self.instance.lector.rol
            self.fields['rol'].help_text = 'Un lector no puede pasar a bibliotecario: para eso se crea otra cuenta.'
            self.fields['carrera'].initial = self.instance.lector.carrera
            del self.fields['turno']  # el turno es del bibliotecario

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
            raise forms.ValidationError('No puedes bloquear tu propia cuenta.')
        return estado


    def clean_nueva_password(self):
        password = self.cleaned_data.get('nueva_password')
        if password:
            validate_password(password, self.instance.user)
        return password

    def save(self, commit=True):
        with transaction.atomic():
            perfil = super().save(commit=commit)
            if perfil.es_lector():
                perfil.lector.rol = self.cleaned_data['rol']
                perfil.lector.carrera = self.cleaned_data.get('carrera', '')
                perfil.lector.save()
            else:
                perfil.bibliotecario.turno = self.cleaned_data.get('turno', '')
                perfil.bibliotecario.save()
            user = perfil.user
            user.first_name = self.cleaned_data['first_name']
            user.last_name = self.cleaned_data['last_name']
            user.email = self.cleaned_data['email']
            if self.cleaned_data.get('nueva_password'):
                user.set_password(self.cleaned_data['nueva_password'])
            user.save()
        return perfil


class RegistroForm(forms.Form):
    """Crea la cuenta (User), el usuario y su subtipo (lector o bibliotecario) en una transacción."""
    first_name = forms.CharField(max_length=150, label='Nombres', widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=150, label='Apellidos', widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(label='Correo electrónico', widget=forms.EmailInput(attrs={'class': 'form-control'}))
    username = forms.CharField(max_length=150, label='Usuario', widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}), label='Contraseña')
    codigo_universitario = forms.CharField(max_length=20, label='Código universitario', widget=forms.TextInput(attrs={'class': 'form-control'}))
    identificacion = forms.CharField(max_length=20, label='Identificación', widget=forms.TextInput(attrs={'class': 'form-control'}))
    rol = forms.ChoiceField(choices=ROL_CHOICES, label='Rol', widget=forms.Select(attrs={'class': 'form-select'}),
                            help_text='Estudiante o docente: lector, puede pedir libros. Bibliotecario: aprueba y registra préstamos.')
    carrera = forms.CharField(max_length=150, required=False, label='Carrera', help_text='Solo para lectores.',
                              widget=forms.TextInput(attrs={'class': 'form-control'}))
    turno = forms.ChoiceField(choices=TURNO_OPCIONES, required=False, label='Turno', help_text='Solo para bibliotecarios.',
                              widget=forms.Select(attrs={'class': 'form-select'}))
    estado = forms.ChoiceField(choices=Usuario.ESTADO_CHOICES, initial='activo', label='Estado', widget=forms.Select(attrs={'class': 'form-select'}))
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
        if Usuario.objects.filter(codigo_universitario=codigo).exists():
            raise forms.ValidationError('Ya existe un usuario con ese código universitario.')
        return codigo

    def clean_identificacion(self):
        identificacion = self.cleaned_data['identificacion']
        if Usuario.objects.filter(identificacion=identificacion).exists():
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
            es_bibliotecario = data['rol'] == 'bibliotecario'
            perfil = Usuario.objects.create(
                user=user,
                codigo_universitario=data['codigo_universitario'],
                identificacion=data['identificacion'],
                tipo='bibliotecario' if es_bibliotecario else 'lector',
                estado=data['estado'],
                telefono=data.get('telefono', ''),
            )
            if es_bibliotecario:
                Bibliotecario.objects.create(usuario=perfil, turno=data.get('turno', ''))
            else:
                Lector.objects.create(usuario=perfil, rol=data['rol'], carrera=data.get('carrera', ''))
        return perfil
