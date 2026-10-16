"""Valores por defecto en la propia base (DEFAULT), iguales a los de sql/01_creacion_tablas.sql.

Django pone los valores por defecto desde Python, así que una base creada con «migrate» no los
tiene en PostgreSQL. Con esta migración, un INSERT escrito a mano (por ejemplo en pgAdmin) puede
omitir las columnas opcionales —carrera, turno, teléfono, estado...— igual que en la base creada
con los scripts. No cambia datos ni reglas.
"""
from django.db import migrations

VALORES = """
ALTER TABLE auth_user ALTER COLUMN date_joined SET DEFAULT now();
ALTER TABLE auth_user ALTER COLUMN email SET DEFAULT '';
ALTER TABLE auth_user ALTER COLUMN first_name SET DEFAULT '';
ALTER TABLE auth_user ALTER COLUMN is_active SET DEFAULT true;
ALTER TABLE auth_user ALTER COLUMN is_staff SET DEFAULT false;
ALTER TABLE auth_user ALTER COLUMN is_superuser SET DEFAULT false;
ALTER TABLE auth_user ALTER COLUMN last_name SET DEFAULT '';
ALTER TABLE autor ALTER COLUMN biografia SET DEFAULT '';
ALTER TABLE bibliotecario ALTER COLUMN turno SET DEFAULT '';
ALTER TABLE categoria ALTER COLUMN descripcion SET DEFAULT '';
ALTER TABLE devolucion ALTER COLUMN creado_en SET DEFAULT now();
ALTER TABLE devolucion ALTER COLUMN detalle_observacion SET DEFAULT '';
ALTER TABLE devolucion ALTER COLUMN fecha_devolucion SET DEFAULT CURRENT_DATE;
ALTER TABLE devolucion ALTER COLUMN observacion SET DEFAULT '';
ALTER TABLE ejemplar ALTER COLUMN estado SET DEFAULT 'disponible';
ALTER TABLE ejemplar ALTER COLUMN notas SET DEFAULT '';
ALTER TABLE lector ALTER COLUMN carrera SET DEFAULT '';
ALTER TABLE lector ALTER COLUMN rol SET DEFAULT 'estudiante';
ALTER TABLE libro ALTER COLUMN creado_en SET DEFAULT now();
ALTER TABLE libro ALTER COLUMN descripcion SET DEFAULT '';
ALTER TABLE multa ALTER COLUMN pagada SET DEFAULT false;
ALTER TABLE prestamo ALTER COLUMN estado SET DEFAULT 'pendiente';
ALTER TABLE prestamo ALTER COLUMN fecha_solicitud SET DEFAULT now();
ALTER TABLE prestamo ALTER COLUMN observaciones SET DEFAULT '';
ALTER TABLE tarifa_multa ALTER COLUMN activa SET DEFAULT true;
ALTER TABLE tarifa_multa ALTER COLUMN vigente_desde SET DEFAULT CURRENT_DATE;
ALTER TABLE usuario ALTER COLUMN estado SET DEFAULT 'activo';
ALTER TABLE usuario ALTER COLUMN fecha_registro SET DEFAULT now();
ALTER TABLE usuario ALTER COLUMN telefono SET DEFAULT '';
"""

QUITAR = """
ALTER TABLE auth_user ALTER COLUMN date_joined DROP DEFAULT;
ALTER TABLE auth_user ALTER COLUMN email DROP DEFAULT;
ALTER TABLE auth_user ALTER COLUMN first_name DROP DEFAULT;
ALTER TABLE auth_user ALTER COLUMN is_active DROP DEFAULT;
ALTER TABLE auth_user ALTER COLUMN is_staff DROP DEFAULT;
ALTER TABLE auth_user ALTER COLUMN is_superuser DROP DEFAULT;
ALTER TABLE auth_user ALTER COLUMN last_name DROP DEFAULT;
ALTER TABLE autor ALTER COLUMN biografia DROP DEFAULT;
ALTER TABLE bibliotecario ALTER COLUMN turno DROP DEFAULT;
ALTER TABLE categoria ALTER COLUMN descripcion DROP DEFAULT;
ALTER TABLE devolucion ALTER COLUMN creado_en DROP DEFAULT;
ALTER TABLE devolucion ALTER COLUMN detalle_observacion DROP DEFAULT;
ALTER TABLE devolucion ALTER COLUMN fecha_devolucion DROP DEFAULT;
ALTER TABLE devolucion ALTER COLUMN observacion DROP DEFAULT;
ALTER TABLE ejemplar ALTER COLUMN estado DROP DEFAULT;
ALTER TABLE ejemplar ALTER COLUMN notas DROP DEFAULT;
ALTER TABLE lector ALTER COLUMN carrera DROP DEFAULT;
ALTER TABLE lector ALTER COLUMN rol DROP DEFAULT;
ALTER TABLE libro ALTER COLUMN creado_en DROP DEFAULT;
ALTER TABLE libro ALTER COLUMN descripcion DROP DEFAULT;
ALTER TABLE multa ALTER COLUMN pagada DROP DEFAULT;
ALTER TABLE prestamo ALTER COLUMN estado DROP DEFAULT;
ALTER TABLE prestamo ALTER COLUMN fecha_solicitud DROP DEFAULT;
ALTER TABLE prestamo ALTER COLUMN observaciones DROP DEFAULT;
ALTER TABLE tarifa_multa ALTER COLUMN activa DROP DEFAULT;
ALTER TABLE tarifa_multa ALTER COLUMN vigente_desde DROP DEFAULT;
ALTER TABLE usuario ALTER COLUMN estado DROP DEFAULT;
ALTER TABLE usuario ALTER COLUMN fecha_registro DROP DEFAULT;
ALTER TABLE usuario ALTER COLUMN telefono DROP DEFAULT;
"""


class Migration(migrations.Migration):

    dependencies = [
        ('prestamos', '0005_nombres_de_restricciones'),
        ('usuarios', '0005_subtipos_disjuntos'),
    ]

    operations = [
        migrations.RunSQL(VALORES, QUITAR),
    ]
