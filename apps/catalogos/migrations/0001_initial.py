import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Autor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100)),
                ('apellido', models.CharField(max_length=100)),
                ('biografia', models.TextField(blank=True)),
            ],
            options={
                'verbose_name': 'Autor',
                'verbose_name_plural': 'Autores',
                'ordering': ['apellido', 'nombre'],
            },
        ),
        migrations.CreateModel(
            name='Categoria',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100, unique=True)),
                ('descripcion', models.TextField(blank=True)),
            ],
            options={
                'verbose_name': 'Categoría',
                'verbose_name_plural': 'Categorías',
                'ordering': ['nombre'],
            },
        ),
        migrations.CreateModel(
            name='Libro',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('isbn', models.CharField(max_length=20, unique=True, verbose_name='ISBN')),
                ('titulo', models.CharField(max_length=255, verbose_name='Título')),
                ('editorial', models.CharField(max_length=150)),
                ('anio_publicacion', models.PositiveIntegerField(verbose_name='Año de publicación')),
                ('descripcion', models.TextField(blank=True, verbose_name='Descripción')),
                ('portada', models.ImageField(blank=True, null=True, upload_to='portadas/')),
                ('creado_en', models.DateTimeField(auto_now_add=True)),
                ('autores', models.ManyToManyField(related_name='libros', to='catalogos.autor')),
                ('categoria', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='libros', to='catalogos.categoria')),
            ],
            options={
                'verbose_name': 'Libro',
                'verbose_name_plural': 'Libros',
                'ordering': ['titulo'],
            },
        ),
        migrations.CreateModel(
            name='Ejemplar',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('codigo_barras', models.CharField(max_length=50, unique=True, verbose_name='Código de barras')),
                ('ubicacion', models.CharField(max_length=100, verbose_name='Ubicación (sala/estante)')),
                ('estado', models.CharField(choices=[('disponible', 'Disponible'), ('prestado', 'Prestado'), ('perdido', 'Perdido'), ('mantenimiento', 'En mantenimiento')], default='disponible', max_length=20)),
                ('notas', models.TextField(blank=True)),
                ('fecha_adquisicion', models.DateField(blank=True, null=True)),
                ('libro', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ejemplares', to='catalogos.libro')),
            ],
            options={
                'verbose_name': 'Ejemplar',
                'verbose_name_plural': 'Ejemplares',
            },
        ),
    ]
