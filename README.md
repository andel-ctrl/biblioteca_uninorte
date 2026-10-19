# Biblioteca Universitaria · Sistema de préstamos

Laboratorio 01 de Bases de Datos. Aplicación web para el préstamo y la devolución de libros:
catálogo de libros y ejemplares, usuarios (lectores y bibliotecarios), préstamos con aprobación,
devoluciones con multa automática por retraso y reportes.

**Tecnologías:** Python · Django · PostgreSQL · Bootstrap 5.

| Carpeta | Qué contiene |
|---|---|
| `sql/` | Scripts de la base de datos: creación de tablas, datos básicos y consultas (ver `sql/LEEME.md`) |
| `diagramas/` | MER (Chen) y modelo relacional, en `.png` y `.drawio` |
| `apps/` | La aplicación: `catalogos`, `usuarios`, `prestamos` y `reportes` |
| `templates/`, `static/` | Pantallas, estilos, imágenes y JavaScript |
| `tests/` | Pruebas automáticas |

---

## Correr el proyecto en un computador

Requisitos: **Python 3.10 o superior**, **PostgreSQL** (con pgAdmin) y Git.

### 1. Traer el proyecto e instalar

```bash
git clone <url-del-repositorio>
cd biblioteca_uninorte
python -m venv venv
```

Activar el entorno: en Windows `venv\Scripts\activate`; en Mac o Linux `source venv/bin/activate`.

```bash
pip install -r requirements.txt
```

### 2. Crear la base de datos (elige una forma)

**Forma A, con los scripts SQL (pgAdmin):**

1. En pgAdmin: clic derecho en *Databases → Create → Database...* y ponle un nombre, por ejemplo `biblioteca_db`.
2. Abre el *Query Tool* de esa base y ejecuta, en este orden, `sql/01_creacion_tablas.sql` y `sql/02_datos_basicos.sql` (F5).

Con esta forma **no** hay que correr `migrate`: el script 02 deja registrada la estructura.

**Forma B, con Django:** crea la base vacía en pgAdmin y, después de configurar el `.env` (paso 3):

```bash
python manage.py migrate
python datos_iniciales.py
```

### 3. Configurar la conexión (`.env`)

Copia `.env.example` con el nombre `.env` y completa:

```
DB_NAME=biblioteca_db
DB_PASSWORD=<la contraseña de PostgreSQL de tu computador>
```

`SECRET_KEY` puede quedar vacía en tu computador.

### 4. Correr la aplicación

```bash
python manage.py runserver
```

Abre <http://127.0.0.1:8000>. Usuarios de prueba (contraseñas completas al inicio de `sql/02_datos_basicos.sql`):

| Usuario | Contraseña | Rol |
|---|---|---|
| `admin` | `admin123` | Bibliotecario |
| `pedrolector` | `est123456` | Estudiante |

### Pruebas automáticas

```bash
python manage.py test tests
```

Django crea una base temporal para las pruebas y la borra al terminar: la base real no se toca.

---

## Publicar en internet (Render)

Render ofrece un plan gratuito para la aplicación y para PostgreSQL. Limitaciones del plan gratuito:
la aplicación se "duerme" tras 15 minutos sin visitas (la primera visita después tarda cerca de un
minuto), la base gratuita vence a los 30 días y las portadas que se suban desde la aplicación se
pierden cuando el servidor se reinicia (las del repositorio siempre se ven).

1. **Repositorio:** Render se conecta a GitHub. El repositorio debe estar en una cuenta a la que
   tengas acceso de administrador (si no, crea uno propio y sube el proyecto con
   `git remote add mio <url>` y `git push mio main`).
2. **Base de datos:** en Render, *New → Postgres*, plan *Free*. Anota de la sección *Connections*:
   *Hostname* (interno), *Port*, *Database*, *Username*, *Password* y el *External Database URL*.
3. **Estructura y datos con los scripts:** en pgAdmin registra un servidor con los datos externos
   (en la pestaña *Parameters*/*SSL* pon *SSL mode = require*), abre el *Query Tool* de esa base y
   ejecuta `sql/01_creacion_tablas.sql` y luego `sql/02_datos_basicos.sql`.
   **Haz este paso antes del siguiente.**
4. **Aplicación:** *New → Web Service*, elige el repositorio, la misma región de la base y el plan *Free*:
   - *Build Command:*
     `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate --noinput`
   - *Start Command:* `gunicorn config.wsgi:application`
   - *Environment Variables:* `DEBUG=False`, `SECRET_KEY=<una clave larga>`, `DB_NAME`, `DB_USER`,
     `DB_PASSWORD`, `DB_HOST` (el *Hostname* interno) y `DB_PORT=5432`.

   Para generar la clave: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`.
   La versión de Python la toma de `.python-version`. La dirección pública, el HTTPS y la protección
   de los formularios se configuran solos (ver `config/settings.py`).
5. Cuando el registro diga *Your service is live*, abre la dirección `https://<nombre>.onrender.com`.
   **Cambia la contraseña de `admin`** y la de los usuarios de prueba: el sitio es público.

Cada `git push` al repositorio conectado vuelve a publicar la aplicación automáticamente.
