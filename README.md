# Biblioteca Universitaria · Sistema de préstamos

Laboratorio 01 de Bases de Datos. Aplicación web para el préstamo y la devolución de libros:
catálogo de libros y ejemplares, usuarios (lectores y bibliotecarios), préstamos con aprobación,
devoluciones con multa automática por retraso y reportes.

**Tecnologías:** Python · Django · PostgreSQL · Bootstrap 5.

| Carpeta | Qué contiene |
|---|---|
| `sql/` | Scripts de la base de datos: creación de tablas, datos básicos y consultas (ver `sql/LEEME.md`) |
| `diagramas/` | MER (notación de Chen) y modelo relacional (con y sin las tablas internas de Django), en `.png` y `.drawio` |
| `apps/` | La aplicación: `catalogos`, `usuarios`, `prestamos` y `reportes` |
| `templates/`, `static/` | Pantallas, estilos, imágenes y JavaScript |
| `media/portadas/` | Portadas de los libros de prueba |
| `tests/` | Pruebas automáticas |

---

## Requisitos

| Programa | Versión | Nota |
|---|---|---|
| Python | 3.10 o superior | En Windows, marcar *Add Python to PATH* al instalarlo |
| PostgreSQL | 13 o superior | El instalador oficial trae pgAdmin y la extensión `unaccent` que usa el proyecto. Recuerda la contraseña del usuario `postgres` que pongas al instalar |
| Git | cualquiera | Solo para clonar; también sirve descargar el proyecto en `.zip` |

Las librerías de Python (Django, psycopg2, python-dotenv, whitenoise, pillow, gunicorn) se instalan
solas con `requirements.txt` en el paso 1. No hace falta instalar nada más.

---

## Correr el proyecto en local (unos 5 minutos)

### 1. Descargar el proyecto e instalar las librerías

Abre una terminal en la carpeta donde quieras dejar el proyecto:

```bash
git clone <url-del-repositorio>
cd biblioteca_uninorte
python -m venv venv
```

Activa el entorno virtual (la terminal mostrará `(venv)` al inicio):

- Windows: `venv\Scripts\activate`
- Mac o Linux: `source venv/bin/activate`

Instala las librerías:

```bash
pip install -r requirements.txt
```

En Mac o Linux, si `python` no existe, usa `python3`. En Windows también funciona `py`.

### 2. Crear la base de datos con los scripts (pgAdmin)

1. En pgAdmin: clic derecho en *Databases → Create → Database...*, nombre `biblioteca_db`, *Save*.
2. Clic derecho en `biblioteca_db` → *Query Tool*.
3. Abre `sql/01_creacion_tablas.sql` (icono de carpeta), ejecútalo con **F5** y espera el mensaje de éxito.
4. Abre `sql/02_datos_basicos.sql` y ejecútalo con **F5**.
5. (Opcional) `sql/03_consultas.sql` tiene las consultas de los reportes; se pueden ejecutar una por una.

Con los scripts **no** hay que correr `python manage.py migrate`: el script 02 deja registrada la
estructura para Django.

<details>
<summary>Alternativa: crear la base con Django en vez de los scripts</summary>

Crea la base vacía `biblioteca_db` en pgAdmin, configura el `.env` (paso 3) y ejecuta:

```bash
python manage.py migrate
python datos_iniciales.py
```

El resultado es la misma estructura y los mismos datos básicos (sin los préstamos de demostración).
</details>

### 3. Configurar la conexión a PostgreSQL (`.env`)

Copia el archivo `.env.example` y nombra la copia `.env`:

- Windows: `copy .env.example .env`
- Mac o Linux: `cp .env.example .env`

Ábrelo y escribe la contraseña de PostgreSQL en `DB_PASSWORD`:

```
DB_NAME=biblioteca_db
DB_USER=postgres
DB_PASSWORD=<la contraseña de postgres de este computador>
```

Lo demás puede quedar igual (`SECRET_KEY` vacía está bien en local).

### 4. Correr la aplicación

```bash
python manage.py runserver
```

Abre <http://127.0.0.1:8000> e inicia sesión con un usuario de prueba:

| Usuario | Contraseña | Rol | Qué puede hacer |
|---|---|---|---|
| `admin` | `admin123` | Bibliotecario | Catálogo, usuarios, aprobar préstamos, devoluciones, multas y reportes |
| `pedrolector` | `est123456` | Estudiante | Buscar libros, pedir préstamos y ver su historial |

La lista completa (6 bibliotecarios y 6 lectores) está al inicio de `sql/02_datos_basicos.sql`.

Para detener el servidor: `Ctrl + C`. Para volver a abrirlo otro día: activar el entorno (paso 1)
y `python manage.py runserver`.

### Si algo falla

| Mensaje | Solución |
|---|---|
| `password authentication failed for user "postgres"` | La contraseña de `DB_PASSWORD` en `.env` no es la de PostgreSQL de este computador |
| `database "biblioteca_db" does not exist` | Falta el paso 2.1, o la base tiene otro nombre que el de `DB_NAME` |
| `relation "..." does not exist` | No se ejecutaron los scripts 01 y 02 (paso 2) |
| `relation "..." already exists` al ejecutar el script 01 | La base no estaba vacía: bórrala, créala de nuevo y repite el paso 2 |
| `ModuleNotFoundError: No module named 'django'` | El entorno virtual no está activado (paso 1) |
| `connection refused` / `could not connect to server` | El servicio de PostgreSQL no está iniciado |

### Pruebas automáticas (opcional)

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
