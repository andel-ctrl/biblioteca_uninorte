# Scripts SQL · Laboratorio 01

| Archivo | Qué hace |
|---|---|
| `01_creacion_tablas.sql` | Crea todas las tablas con sus llaves primarias y foráneas, UNIQUE, CHECK y reglas `ON DELETE`. |
| `02_datos_basicos.sql` | Carga los datos para que la app funcione (tarifa, categorías, 27 autores, 26 libros, 31 ejemplares, 12 usuarios: 6 lectores y 6 bibliotecarios) y, al final, préstamos de demostración opcionales con sus devoluciones y multas. |
| `03_consultas.sql` | Consultas de los 4 reportes, consultas de apoyo, consultas de la especialización de usuarios y operaciones de ejemplo (INSERT, UPDATE, DELETE y restricciones en acción, que se deshacen al final). |

## Tablas del modelo

| Tabla | Qué guarda |
|---|---|
| `usuario` | Supertipo: lo que comparten todos los usuarios. `tipo` (lector o bibliotecario) es el discriminador. |
| `lector` | Subtipo: estudiantes y docentes (`rol`), con su carrera. Son los únicos que piden préstamos. |
| `bibliotecario` | Subtipo: personal que aprueba préstamos, registra devoluciones y cobra multas, con su `turno` (opcional). |
| `categoria`, `autor`, `libro`, `libro_autor` | Catálogo. Un libro tiene una categoría y uno o varios autores. |
| `ejemplar` | Copia física de un libro, con `sala`, `estante` y estado. |
| `prestamo` | Un lector pide un ejemplar; un bibliotecario lo aprueba. |
| `devolucion` | Cierre de un préstamo (0 o 1 por préstamo). |
| `multa` | Solo si la devolución fue tardía (0 o 1 por devolución), con la tarifa aplicada y el pago. |
| `tarifa_multa` | Valor por día de retraso, con historial. |
| `auth_user` | Cuenta de acceso de Django: usuario, contraseña cifrada, nombres y correo. |

La especialización es **total y disjunta**: todo usuario está en `lector` o en `bibliotecario`, nunca en ambos ni en ninguno.

- **Disjunta**: la garantiza la base. Cada subtipo guarda su `tipo` fijo y su llave foránea apunta al par `(id, tipo)` del usuario, así un usuario solo cabe en el subtipo de su tipo, y su tipo no puede cambiar mientras tenga fila en un subtipo.
- **Total**: la garantiza la aplicación, que crea el usuario y su subtipo en una sola transacción. La consulta 12 del script 3 lo verifica (debe devolver 0 filas).

## Cómo ejecutarlos

Sobre una base de datos **vacía**, en este orden:

```bash
createdb -U postgres biblioteca_db
psql -U postgres -d biblioteca_db -v ON_ERROR_STOP=1 -f sql/01_creacion_tablas.sql
psql -U postgres -d biblioteca_db -v ON_ERROR_STOP=1 -f sql/02_datos_basicos.sql
psql -U postgres -d biblioteca_db -f sql/03_consultas.sql
```

En pgAdmin: abrir cada archivo en el Query Tool de la base y ejecutarlo (F5).

Después de los scripts 01 y 02 la aplicación funciona directamente con `python manage.py runserver`, sin `migrate`: el script 02 registra las migraciones como aplicadas.

## Equivalencia con la aplicación

La base creada con estos scripts tiene las mismas tablas, las mismas 113 columnas, las mismas 79 restricciones (llaves primarias, foráneas, UNIQUE y CHECK), los mismos nombres y los mismos valores por defecto que crea `python manage.py migrate`. Las diferencias son intencionales:

- Todas las llaves foráneas declaran su regla `ON DELETE` (`CASCADE`, `RESTRICT`, `SET NULL`). En la base de `migrate` solo la tienen las dos llaves compuestas de los subtipos; las demás las crea Django, que aplica esa regla desde Python.
- No se crean los índices adicionales que agrega Django para acelerar búsquedas. No cambian ningún resultado; solo la velocidad con tablas muy grandes.

Los nombres de las llaves primarias, foráneas y UNIQUE siguen la convención de PostgreSQL (`usuario_pkey`, `prestamo_lector_id_fkey`, `libro_isbn_key`) en las dos bases: la migración `prestamos/0005` los deja así en una base creada con `migrate`, y la `prestamos/0006` le pone los mismos `DEFAULT` que este script, para que los INSERT escritos a mano funcionen igual en ambas.

Las contraseñas de los usuarios de prueba están listadas al inicio de `02_datos_basicos.sql`.
