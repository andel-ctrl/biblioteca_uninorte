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
    ('Hermano', 'Héctor'),
    ('Gerald', 'Weinberg'),
    ('Viktor', 'Frank'),
    ('Scott', 'Mescudi'),
    ('Dan', 'Brownstein'),
    ('Arturo', 'Uslar'),
    ('Marco', 'Cicerón'),
    ('Antoine', 'Saint-Clair'),
    ('Frank', 'Herbert'),
    ('Mirko', 'Popovich'),
    ('Guillermo', 'Cabrera'),
    ('José', 'Barros'),
    ('Brandon', 'Sanderson'),
    ('Laura', 'Restrepo'),
    ('Carl', 'Sagan'),
    ('Bobby', 'Drake'),
    ('Felipe', 'Peláez'),
    ('Jane', 'Goodall'),
    ('Eiichiro', 'Oda'),
    ('Miles', 'Coltrane'),
    ('Charles', 'Taze'),
    ('Karl', 'Marxell'),
]
autores = []
for nombre, apellido in autores_data:
    autor, created = Autor.objects.get_or_create(nombre=nombre, apellido=apellido)
    autores.append(autor)

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
        'portada': 'portadas/programar.jpg',
        'ejemplares': [('CB-003', 'Sala B / Estante 2')],
    },
    {
        'isbn': '978-0-13-235088-4',
        'titulo': 'La biblia: el reciente testamento',
        'editorial': 'Church Editorial',
        'anio': 2008,
        'categoria': 'Historia',
        'autores': [autores[2]],
        'portada': 'portadas/biblia.jpg',
        'ejemplares': [('CB-004', 'Sala B / Estante 3'), ('CB-005', 'Sala B / Estante 3')],
    },
    {
        'isbn': '978-0-13-468599-1',
        'titulo': 'La pasión de Baldor',
        'editorial': 'Santillana',
        'anio': 2011,
        'categoria': 'Literatura',
        'autores': [autores[3]],
        'portada': 'portadas/baldor.jpg',
        'ejemplares': [('CB-006', 'Sala B / Estante 4')],
    },
    {
        'isbn': '978-958-04-1120-1',
        'titulo': 'Yuropari',
        'editorial': 'Editorial Amazonia',
        'anio': 1995,
        'categoria': 'Literatura',
        'autores': [autores[5]],
        'ejemplares': [('CB-007', 'Sala A / Estante 2')],
    },
    {
        'isbn': '978-84-344-0231-5',
        'titulo': 'Tomas y Gerald: Analisis profundo de relaciones interpesonales',
        'editorial': 'Paidós',
        'anio': 2005,
        'categoria': 'Humanidades',
        'autores': [autores[6]],
        'portada': 'portadas/tomasygerald.jpg',
        'ejemplares': [('CB-008', 'Sala C / Estante 1'), ('CB-009', 'Sala C / Estante 1')],
    },
    {
        'isbn': '978-84-254-1533-8',
        'titulo': 'El hombre en busca de opiniones',
        'editorial': 'Herder Editorial',
        'anio': 1982,
        'categoria': 'Humanidades',
        'autores': [autores[7]],
        'portada': 'portadas/opiniones.jpg',
        'ejemplares': [('CB-010', 'Sala C / Estante 2')],
    },
    {
        'isbn': '978-0-06-231609-7',
        'titulo': 'Day N Night',
        'editorial': 'HarperCollins',
        'anio': 2015,
        'categoria': 'Literatura',
        'autores': [autores[8]],
        'portada': 'portadas/dayandnight.jpg',
        'ejemplares': [('CB-011', 'Sala A / Estante 3')],
    },
    {
        'isbn': '978-84-08-05294-4',
        'titulo': 'Código De La Espriella',
        'editorial': 'Planeta',
        'anio': 2006,
        'categoria': 'Historia',
        'autores': [autores[9]],
        'portada': 'portadas/espriella.jpg',
        'ejemplares': [('CB-012', 'Sala B / Estante 1')],
    },
    {
        'isbn': '978-958-06-0341-5',
        'titulo': '12 Ponllos Peregrinos',
        'editorial': 'Norma',
        'anio': 1992,
        'categoria': 'Literatura',
        'autores': [autores[10], autores[0]],
        'portada': 'portadas/ponllos.jpg',
        'ejemplares': [('CB-013', 'Sala A / Estante 1')],
    },
    {
        'isbn': '978-84-249-1402-9',
        'titulo': '10 años de elocuencia',
        'editorial': 'Gredos',
        'anio': 1978,
        'categoria': 'Humanidades',
        'autores': [autores[11]],
        'portada': 'portadas/elocuencia.jpg',
        'ejemplares': [('CB-014', 'Sala C / Estante 3')],
    },
    {
        'isbn': '978-0-14-132104-2',
        'titulo': 'Albert el chico volador',
        'editorial': 'Puffin Books',
        'anio': 2001,
        'categoria': 'Literatura',
        'autores': [autores[12]],
        'portada': 'portadas/albert.jpg',
        'ejemplares': [('CB-015', 'Sala A / Estante 4')],
    },
    {
        'isbn': '978-84-9759-682-4',
        'titulo': 'Perdidos en la arena',
        'editorial': 'Debolsillo',
        'anio': 1984,
        'categoria': 'Literatura',
        'autores': [autores[13]],
        'portada': 'portadas/arena.jpg',
        'ejemplares': [('CB-016', 'Sala A / Estante 4')],
    },
    {
        'isbn': '978-84-339-0820-9',
        'titulo': 'El Diario de Mirko',
        'editorial': 'Anagrama',
        'anio': 1999,
        'categoria': 'Historia',
        'autores': [autores[14]],
        'portada': 'portadas/mirko.jpg',
        'ejemplares': [('CB-017', 'Sala B / Estante 2')],
    },
    {
        'isbn': '978-958-8883-05-2',
        'titulo': 'Joselo y sus vagancias',
        'editorial': 'Caribe Editores',
        'anio': 2014,
        'categoria': 'Literatura',
        'autores': [autores[15]],
        'portada': 'portadas/joselo.jpg',
        'ejemplares': [('CB-018', 'Sala A / Estante 5')],
    },
    {
        'isbn': '978-958-9045-12-3',
        'titulo': 'Lo que se llevo Jefferson',
        'editorial': 'Editorial La Mojana',
        'anio': 1987,
        'categoria': 'Historia',
        'autores': [autores[16]],
        'portada': 'portadas/jefferson.jpg',
        'ejemplares': [('CB-019', 'Sala B / Estante 3')],
    },
    {
        'isbn': '978-84-666-5881-2',
        'titulo': 'Los secretos de la universidad del Monte',
        'editorial': 'Nova',
        'anio': 2018,
        'categoria': 'Literatura',
        'autores': [autores[17]],
        'portada': 'portadas/monte.jpg',
        'ejemplares': [('CB-021', 'Sala A / Estante 6'), ('CB-022', 'Sala A / Estante 6')],
    },
    {
        'isbn': '978-958-5446-21-2',
        'titulo': 'Las aventuras del pollo Sammy',
        'editorial': 'Alfaguara',
        'anio': 2016,
        'categoria': 'Literatura',
        'autores': [autores[18], autores[4]],
        'portada': 'portadas/sammy.jpg',
        'ejemplares': [('CB-023', 'Sala A / Estante 7')],
    },
    {
        'isbn': '978-84-253-5100-6',
        'titulo': '¿Y donde estan las monas?',
        'editorial': 'Crítica',
        'anio': 1997,
        'categoria': 'Ciencias',
        'autores': [autores[19]],
        'portada': 'portadas/monas.jpg',
        'ejemplares': [('CB-024', 'Sala D / Estante 1')],
    },
    {
        'isbn': '978-1-302-90123-4',
        'titulo': 'Iceman el chico caliente',
        'editorial': 'Marvel Press',
        'anio': 2017,
        'categoria': 'Literatura',
        'autores': [autores[20]],
        'portada': 'portadas/iceman.jpg',
        'ejemplares': [('CB-025', 'Sala A / Estante 8')],
    },
    {
        'isbn': '978-958-42-8811-0',
        'titulo': '2 veces Pipe',
        'editorial': 'Intermedio Editores',
        'anio': 2020,
        'categoria': 'Literatura',
        'portada': 'portadas/pipe.jpg',
        'autores': [autores[21]],
        'ejemplares': [('CB-026', 'Sala C / Estante 4')],
    },
    {
        'isbn': '978-84-9988-341-1',
        'titulo': 'El Mono que pudo volar',
        'editorial': 'Kairós',
        'anio': 2009,
        'categoria': 'Ciencias',
        'autores': [autores[22]],
        'portada': 'portadas/mono.jpg',
        'ejemplares': [('CB-027', 'Sala D / Estante 2')],
    },
    {
        'isbn': '978-1-4215-3625-5',
        'titulo': 'En camino al One Piece',
        'editorial': 'Shueisha Jump Comics',
        'anio': 2003,
        'categoria': 'Literatura',
        'autores': [autores[23]],
        'portada': 'portadas/onepiece.jpg',
        'ejemplares': [('CB-028', 'Sala A / Estante 9'), ('CB-029', 'Sala A / Estante 9')],
    },
    {
        'isbn': '978-84-92669-12-7',
        'titulo': 'La guitarra saxofonista',
        'editorial': 'Alba Editorial',
        'anio': 1991,
        'categoria': 'Literatura',
        'autores': [autores[24]],
        'portada': 'portadas/guitarra.jpg',
        'ejemplares': [('CB-030', 'Sala C / Estante 5')],
    },
    {
        'isbn': '978-0-7868-6124-9',
        'titulo': 'Sentado en el Atalaya',
        'editorial': 'Watchtower Press',
        'anio': 1989,
        'categoria': 'Historia',
        'autores': [autores[25]],
        'portada': 'portadas/atalaya.jpg',
        'ejemplares': [('CB-031', 'Sala B / Estante 4')],
    },
    {
        'isbn': '978-84-460-2187-2',
        'titulo': 'Matthew el comunista',
        'editorial': 'Akal',
        'anio': 1974,
        'categoria': 'Historia',
        'autores': [autores[26]],
        'portada': 'portadas/matthew.jpg',
        'ejemplares': [('CB-032', 'Sala B / Estante 5')],
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

admins_data = [
    {
        'username': 'admin',
        'first_name': 'Administrador',
        'last_name': 'Biblioteca',
        'email': 'admin@biblioteca.edu',
        'password': 'admin123',
        'codigo_universitario': 'ADMIN-001',
        'identificacion': '0000000001',
    },
    {
        'username': 'andel',
        'first_name': 'Angelo',
        'last_name': 'De León',
        'email': 'adeleon@biblioteca.edu',
        'password': 'andeladmin',
        'codigo_universitario': 'ADMIN-002',
        'identificacion': '1042781920',
    },
    {
        'username': 'luisangel',
        'first_name': 'Luis Angel',
        'last_name': 'Cuellar',
        'email': 'lcuellar@biblioteca.edu',
        'password': 'luisadmin',
        'codigo_universitario': 'ADMIN-003',
        'identificacion': '1043892011',
    },
    {
        'username': 'carcabria',
        'first_name': 'Carlos',
        'last_name': 'Calabria',
        'email': 'ccalabria@biblioteca.edu',
        'password': 'carbabriaadmin',
        'codigo_universitario': 'ADMIN-004',
        'identificacion': '1044903122',
    },
    {
        'username': 'dubalaguil',
        'first_name': 'Dubal',
        'last_name': 'Aguilar',
        'email': 'daguilar@biblioteca.edu',
        'password': 'dubalaguiladmin',
        'codigo_universitario': 'ADMIN-005',
        'identificacion': '1045014233',
    },
    {
        'username': 'matthewcis',
        'first_name': 'Mateo',
        'last_name': 'Cisneros',
        'email': 'mcisneros@biblioteca.edu',
        'password': 'matthewcisadmin',
        'codigo_universitario': 'ADMIN-006',
        'identificacion': '1046125344',
    },
]

for item in admins_data:
    if not User.objects.filter(username=item['username']).exists():
        admin_user = User.objects.create_superuser(
            username=item['username'],
            email=item['email'],
            password=item['password'],
            first_name=item['first_name'],
            last_name=item['last_name'],
        )
        UsuarioBiblioteca.objects.create(
            user=admin_user,
            codigo_universitario=item['codigo_universitario'],
            identificacion=item['identificacion'],
            rol='bibliotecario',
            estado='activo',
        )
        print(f"✓ Superusuario creado: {item['username']} ({item['first_name']} {item['last_name']})")
    else:
        print(f"→ Superusuario {item['username']} ya existe")

estudiantes_data = [
    {
        'username': 'pedrolector',
        'first_name': 'Pedro',
        'last_name': 'De Leon',
        'email': 'estudiante1@universidad.edu',
        'password': 'est123456',
        'codigo_universitario': 'EST-2024-001',
        'identificacion': '1234567890',
        'carrera': 'Ingeniería de Sistemas',
    },
    {
        'username': 'gatiella',
        'first_name': 'Gabriella',
        'last_name': 'Llanta',
        'email': 'gllanta@uninorte.edu.co',
        'password': 'ao3_4_eva',
        'codigo_universitario': 'EST-2024-002',
        'identificacion': '1143209841',
        'carrera': 'Diseño Gráfico',
    },
    {
        'username': 'pipe',
        'first_name': 'Andres',
        'last_name': 'Palacio',
        'email': 'apalacio@uninorte.edu.co',
        'password': 'pipeestuvoaqui',
        'codigo_universitario': 'EST-2024-003',
        'identificacion': '1143310952',
        'carrera': 'Ingeniería Mecánica',
    },
    {
        'username': 'mrsluis',
        'first_name': 'Luis',
        'last_name': 'Cortéz',
        'email': 'lcortez@uninorte.edu.co',
        'password': 'daynnite',
        'codigo_universitario': 'EST-2024-004',
        'identificacion': '1143421063',
        'carrera': 'Música',
    },
    {
        'username': 'mihovil',
        'first_name': 'Mirko',
        'last_name': 'Notengopila',
        'email': 'mnotengopila@uninorte.edu.co',
        'password': 'eldering',
        'codigo_universitario': 'EST-2024-005',
        'identificacion': '1143532174',
        'carrera': 'Ingeniería Eléctrica',
    },
    {
        'username': 'ponllo09',
        'first_name': 'Rafael',
        'last_name': 'Llantos',
        'email': 'rllantos@uninorte.edu.co',
        'password': 'ponllo09',
        'codigo_universitario': 'EST-2024-006',
        'identificacion': '1143643285',
        'carrera': 'Ciencia Política',
    },
]

for item in estudiantes_data:
    if not User.objects.filter(username=item['username']).exists():
        est_user = User.objects.create_user(
            username=item['username'],
            email=item['email'],
            password=item['password'],
            first_name=item['first_name'],
            last_name=item['last_name'],
        )
        UsuarioBiblioteca.objects.create(
            user=est_user,
            codigo_universitario=item['codigo_universitario'],
            identificacion=item['identificacion'],
            rol='estudiante',
            carrera=item['carrera'],
            estado='activo',
        )
        print(f"✓ Estudiante creado: {item['username']} ({item['first_name']} {item['last_name']})")
    else:
        print(f"→ Estudiante {item['username']} ya existe")

