"""Atributo propio del bibliotecario: el turno (mañana, tarde o noche).
Es opcional: los bibliotecarios que ya existen quedan sin turno asignado (texto vacío)."""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0003_especializacion'),
    ]

    operations = [
        migrations.AddField(
            model_name='bibliotecario',
            name='turno',
            field=models.CharField(blank=True, max_length=10,
                                   choices=[('manana', 'Mañana'), ('tarde', 'Tarde'), ('noche', 'Noche')]),
        ),
        migrations.AddConstraint(
            model_name='bibliotecario',
            constraint=models.CheckConstraint(condition=models.Q(turno__in=['', 'manana', 'tarde', 'noche']),
                                              name='bibliotecario_turno_valido',
                                              violation_error_message='El turno debe ser mañana, tarde o noche.'),
        ),
    ]
