from django import forms
from .models import Libro, Ejemplar, Autor, Categoria
from .portadas import recortar_portada


class LibroForm(forms.ModelForm):
    class Meta:
        model = Libro
        fields = ['isbn', 'titulo', 'autores', 'editorial', 'anio_publicacion', 'categoria', 'descripcion', 'portada']
        labels = {'categoria': 'Categoría'}
        widgets = {
            'isbn': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '978-...'}),
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            # Casillas (el formulario las muestra con buscador y etiquetas de los elegidos)
            'autores': forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
            # list=...: el navegador sugiere las editoriales ya registradas (sigue siendo texto libre)
            'editorial': forms.TextInput(attrs={'class': 'form-control', 'list': 'editoriales-registradas', 'autocomplete': 'off'}),
            'anio_publicacion': forms.NumberInput(attrs={'class': 'form-control', 'min': 1000, 'max': 2099}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'portada': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }
        help_texts = {
            'editorial': 'Elige una de las sugerencias si la editorial ya existe, para escribirla siempre igual.',
        }
        error_messages = {'isbn': {'unique': 'Ya existe un libro con este ISBN.'}}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Django 6.1 aún no trae traducido su texto vacío ("- Select an option -")
        self.fields['categoria'].empty_label = 'Sin categoría'
        # Editoriales ya usadas en el catálogo, para sugerirlas al escribir
        self.editoriales = (Libro.objects.exclude(editorial='').order_by('editorial')
                            .values_list('editorial', flat=True).distinct())

    def clean_portada(self):
        # Una portada nueva se recorta a la tapa del libro (sin fondo ni márgenes)
        portada = self.cleaned_data.get('portada')
        if portada and portada is not self.initial.get('portada') and hasattr(portada, 'content_type'):
            return recortar_portada(portada)
        return portada


class EjemplarForm(forms.ModelForm):
    class Meta:
        model = Ejemplar
        fields = ['codigo_barras', 'sala', 'estante', 'estado', 'notas', 'fecha_adquisicion']
        help_texts = {'sala': 'Solo la letra o el nombre de la sala: «A».', 'estante': 'Solo el número del estante: «3».'}
        widgets = {
            'codigo_barras': forms.TextInput(attrs={'class': 'form-control'}),
            'sala': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: A'}),
            'estante': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 3'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'notas': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'fecha_adquisicion': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
        }
        error_messages = {'codigo_barras': {'unique': 'Ya existe un ejemplar con este código de barras.'}}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        estado = self.fields['estado']
        if self.instance.pk and self.instance.prestamo_activo():
            # Con un préstamo en curso el estado lo manejan la devolución o la pérdida: no se cambia a mano
            estado.disabled = True
            estado.help_text = 'Tiene un préstamo en curso: el estado cambia al registrar la devolución o la pérdida.'
        else:
            # «Prestado» solo lo pone la aprobación de un préstamo
            estado.choices = [c for c in estado.choices if c[0] != 'prestado']


class AutorForm(forms.ModelForm):
    class Meta:
        model = Autor
        fields = ['nombre', 'apellido', 'biografia']
        labels = {'biografia': 'Biografía'}
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control'}),
            'biografia': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, evitar_duplicados=True, **kwargs):
        # El alta rápida desde el libro no lo usa: allí un duplicado se resuelve devolviendo el autor existente
        super().__init__(*args, **kwargs)
        self.evitar_duplicados = evitar_duplicados

    def clean(self):
        datos = super().clean()
        nombre, apellido = (datos.get('nombre') or '').strip(), (datos.get('apellido') or '').strip()
        if self.evitar_duplicados and nombre and apellido:
            if Autor.buscar_igual(nombre, apellido, excluir_pk=self.instance.pk):
                raise forms.ValidationError(f'Ya existe un autor registrado como «{apellido}, {nombre}».')
        return datos


class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nombre', 'descripcion']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
