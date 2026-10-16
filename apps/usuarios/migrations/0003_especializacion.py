"""Especialización total y disjunta de usuarios.

usuario (supertipo, discriminador «tipo») → lector (rol, carrera) | bibliotecario.
Cada usuario existente pasa a su subtipo según el rol que tenía; rol y carrera se mueven a lector.
"""
import django.db.models.deletion
from django.db import migrations, models


def repartir_usuarios(apps, schema_editor):
    Usuario = apps.get_model('usuarios', 'Usuario')
    Lector = apps.get_model('usuarios', 'Lector')
    Bibliotecario = apps.get_model('usuarios', 'Bibliotecario')
    for u in Usuario.objects.all():
        if u.rol == 'bibliotecario':
            u.tipo = 'bibliotecario'
            Bibliotecario.objects.create(usuario=u)
        else:
            u.tipo = 'lector'
            Lector.objects.create(usuario=u, rol=u.rol, carrera=u.carrera)
        u.save(update_fields=['tipo'])
    # Las llaves foráneas son diferidas: se verifican ya, para que los cambios de estructura
    # que siguen en esta migración no choquen con verificaciones pendientes de PostgreSQL
    schema_editor.execute('SET CONSTRAINTS ALL IMMEDIATE')


def juntar_usuarios(apps, schema_editor):
    Usuario = apps.get_model('usuarios', 'Usuario')
    for u in Usuario.objects.all():
        lector = getattr(u, 'lector', None)
        u.rol = lector.rol if lector else 'bibliotecario'
        u.carrera = lector.carrera if lector else ''
        u.save(update_fields=['rol', 'carrera'])


class Migration(migrations.Migration):

    # Las migraciones viejas de préstamos apuntan a «UsuarioBiblioteca»: el cambio de nombre
    # debe ir después de ellas, o una base nueva (vacía) no podría construirse
    dependencies = [
        ('usuarios', '0002_restricciones_check'),
        ('prestamos', '0003_restricciones_check'),
    ]

    operations = [
        migrations.RenameModel('UsuarioBiblioteca', 'Usuario'),
        migrations.AlterModelOptions('usuario', options={'verbose_name': 'Usuario', 'verbose_name_plural': 'Usuarios'}),
        migrations.AddField('usuario', 'tipo', models.CharField(
            max_length=20, default='lector', choices=[('lector', 'Lector'), ('bibliotecario', 'Bibliotecario')])),
        migrations.CreateModel(
            name='Lector',
            fields=[
                ('usuario', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True,
                                                 related_name='lector', serialize=False, to='usuarios.usuario')),
                ('rol', models.CharField(choices=[('estudiante', 'Estudiante'), ('docente', 'Docente')],
                                         default='estudiante', max_length=20)),
                ('carrera', models.CharField(blank=True, max_length=150)),
            ],
            options={
                'verbose_name': 'Lector', 'verbose_name_plural': 'Lectores', 'db_table': 'lector',
                'constraints': [models.CheckConstraint(condition=models.Q(rol__in=['estudiante', 'docente']),
                                                       name='lector_rol_valido',
                                                       violation_error_message='El rol del lector no es válido.')],
            },
        ),
        migrations.CreateModel(
            name='Bibliotecario',
            fields=[
                ('usuario', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True,
                                                 related_name='bibliotecario', serialize=False, to='usuarios.usuario')),
            ],
            options={'verbose_name': 'Bibliotecario', 'verbose_name_plural': 'Bibliotecarios', 'db_table': 'bibliotecario'},
        ),
        migrations.RunPython(repartir_usuarios, juntar_usuarios),
        migrations.RemoveConstraint('usuario', 'usuario_rol_valido'),
        migrations.RemoveField('usuario', 'rol'),
        migrations.RemoveField('usuario', 'carrera'),
        migrations.AlterField('usuario', 'telefono', models.CharField(blank=True, max_length=20, verbose_name='Teléfono')),
        migrations.AddConstraint('usuario', models.CheckConstraint(
            condition=models.Q(tipo__in=['lector', 'bibliotecario']), name='usuario_tipo_valido',
            violation_error_message='El tipo de usuario no es válido.')),
        migrations.AlterModelTable('usuario', 'usuario'),
    ]
