import unicodedata

from django.db import models


def clave_nombre(texto):
    """Forma de comparar nombres sin importar mayúsculas, espacios ni tildes: «Núñez» = «nunez».
    Es el mismo criterio del buscador del catálogo (extensión unaccent de PostgreSQL)."""
    texto = unicodedata.normalize('NFKD', texto.strip().casefold())
    return ''.join(c for c in texto if not unicodedata.combining(c))


class Autor(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    biografia = models.TextField(blank=True)

    class Meta:
        db_table = 'autor'
        verbose_name = 'Autor'
        verbose_name_plural = 'Autores'
        ordering = ['apellido', 'nombre']

    def __str__(self):
        return f"{self.apellido}, {self.nombre}"

    @classmethod
    def buscar_igual(cls, nombre, apellido, excluir_pk=None):
        """Autor con el mismo nombre y apellido sin importar mayúsculas, espacios ni tildes
        («García Márquez» = «garcia marquez»), igual que el buscador del catálogo.
        Se compara en Python: con la intercalación "C" de PostgreSQL, iexact no iguala "Í" con "í"."""
        clave = (clave_nombre(nombre), clave_nombre(apellido))
        for autor in cls.objects.exclude(pk=excluir_pk).only('nombre', 'apellido'):
            if (clave_nombre(autor.nombre), clave_nombre(autor.apellido)) == clave:
                return autor
        return None


class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)

    class Meta:
        db_table = 'categoria'
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Libro(models.Model):
    isbn = models.CharField(max_length=20, unique=True, verbose_name='ISBN')
    titulo = models.CharField(max_length=255, verbose_name='Título')
    # Muchos a muchos: tabla intermedia libro_autor (libro_id, autor_id), el par no se repite
    autores = models.ManyToManyField(Autor, related_name='libros', db_table='libro_autor')
    editorial = models.CharField(max_length=150)
    anio_publicacion = models.PositiveIntegerField(verbose_name='Año de publicación')
    categoria = models.ForeignKey(
        Categoria, on_delete=models.SET_NULL, null=True, blank=True, related_name='libros'
    )
    descripcion = models.TextField(blank=True, verbose_name='Descripción')
    portada = models.ImageField(upload_to='portadas/', null=True, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'libro'
        verbose_name = 'Libro'
        verbose_name_plural = 'Libros'
        ordering = ['titulo']
        constraints = [
            # Restricción de integridad en la propia BD (no solo en el formulario)
            models.CheckConstraint(condition=models.Q(anio_publicacion__gte=1000, anio_publicacion__lte=2100),
                                   name='libro_anio_publicacion_valido',
                violation_error_message='El año de publicación debe estar entre 1000 y 2100.'),
        ]

    def __str__(self):
        return f"{self.titulo} ({self.isbn})"

    def ejemplares_disponibles(self):
        return self.ejemplares.filter(estado='disponible').count()

    def total_ejemplares(self):
        return self.ejemplares.count()


class Ejemplar(models.Model):
    ESTADO_CHOICES = [
        ('disponible', 'Disponible'),
        ('prestado', 'Prestado'),
        ('perdido', 'Perdido'),
        ('mantenimiento', 'En mantenimiento'),
    ]

    libro = models.ForeignKey(Libro, on_delete=models.CASCADE, related_name='ejemplares')
    codigo_barras = models.CharField(max_length=50, unique=True, verbose_name='Código de barras')
    # Ubicación en dos columnas atómicas (primera forma normal): se puede consultar por sala
    sala = models.CharField(max_length=30)
    estante = models.CharField(max_length=30)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='disponible')
    notas = models.TextField(blank=True)
    fecha_adquisicion = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'ejemplar'
        verbose_name = 'Ejemplar'
        verbose_name_plural = 'Ejemplares'
        constraints = [
            models.CheckConstraint(condition=models.Q(estado__in=['disponible', 'prestado', 'perdido', 'mantenimiento']),
                                   name='ejemplar_estado_valido',
                violation_error_message='El estado del ejemplar no es válido.'),
        ]

    def __str__(self):
        return f"{self.codigo_barras} — {self.libro.titulo} [{self.get_estado_display()}]"

    @property
    def ubicacion(self):
        """Texto para mostrar: «Sala A / Estante 3»."""
        return f'Sala {self.sala} / Estante {self.estante}'

    def esta_disponible(self):
        return self.estado == 'disponible'

    def prestamo_activo(self):
        return self.prestamos.filter(estado__in=['activo', 'vencido']).first()
