"""Nombres limpios para las restricciones, secuencias e índices de las tablas del modelo.

Al cambiar el nombre de una tabla, Django no renombra lo que cuelga de ella: la tabla «usuario»
seguía con su llave primaria «usuarios_usuariobiblioteca_pkey». Esta migración aplica la
convención de PostgreSQL, la misma de sql/01_creacion_tablas.sql:

    <tabla>_pkey               llave primaria
    <tabla>_<columnas>_key     UNIQUE
    <tabla>_<columna>_fkey     llave foránea
    <tabla>_<columna>_not_null NOT NULL (PostgreSQL 18 les da nombre)
    <tabla>_<columna>_seq      secuencia del id
    <tabla>_<columnas>_idx     índice adicional de Django (_like si es para búsquedas con LIKE)

Lee los nombres actuales de la propia base, así que sirve igual para una base migrada desde
el diseño anterior y para una nueva; lo que ya tiene el nombre correcto no se toca.
Los CHECK no se tocan: ya tienen nombres propios (salvo el que Django crea por ser entero
positivo, que también pasa a la convención). Solo cambian nombres: ningún dato ni regla.
"""
from django.db import migrations

TABLAS = ['usuario', 'lector', 'bibliotecario', 'categoria', 'autor', 'libro', 'libro_autor',
          'ejemplar', 'tarifa_multa', 'prestamo', 'devolucion', 'multa']


def renombrar(apps, schema_editor):
    if schema_editor.connection.vendor != 'postgresql':
        return
    q = schema_editor.quote_name
    with schema_editor.connection.cursor() as c:
        for tabla in TABLAS:
            # Restricciones: llave primaria, UNIQUE, llave foránea y NOT NULL
            c.execute("""
                SELECT con.conname, con.contype,
                       ARRAY(SELECT a.attname FROM unnest(con.conkey) WITH ORDINALITY k(n, i)
                             JOIN pg_attribute a ON a.attrelid = con.conrelid AND a.attnum = k.n ORDER BY k.i)
                FROM pg_constraint con
                WHERE con.conrelid = %s::regclass AND con.contype IN ('p', 'u', 'f', 'n', 'c')
            """, [tabla])
            for nombre, tipo, columnas in c.fetchall():
                if tipo == 'p':
                    nuevo = f'{tabla}_pkey'
                elif tipo == 'u':
                    nuevo = f'{tabla}_{"_".join(columnas)}_key'
                elif tipo == 'f':
                    nuevo = f'{tabla}_{columnas[0]}_fkey'
                elif tipo == 'n':
                    nuevo = f'{tabla}_{columnas[0]}_not_null'
                elif nombre.endswith('_check') and len(columnas) == 1 and nombre.endswith(f'_{columnas[0]}_check'):
                    nuevo = f'{tabla}_{columnas[0]}_check'  # el CHECK automático de Django (entero positivo)
                else:
                    continue  # CHECK con nombre propio
                if nombre != nuevo:
                    c.execute(f'ALTER TABLE {q(tabla)} RENAME CONSTRAINT {q(nombre)} TO {q(nuevo)}')

            # Secuencia del id (los subtipos no tienen: su llave es la del usuario)
            if tabla not in ('lector', 'bibliotecario'):
                c.execute("SELECT pg_get_serial_sequence(%s, 'id')", [tabla])
                secuencia = c.fetchone()[0]  # p. ej. public.usuarios_usuariobiblioteca_id_seq
                if secuencia and secuencia.split('.')[-1].strip('"') != f'{tabla}_id_seq':
                    c.execute(f'ALTER SEQUENCE {secuencia} RENAME TO {q(tabla + "_id_seq")}')

            # Índices adicionales que crea Django (no los de llaves primarias ni UNIQUE)
            c.execute("""
                SELECT i.relname, ARRAY(SELECT a.attname FROM unnest(x.indkey) WITH ORDINALITY k(n, o)
                                       JOIN pg_attribute a ON a.attrelid = x.indrelid AND a.attnum = k.n ORDER BY k.o)
                FROM pg_index x JOIN pg_class i ON i.oid = x.indexrelid
                WHERE x.indrelid = %s::regclass
                  AND NOT EXISTS (SELECT 1 FROM pg_constraint con WHERE con.conindid = x.indexrelid)
            """, [tabla])
            for nombre, columnas in c.fetchall():
                nuevo = f'{tabla}_{"_".join(columnas)}_{"like" if nombre.endswith("_like") else "idx"}'
                if nombre != nuevo:
                    c.execute(f'ALTER INDEX {q(nombre)} RENAME TO {q(nuevo)}')


class Migration(migrations.Migration):

    dependencies = [
        ('prestamos', '0004_multa_y_especializacion'),
    ]

    operations = [
        # Al revertir no hace falta volver a los nombres viejos: no cambian datos ni reglas
        migrations.RunPython(renombrar, migrations.RunPython.noop),
    ]
