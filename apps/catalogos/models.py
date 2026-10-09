from django.db import models


class Autor(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    biografia = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Autor'
        verbose_name_plural = 'Autores'
        ordering = ['apellido', 'nombre']

    def __str__(self):
        return f"{self.apellido}, {self.nombre}"


class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Libro(models.Model):
    isbn = models.CharField(max_length=20, unique=True, verbose_name='ISBN')
    titulo = models.CharField(max_length=255, verbose_name='Título')
    autores = models.ManyToManyField(Autor, related_name='libros')
    editorial = models.CharField(max_length=150)
    anio_publicacion = models.PositiveIntegerField(verbose_name='Año de publicación')
    categoria = models.ForeignKey(
        Categoria, on_delete=models.SET_NULL, null=True, blank=True, related_name='libros'
    )
    descripcion = models.TextField(blank=True, verbose_name='Descripción')
    portada = models.ImageField(upload_to='portadas/', null=True, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Libro'
        verbose_name_plural = 'Libros'
        ordering = ['titulo']

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
    ubicacion = models.CharField(max_length=100, verbose_name='Ubicación (sala/estante)')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='disponible')
    notas = models.TextField(blank=True)
    fecha_adquisicion = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = 'Ejemplar'
        verbose_name_plural = 'Ejemplares'

    def __str__(self):
        return f"{self.codigo_barras} — {self.libro.titulo} [{self.get_estado_display()}]"

    def esta_disponible(self):
        return self.estado == 'disponible'

    def prestamo_activo(self):
        return self.prestamos.filter(estado__in=['activo', 'vencido']).first()
