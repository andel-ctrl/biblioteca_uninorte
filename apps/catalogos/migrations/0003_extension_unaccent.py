# Activa la extensión unaccent de PostgreSQL: permite buscar "garcia" y encontrar "García".
# Es una extensión «confiable» (PostgreSQL 13+): basta con permiso CREATE sobre la base de datos.
from django.contrib.postgres.operations import UnaccentExtension
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('catalogos', '0002_restricciones_check'),
    ]

    operations = [
        UnaccentExtension(),
    ]
