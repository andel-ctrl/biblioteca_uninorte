"""Nombres de tabla del diseño (autor, categoria, libro, libro_autor, ejemplar) y ubicación del
ejemplar en dos columnas atómicas: «Sala A / Estante 3» pasa a sala='A', estante='3'."""
import re

from django.db import migrations, models

PATRON = re.compile(r'^\s*sala\s+(?P<sala>.+?)\s*/\s*estante\s+(?P<estante>[^/]+?)\s*(?:/.*)?$', re.IGNORECASE)


def separar_ubicacion(apps, schema_editor):
    Ejemplar = apps.get_model('catalogos', 'Ejemplar')
    for e in Ejemplar.objects.all():
        texto = (e.ubicacion or '').strip()
        m = PATRON.match(texto)
        if m:
            e.sala, e.estante = m.group('sala')[:30], m.group('estante')[:30]
        else:  # formato libre: se conserva completo en sala para no perder nada
            e.sala, e.estante = (texto or 'Sin asignar')[:30], '—'
        e.save(update_fields=['sala', 'estante'])
    # Las llaves foráneas son diferidas: se verifican ya, para que los cambios de estructura
    # que siguen en esta migración no choquen con verificaciones pendientes de PostgreSQL
    schema_editor.execute('SET CONSTRAINTS ALL IMMEDIATE')


def unir_ubicacion(apps, schema_editor):
    Ejemplar = apps.get_model('catalogos', 'Ejemplar')
    for e in Ejemplar.objects.all():
        e.ubicacion = f'Sala {e.sala} / Estante {e.estante}'
        e.save(update_fields=['ubicacion'])


class Migration(migrations.Migration):

    dependencies = [
        ('catalogos', '0003_extension_unaccent'),
    ]

    operations = [
        migrations.AddField('ejemplar', 'sala', models.CharField(max_length=30, default=''), preserve_default=False),
        migrations.AddField('ejemplar', 'estante', models.CharField(max_length=30, default=''), preserve_default=False),
        migrations.RunPython(separar_ubicacion, unir_ubicacion),
        migrations.RemoveField('ejemplar', 'ubicacion'),
        migrations.AlterModelTable('autor', 'autor'),
        migrations.AlterModelTable('categoria', 'categoria'),
        migrations.AlterModelTable('libro', 'libro'),
        migrations.AlterModelTable('ejemplar', 'ejemplar'),
        migrations.AlterField('libro', 'autores',
                              models.ManyToManyField(to='catalogos.autor', related_name='libros', db_table='libro_autor')),
    ]
