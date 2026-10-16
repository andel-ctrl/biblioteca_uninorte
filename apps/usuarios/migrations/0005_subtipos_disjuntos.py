"""La base garantiza que la especialización es DISJUNTA y que «tipo» coincide con el subtipo.

· usuario: el par (id, tipo) pasa a ser único.
· lector y bibliotecario: guardan su tipo fijo (CHECK tipo = 'lector' / 'bibliotecario') y su
  llave foránea apunta al PAR (usuario_id, tipo) → usuario (id, tipo).

Así una fila de lector solo puede apuntar a un usuario de tipo lector (y lo mismo con
bibliotecario): un usuario nunca queda en los dos subtipos ni en el que no le corresponde, y su
tipo no se puede cambiar mientras tenga fila en un subtipo. La llave foránea simple que creaba
Django se reemplaza por la compuesta (Django no declara llaves foráneas compuestas: va en SQL).
Si una base tuviera datos incoherentes, esta migración falla y no cambia nada.
"""
import django.db.models.deletion
from django.db import migrations, models

LLAVES_COMPUESTAS = """
ALTER TABLE lector ADD CONSTRAINT lector_usuario_id_tipo_fkey
    FOREIGN KEY (usuario_id, tipo) REFERENCES usuario (id, tipo) ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE bibliotecario ADD CONSTRAINT bibliotecario_usuario_id_tipo_fkey
    FOREIGN KEY (usuario_id, tipo) REFERENCES usuario (id, tipo) ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED;
"""
QUITAR_LLAVES_COMPUESTAS = """
ALTER TABLE lector DROP CONSTRAINT lector_usuario_id_tipo_fkey;
ALTER TABLE bibliotecario DROP CONSTRAINT bibliotecario_usuario_id_tipo_fkey;
"""


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0004_bibliotecario_turno'),
        # después de renombrar restricciones: así los nombres quedan iguales en toda base
        ('prestamos', '0005_nombres_de_restricciones'),
    ]

    operations = [
        migrations.AddConstraint('usuario', models.UniqueConstraint(fields=['id', 'tipo'], name='usuario_id_tipo_key')),

        migrations.AddField('lector', 'tipo', models.CharField(max_length=20, db_default='lector', editable=False)),
        migrations.AddConstraint('lector', models.CheckConstraint(
            condition=models.Q(tipo='lector'), name='lector_tipo_fijo',
            violation_error_message='La tabla lector solo admite usuarios de tipo lector.')),
        migrations.AddField('bibliotecario', 'tipo', models.CharField(max_length=20, db_default='bibliotecario', editable=False)),
        migrations.AddConstraint('bibliotecario', models.CheckConstraint(
            condition=models.Q(tipo='bibliotecario'), name='bibliotecario_tipo_fijo',
            violation_error_message='La tabla bibliotecario solo admite usuarios de tipo bibliotecario.')),

        # La llave foránea simple (usuario_id → usuario.id) se reemplaza por la compuesta
        migrations.AlterField('lector', 'usuario', models.OneToOneField(
            on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='lector',
            serialize=False, to='usuarios.usuario', db_constraint=False)),
        migrations.AlterField('bibliotecario', 'usuario', models.OneToOneField(
            on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='bibliotecario',
            serialize=False, to='usuarios.usuario', db_constraint=False)),
        migrations.RunSQL(LLAVES_COMPUESTAS, QUITAR_LLAVES_COMPUESTAS),
    ]
