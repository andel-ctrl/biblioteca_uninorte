import django
import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from apps.catalogos.models import Autor, Categoria, Libro, Ejemplar
from apps.usuarios.models import UsuarioBiblioteca
from apps.prestamos.models import ConfiguracionMulta
import datetime

print("=== Cargando datos iniciales ===")

# 1. Config de la mulTA
multa, created = ConfiguracionMulta.objects.get_or_create(
    activa=True,
    defaults={'tarifa_por_dia': 500.00, 'vigencia_desde': datetime.date.today()}
)
print(f"{'✓' if created else '→'} Configuración de multa: $500/día")

# 2. Categorías
categorias_data = ['Ciencias', 'Humanidades', 'Tecnología', 'Literatura', 'Historia', 'Matemáticas', 'Derecho', 'Medicina']
categorias = {}
for nombre in categorias_data:
    cat, created = Categoria.objects.get_or_create(nombre=nombre)
    categorias[nombre] = cat
    print(f"{'✓' if created else '→'} Categoría: {nombre}")

# 3. Autores
autores_data = [
    ('Gabriel', 'García Márquez'),
    ('Donald', 'Knuth'),
    ('Robert', 'Martin'),
    ('Andrew', 'Tanenbaum'),
    ('Isabel', 'Allende'),
]
autores = []
for nombre, apellido in autores_data:
    autor, created = Autor.objects.get_or_create(nombre=nombre, apellido=apellido)
    autores.append(autor)
    print(f"{'✓' if created else '→'} Autor: {apellido}, {nombre}")

# <. Libros y los ejempalers
libros_data = [
    {
        'isbn': '978-0-385-47348-3',
        'titulo': 'Doscientos años de soledad',
        'editorial': 'Editorial Sudamericana',
        'anio': 1967,
        'categoria': 'Literatura',
        'autores': [autores[0]],
        'portada': 'portadas/doscientos.jpg',
        'ejemplares': [('CB-001', 'Sala A / Estante 1'), ('CB-002', 'Sala A / Estante 1')],
    },
    {
        'isbn': '978-0-201-83595-3',
        'titulo': 'Como programar para gente que no sabe programar',
        'editorial': 'Addison-Wesley',
        'anio': 1968,
        'categoria': 'Tecnología',
        'autores': [autores[1]],
        'ejemplares': [('CB-003', 'Sala B / Estante 2')],
    },
    {
        'isbn': '978-0-13-235088-4',
        'titulo': 'La biblia: el reciente testamento',
        'editorial': 'Church Editorial',
        'anio': 2008,
        'categoria': 'Historia',
        'autores': [autores[2]],
        'ejemplares': [('CB-004', 'Sala B / Estante 3'), ('CB-005', 'Sala B / Estante 3')],
    },
    {
        'isbn': '978-0-13-468599-1',
        'titulo': 'La pasión de Baldor',
        'editorial': 'Santillana',
        'anio': 2011,
        'categoria': 'Literatura',
        'autores': [autores[3]],
        'ejemplares': [('CB-006', 'Sala B / Estante 4')],
    },
]

for data in libros_data:
    defaults = {
        'titulo': data['titulo'],
        'editorial': data['editorial'],
        'anio_publicacion': data['anio'],
        'categoria': categorias[data['categoria']],
    }
    if 'portada' in data:
        defaults['portada'] = data['portada']

    libro, created = Libro.objects.get_or_create(
        isbn=data['isbn'],
        defaults=defaults
    )
    if not created and 'portada' in data and not libro.portada:
        libro.portada = data['portada']
        libro.save()

    if created:
        libro.autores.set(data['autores'])
        for codigo, ubicacion in data['ejemplares']:
            Ejemplar.objects.create(libro=libro, codigo_barras=codigo, ubicacion=ubicacion)
    print(f"{'✓' if created else '→'} Libro: {data['titulo']}")

# ── 5. Superusuario Admin ─────────────────────────────────────────────────────
if not User.objects.filter(username='admin').exists():
    admin_user = User.objects.create_superuser(
        username='admin',
        email='admin@biblioteca.edu',
        password='admin123',
        first_name='Administrador',
        last_name='Biblioteca',
    )
    UsuarioBiblioteca.objects.create(
        user=admin_user,
        codigo_universitario='ADMIN-001',
        identificacion='0000000001',
        rol='bibliotecario',
        estado='activo',
    )
    print("✓ Superusuario admin creado (usuario: admin / contraseña: admin123)")
else:
    print("→ Superusuario admin ya existe")

# ── 6. Usuario estudiante de prueba ──────────────────────────────────────────
if not User.objects.filter(username='estudiante1').exists():
    est_user = User.objects.create_user(
        username='pedrolector',
        email='estudiante1@universidad.edu',
        password='est123456',
        first_name='Pedro',
        last_name='De Leon',
    )
    UsuarioBiblioteca.objects.create(
        user=est_user,
        codigo_universitario='EST-2024-001',
        identificacion='1234567890',
        rol='estudiante',
        carrera='Ingeniería de Sistemas',
        estado='activo',
    )
    print("✓ Estudiante de prueba creado (usuario: pedrolector / contraseña: est123456)")
else:
    print("→ Estudiante de prueba ya existe")

print("\n=== ¡Datos iniciales cargados exitosamente! ===")
print("Accede al sistema con:")
print("  Admin/Bibliotecario: admin / admin123")
print("  Estudiante de prueba: pedrolector< / est123456")
