"""
Pruebas de integridad funcional de la aplicación.

Protegen el rediseño visual: si un cambio de plantillas rompe una ruta, un campo de formulario,
un permiso o un flujo de préstamo, alguna de estas pruebas falla.

Ejecutar con:  python manage.py test tests
Django crea una base de datos temporal (test_<nombre>) y la elimina al terminar:
la base de datos real nunca se toca.
"""
import datetime
from decimal import Decimal

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.catalogos.models import Autor, Categoria, Ejemplar, Libro
from apps.prestamos.models import ConfiguracionMulta, Devolucion, Prestamo
from apps.usuarios.models import UsuarioBiblioteca

CLAVE = 'Clave#Segura2026'


def hace(dias):
    return timezone.localdate() - datetime.timedelta(days=dias)


class BaseBiblioteca(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.tarifa = ConfiguracionMulta.objects.create(tarifa_por_dia=Decimal('500'), activa=True)
        cls.categoria = Categoria.objects.create(nombre='Literatura')
        cls.otra_categoria = Categoria.objects.create(nombre='Tecnología')
        cls.autor = Autor.objects.create(nombre='Gabriel', apellido='García Márquez')
        cls.libro = Libro.objects.create(
            isbn='978-0-0000-0001', titulo='Cien años de soledad', editorial='Sudamericana',
            anio_publicacion=1967, categoria=cls.categoria,
        )
        cls.libro.autores.add(cls.autor)
        cls.libro_sin_stock = Libro.objects.create(
            isbn='978-0-0000-0002', titulo='Manual de redes', editorial='Pearson',
            anio_publicacion=2010, categoria=cls.otra_categoria,
        )
        cls.ej1 = Ejemplar.objects.create(libro=cls.libro, codigo_barras='T-001', ubicacion='Sala A / Estante 1')
        cls.ej2 = Ejemplar.objects.create(libro=cls.libro, codigo_barras='T-002', ubicacion='Sala A / Estante 1')
        cls.ej_perdido = Ejemplar.objects.create(libro=cls.libro_sin_stock, codigo_barras='T-003',
                                                 ubicacion='Sala B', estado='perdido')
        cls.ej_libre = Ejemplar.objects.create(libro=cls.libro, codigo_barras='T-004', ubicacion='Sala A / Estante 2')

        cls.bib_user = User.objects.create_user('biblio', 'biblio@uni.edu', CLAVE,
                                                first_name='Bea', last_name='Bibliotecaria')
        cls.bib = UsuarioBiblioteca.objects.create(user=cls.bib_user, codigo_universitario='B-001',
                                                   identificacion='100', rol='bibliotecario')
        cls.lec_user = User.objects.create_user('lector', 'lector@uni.edu', CLAVE,
                                                first_name='Luis', last_name='Lector')
        cls.lec = UsuarioBiblioteca.objects.create(user=cls.lec_user, codigo_universitario='E-001',
                                                   identificacion='200', rol='estudiante',
                                                   carrera='Ingeniería de Sistemas')

    def setUp(self):
        self.c_bib = self.client_class()
        self.c_bib.force_login(self.bib_user)
        self.c_lec = self.client_class()
        self.c_lec.force_login(self.lec_user)
        self.c_anon = self.client_class()

    def prestamo(self, ejemplar=None, estado='activo', prestado_hace=5, vence_en=10, usuario=None):
        ejemplar = ejemplar or self.ej1
        datos = {}
        if estado not in ('pendiente', 'rechazado'):
            datos = {'fecha_prestamo': hace(prestado_hace), 'fecha_vencimiento': hace(-vence_en)}
            if estado in ('activo', 'vencido'):
                ejemplar.estado = 'prestado'
                ejemplar.save()
        return Prestamo.objects.create(usuario=usuario or self.lec, ejemplar=ejemplar, estado=estado, **datos)


# ---------------------------------------------------------------------------
# 1. Rutas y permisos por rol
# ---------------------------------------------------------------------------
class RutasYPermisosTest(BaseBiblioteca):

    def rutas_lector(self):
        return [
            reverse('catalogos:libro_list'),
            reverse('catalogos:libro_detail', args=[self.libro.pk]),
            reverse('catalogos:autor_list'),
            reverse('usuarios:mi_historial'),
            reverse('prestamos:prestamo_solicitar', args=[self.ej_libre.pk]),
        ]

    def rutas_bibliotecario(self):
        # El detalle de un préstamo no está aquí: el lector puede ver los suyos (ver test_lector_solo_ve_sus_propios_prestamos)
        p_pend = self.prestamo(ejemplar=self.ej2, estado='pendiente')
        p_act = self.prestamo(ejemplar=self.ej1, estado='activo')
        return [
            reverse('reportes:dashboard'),
            reverse('reportes:prestamos_activos'),
            reverse('reportes:libros_mas_prestados'),
            reverse('reportes:usuarios_mas_prestamos'),
            reverse('reportes:inventario'),
            reverse('catalogos:libro_create'),
            reverse('catalogos:libro_edit', args=[self.libro.pk]),
            reverse('catalogos:libro_delete', args=[self.libro.pk]),
            reverse('catalogos:ejemplar_create', args=[self.libro.pk]),
            reverse('catalogos:ejemplar_edit', args=[self.ej1.pk]),
            reverse('catalogos:ejemplar_delete', args=[self.ej1.pk]),
            reverse('catalogos:autor_create'),
            reverse('usuarios:usuario_list'),
            reverse('usuarios:usuario_create'),
            reverse('usuarios:usuario_detail', args=[self.lec.pk]),
            reverse('usuarios:usuario_edit', args=[self.lec.pk]),
            reverse('usuarios:usuario_delete', args=[self.lec.pk]),
            reverse('prestamos:prestamo_list'),
            reverse('prestamos:prestamo_aprobar', args=[p_pend.pk]),
            reverse('prestamos:prestamo_rechazar', args=[p_pend.pk]),
            reverse('prestamos:devolucion_registrar', args=[p_act.pk]),
            reverse('prestamos:prestamo_reportar_perdida', args=[p_act.pk]),
            reverse('prestamos:multa_config'),
        ]

    def test_login_responde(self):
        self.assertEqual(self.c_anon.get(reverse('login')).status_code, 200)

    def test_home_redirige_segun_rol(self):
        self.assertRedirects(self.c_anon.get('/'), reverse('login'), fetch_redirect_response=False)
        self.assertRedirects(self.c_bib.get('/'), reverse('reportes:dashboard'), fetch_redirect_response=False)
        self.assertRedirects(self.c_lec.get('/'), reverse('catalogos:libro_list'), fetch_redirect_response=False)

    def test_lector_accede_a_sus_rutas(self):
        for url in self.rutas_lector():
            with self.subTest(url=url):
                self.assertEqual(self.c_lec.get(url).status_code, 200)

    def test_bibliotecario_accede_a_todo(self):
        for url in self.rutas_lector() + self.rutas_bibliotecario():
            with self.subTest(url=url):
                self.assertEqual(self.c_bib.get(url).status_code, 200)

    def test_lector_no_accede_a_rutas_de_bibliotecario(self):
        for url in self.rutas_bibliotecario():
            with self.subTest(url=url):
                r = self.c_lec.get(url)
                self.assertEqual(r.status_code, 302)
                self.assertEqual(r['Location'], reverse('catalogos:libro_list'))

    def test_anonimo_es_enviado_al_login(self):
        for url in self.rutas_lector() + self.rutas_bibliotecario():
            with self.subTest(url=url):
                r = self.c_anon.get(url)
                self.assertEqual(r.status_code, 302)
                self.assertIn('/login/', r['Location'])

    def test_lector_solo_ve_sus_propios_prestamos(self):
        otro_user = User.objects.create_user('otro', 'otro@uni.edu', CLAVE)
        otro = UsuarioBiblioteca.objects.create(user=otro_user, codigo_universitario='E-999',
                                                identificacion='999', rol='estudiante')
        ajeno = self.prestamo(usuario=otro)
        propio = self.prestamo(ejemplar=self.ej2)
        self.assertEqual(self.c_lec.get(reverse('prestamos:prestamo_detail', args=[propio.pk])).status_code, 200)
        r = self.c_lec.get(reverse('prestamos:prestamo_detail', args=[ajeno.pk]))
        self.assertRedirects(r, reverse('usuarios:mi_historial'), fetch_redirect_response=False)
        self.assertEqual(self.c_bib.get(reverse('prestamos:prestamo_detail', args=[ajeno.pk])).status_code, 200)

    def test_logout(self):
        r = self.c_lec.get(reverse('logout'))
        self.assertRedirects(r, reverse('login'), fetch_redirect_response=False)


# ---------------------------------------------------------------------------
# 2. Formularios: nombres de campos y token CSRF
# ---------------------------------------------------------------------------
class FormulariosTest(BaseBiblioteca):

    def assertCampos(self, cliente, url, campos, csrf=True):
        html = cliente.get(url).content.decode()
        for campo in campos:
            self.assertIn(f'name="{campo}"', html, f'Falta el campo "{campo}" en {url}')
        if csrf:
            self.assertIn('name="csrfmiddlewaretoken"', html, f'Falta el token CSRF en {url}')

    def test_login(self):
        self.assertCampos(self.c_anon, reverse('login'), ['username', 'password'])

    def test_busqueda_del_catalogo(self):
        self.assertCampos(self.c_lec, reverse('catalogos:libro_list'), ['q', 'categoria', 'disponible'], csrf=False)

    def test_formularios_del_catalogo(self):
        self.assertCampos(self.c_bib, reverse('catalogos:libro_create'),
                          ['isbn', 'titulo', 'autores', 'editorial', 'anio_publicacion', 'categoria', 'descripcion', 'portada'])
        self.assertCampos(self.c_bib, reverse('catalogos:libro_edit', args=[self.libro.pk]),
                          ['isbn', 'titulo', 'autores', 'editorial', 'anio_publicacion', 'categoria', 'descripcion', 'portada'])
        self.assertCampos(self.c_bib, reverse('catalogos:ejemplar_create', args=[self.libro.pk]),
                          ['codigo_barras', 'ubicacion', 'estado', 'notas', 'fecha_adquisicion'])
        self.assertCampos(self.c_bib, reverse('catalogos:ejemplar_edit', args=[self.ej1.pk]),
                          ['codigo_barras', 'ubicacion', 'estado', 'notas', 'fecha_adquisicion'])
        self.assertCampos(self.c_bib, reverse('catalogos:autor_create'), ['nombre', 'apellido', 'biografia'])
        self.assertCampos(self.c_bib, reverse('catalogos:libro_delete', args=[self.libro.pk]), [])
        self.assertCampos(self.c_bib, reverse('catalogos:ejemplar_delete', args=[self.ej1.pk]), [])

    def test_formularios_de_usuarios(self):
        self.assertCampos(self.c_bib, reverse('usuarios:usuario_create'),
                          ['first_name', 'last_name', 'email', 'username', 'password', 'codigo_universitario',
                           'identificacion', 'rol', 'carrera', 'estado', 'telefono'])
        self.assertCampos(self.c_bib, reverse('usuarios:usuario_edit', args=[self.lec.pk]),
                          ['first_name', 'last_name', 'email', 'codigo_universitario', 'identificacion',
                           'rol', 'carrera', 'estado', 'telefono', 'nueva_password'])
        self.assertCampos(self.c_bib, reverse('usuarios:usuario_delete', args=[self.lec.pk]), [])

    def test_formularios_de_prestamos(self):
        p_pend = self.prestamo(ejemplar=self.ej2, estado='pendiente')
        p_act = self.prestamo(ejemplar=self.ej1, estado='activo')
        self.assertCampos(self.c_bib, reverse('prestamos:prestamo_list'), ['estado'], csrf=False)
        self.assertCampos(self.c_bib, reverse('prestamos:prestamo_aprobar', args=[p_pend.pk]), ['fecha_vencimiento'])
        self.assertCampos(self.c_bib, reverse('prestamos:prestamo_rechazar', args=[p_pend.pk]), [])
        self.assertCampos(self.c_bib, reverse('prestamos:devolucion_registrar', args=[p_act.pk]),
                          ['fecha_devolucion', 'observacion', 'detalle_observacion', 'multa_pagada'])
        self.assertCampos(self.c_bib, reverse('prestamos:prestamo_reportar_perdida', args=[p_act.pk]), [])
        self.assertCampos(self.c_bib, reverse('prestamos:multa_config'), ['tarifa_por_dia'])

    def test_solicitud_del_lector(self):
        self.assertCampos(self.c_lec, reverse('prestamos:prestamo_solicitar', args=[self.ej1.pk]), [])

    def test_filtros_de_reportes(self):
        self.assertCampos(self.c_bib, reverse('reportes:libros_mas_prestados'), ['desde', 'hasta'], csrf=False)
        self.assertCampos(self.c_bib, reverse('reportes:usuarios_mas_prestamos'), ['desde', 'hasta'], csrf=False)


# ---------------------------------------------------------------------------
# 3. Flujo completo de préstamos, devoluciones, pérdidas y multas
# ---------------------------------------------------------------------------
class FlujoPrestamosTest(BaseBiblioteca):

    def test_solicitar_crea_prestamo_pendiente(self):
        r = self.c_lec.post(reverse('prestamos:prestamo_solicitar', args=[self.ej1.pk]), follow=True)
        self.assertContains(r, 'Solicitud de préstamo enviada')
        p = Prestamo.objects.get(usuario=self.lec, ejemplar=self.ej1)
        self.assertEqual(p.estado, 'pendiente')

    def test_no_se_solicita_dos_veces_el_mismo_ejemplar(self):
        self.prestamo(estado='pendiente')
        r = self.c_lec.post(reverse('prestamos:prestamo_solicitar', args=[self.ej1.pk]), follow=True)
        self.assertContains(r, 'Ya tienes una solicitud')
        self.assertEqual(Prestamo.objects.filter(usuario=self.lec, ejemplar=self.ej1).count(), 1)

    def test_usuario_bloqueado_no_puede_solicitar(self):
        self.lec.estado = 'bloqueado'
        self.lec.save()
        r = self.c_lec.post(reverse('prestamos:prestamo_solicitar', args=[self.ej1.pk]), follow=True)
        self.assertContains(r, 'Tu cuenta está bloqueada')
        self.assertFalse(Prestamo.objects.exists())

    def test_ejemplar_no_disponible_no_se_solicita(self):
        r = self.c_lec.post(reverse('prestamos:prestamo_solicitar', args=[self.ej_perdido.pk]), follow=True)
        self.assertContains(r, 'no está disponible')
        self.assertFalse(Prestamo.objects.exists())

    def test_aprobar_con_fecha_elegida(self):
        p = self.prestamo(estado='pendiente')
        vence = hace(-20)
        r = self.c_bib.post(reverse('prestamos:prestamo_aprobar', args=[p.pk]), {'fecha_vencimiento': vence.isoformat()}, follow=True)
        self.assertContains(r, 'aprobado')
        p.refresh_from_db()
        self.ej1.refresh_from_db()
        self.assertEqual((p.estado, p.fecha_prestamo, p.fecha_vencimiento, p.aprobado_por),
                         ('activo', timezone.localdate(), vence, self.bib))
        self.assertEqual(self.ej1.estado, 'prestado')

    def test_aprobar_valida_fechas(self):
        p = self.prestamo(estado='pendiente')
        for fecha, error in [(hace(0), 'posterior a hoy'), (hace(-61), 'no puede superar 60')]:
            with self.subTest(fecha=fecha):
                r = self.c_bib.post(reverse('prestamos:prestamo_aprobar', args=[p.pk]), {'fecha_vencimiento': fecha.isoformat()})
                self.assertContains(r, error)
                p.refresh_from_db()
                self.assertEqual(p.estado, 'pendiente')

    def test_no_se_aprueba_a_usuario_bloqueado(self):
        p = self.prestamo(estado='pendiente')
        self.lec.estado = 'bloqueado'
        self.lec.save()
        r = self.c_bib.post(reverse('prestamos:prestamo_aprobar', args=[p.pk]), {'fecha_vencimiento': hace(-10).isoformat()}, follow=True)
        self.assertContains(r, 'está bloqueado')
        p.refresh_from_db()
        self.assertEqual(p.estado, 'pendiente')

    def test_rechazar(self):
        p = self.prestamo(estado='pendiente')
        r = self.c_bib.post(reverse('prestamos:prestamo_rechazar', args=[p.pk]), follow=True)
        self.assertContains(r, 'rechazado')
        p.refresh_from_db()
        self.assertEqual(p.estado, 'rechazado')

    def test_devolucion_a_tiempo_libera_ejemplar_sin_multa(self):
        p = self.prestamo(vence_en=5)
        r = self.c_bib.post(reverse('prestamos:devolucion_registrar', args=[p.pk]),
                            {'fecha_devolucion': timezone.localdate().isoformat(), 'observacion': 'bueno'}, follow=True)
        self.assertContains(r, 'Devolución registrada sin multa')
        p.refresh_from_db()
        self.ej1.refresh_from_db()
        self.assertEqual((p.estado, self.ej1.estado, p.devolucion.monto_multa), ('devuelto', 'disponible', 0))

    def test_devolucion_tardia_y_danada(self):
        p = self.prestamo(prestado_hace=20, vence_en=-3)  # venció hace 3 días
        r = self.c_bib.post(reverse('prestamos:devolucion_registrar', args=[p.pk]),
                            {'fecha_devolucion': timezone.localdate().isoformat(), 'observacion': 'danado'}, follow=True)
        self.assertContains(r, 'quedó en mantenimiento')
        p.refresh_from_db()
        self.ej1.refresh_from_db()
        self.assertEqual(p.devolucion.monto_multa, Decimal('1500.00'))
        self.assertEqual((p.estado, self.ej1.estado), ('devuelto', 'mantenimiento'))

    def test_formulario_de_devolucion_no_ofrece_perdida(self):
        p = self.prestamo()
        r = self.c_bib.get(reverse('prestamos:devolucion_registrar', args=[p.pk]))
        self.assertNotContains(r, 'value="perdido"')

    def test_reportar_perdida_con_mora(self):
        p = self.prestamo(prestado_hace=20, vence_en=-4)
        r = self.c_bib.post(reverse('prestamos:prestamo_reportar_perdida', args=[p.pk]), follow=True)
        self.assertContains(r, 'cerrado por pérdida')
        p.refresh_from_db()
        self.ej1.refresh_from_db()
        self.assertEqual((p.estado, self.ej1.estado), ('perdido', 'perdido'))
        self.assertEqual(p.devolucion.monto_multa, Decimal('2000.00'))
        self.assertEqual(p.devolucion.observacion, 'perdido')

    def test_no_se_devuelve_ni_se_pierde_un_prestamo_cerrado(self):
        p = self.prestamo(estado='devuelto')
        self.assertEqual(self.c_bib.get(reverse('prestamos:devolucion_registrar', args=[p.pk])).status_code, 404)
        self.assertEqual(self.c_bib.post(reverse('prestamos:prestamo_reportar_perdida', args=[p.pk])).status_code, 404)

    def test_vencidos_se_actualizan_al_abrir_pantallas(self):
        for url in [reverse('reportes:dashboard'), reverse('prestamos:prestamo_list'), reverse('usuarios:mi_historial')]:
            with self.subTest(url=url):
                Prestamo.objects.all().delete()
                p = self.prestamo(prestado_hace=20, vence_en=-1)
                cliente = self.c_lec if 'historial' in url else self.c_bib
                cliente.get(url)
                p.refresh_from_db()
                self.assertEqual(p.estado, 'vencido')

    def test_cambio_de_tarifa_no_altera_multas_anteriores(self):
        p1 = self.prestamo(prestado_hace=20, vence_en=-2)
        d1 = Devolucion.objects.create(prestamo=p1, fecha_devolucion=timezone.localdate())
        self.assertEqual(d1.monto_multa, Decimal('1000.00'))
        r = self.c_bib.post(reverse('prestamos:multa_config'), {'tarifa_por_dia': '800'}, follow=True)
        self.assertContains(r, 'Nueva tarifa de multa')
        self.assertEqual(ConfiguracionMulta.tarifa_vigente(), Decimal('800'))
        self.assertEqual(ConfiguracionMulta.objects.filter(activa=True).count(), 1)
        p2 = self.prestamo(ejemplar=self.ej2, prestado_hace=20, vence_en=-2)
        d2 = Devolucion.objects.create(prestamo=p2, fecha_devolucion=timezone.localdate())
        d1.refresh_from_db()
        self.assertEqual((d1.monto_multa, d2.monto_multa), (Decimal('1000.00'), Decimal('1600.00')))

    def test_tarifa_invalida(self):
        for valor in ['0', '-5', 'abc']:
            with self.subTest(valor=valor):
                r = self.c_bib.post(reverse('prestamos:multa_config'), {'tarifa_por_dia': valor})
                self.assertEqual(r.status_code, 200)
                self.assertEqual(ConfiguracionMulta.objects.count(), 1)


# ---------------------------------------------------------------------------
# 4. Catálogo: CRUD, búsquedas y restricciones de integridad
# ---------------------------------------------------------------------------
class CatalogoTest(BaseBiblioteca):

    def test_busquedas(self):
        url = reverse('catalogos:libro_list')
        casos = [
            ({'q': 'Cien'}, True, False),                       # título
            ({'q': 'García'}, True, False),                     # autor
            ({'q': '978-0-0000-0002'}, False, True),            # ISBN
            ({'categoria': self.otra_categoria.pk}, False, True),
            ({'disponible': '1'}, True, False),                 # el otro libro solo tiene un ejemplar perdido
        ]
        for params, ve_cien, ve_manual in casos:
            with self.subTest(params=params):
                libros = list(self.c_lec.get(url, params).context['libros'])
                self.assertEqual(self.libro in libros, ve_cien)
                self.assertEqual(self.libro_sin_stock in libros, ve_manual)

    def test_crud_libro(self):
        r = self.c_bib.post(reverse('catalogos:libro_create'), {
            'isbn': '978-9-9999-9999', 'titulo': 'Libro nuevo', 'autores': [self.autor.pk],
            'editorial': 'Ed', 'anio_publicacion': 2020, 'categoria': self.categoria.pk,
        })
        nuevo = Libro.objects.get(isbn='978-9-9999-9999')
        self.assertRedirects(r, reverse('catalogos:libro_detail', args=[nuevo.pk]), fetch_redirect_response=False)
        self.c_bib.post(reverse('catalogos:libro_edit', args=[nuevo.pk]), {
            'isbn': nuevo.isbn, 'titulo': 'Libro editado', 'autores': [self.autor.pk],
            'editorial': 'Ed', 'anio_publicacion': 2021,
        })
        nuevo.refresh_from_db()
        self.assertEqual((nuevo.titulo, nuevo.anio_publicacion), ('Libro editado', 2021))
        self.c_bib.post(reverse('catalogos:libro_delete', args=[nuevo.pk]))
        self.assertFalse(Libro.objects.filter(pk=nuevo.pk).exists())

    def test_crud_ejemplar(self):
        self.c_bib.post(reverse('catalogos:ejemplar_create', args=[self.libro.pk]),
                        {'codigo_barras': 'T-NUEVO', 'ubicacion': 'Sala C', 'estado': 'disponible'})
        ej = Ejemplar.objects.get(codigo_barras='T-NUEVO')
        self.c_bib.post(reverse('catalogos:ejemplar_edit', args=[ej.pk]),
                        {'codigo_barras': 'T-NUEVO', 'ubicacion': 'Sala D', 'estado': 'mantenimiento'})
        ej.refresh_from_db()
        self.assertEqual((ej.ubicacion, ej.estado), ('Sala D', 'mantenimiento'))
        self.c_bib.post(reverse('catalogos:ejemplar_delete', args=[ej.pk]))
        self.assertFalse(Ejemplar.objects.filter(pk=ej.pk).exists())

    def test_crear_autor(self):
        r = self.c_bib.post(reverse('catalogos:autor_create'), {'nombre': 'Isabel', 'apellido': 'Allende'}, follow=True)
        self.assertContains(r, 'Autor creado')
        self.assertContains(r, 'Allende')

    def test_no_se_borra_lo_que_tiene_prestamos(self):
        self.prestamo(estado='devuelto')
        r = self.c_bib.post(reverse('catalogos:libro_delete', args=[self.libro.pk]), follow=True)
        self.assertContains(r, 'No se puede eliminar')
        r = self.c_bib.post(reverse('catalogos:ejemplar_delete', args=[self.ej1.pk]), follow=True)
        self.assertContains(r, 'No se puede eliminar')
        self.assertTrue(Libro.objects.filter(pk=self.libro.pk).exists())
        self.assertTrue(Ejemplar.objects.filter(pk=self.ej1.pk).exists())


# ---------------------------------------------------------------------------
# 5. Usuarios: CRUD, validaciones y protecciones
# ---------------------------------------------------------------------------
class UsuariosTest(BaseBiblioteca):

    def datos_nuevo(self, **cambios):
        datos = {'first_name': 'Ana', 'last_name': 'Prueba', 'email': 'ana@uni.edu', 'username': 'ana',
                 'password': CLAVE, 'codigo_universitario': 'E-NUEVO', 'identificacion': '300',
                 'rol': 'estudiante', 'carrera': '', 'estado': 'bloqueado', 'telefono': ''}
        datos.update(cambios)
        return datos

    def datos_edicion(self, perfil, **cambios):
        datos = {'first_name': perfil.user.first_name, 'last_name': perfil.user.last_name,
                 'email': perfil.user.email, 'codigo_universitario': perfil.codigo_universitario,
                 'identificacion': perfil.identificacion, 'rol': perfil.rol, 'carrera': perfil.carrera,
                 'estado': perfil.estado, 'telefono': perfil.telefono, 'nueva_password': ''}
        datos.update(cambios)
        return datos

    def test_crear_usuario_con_estado(self):
        self.c_bib.post(reverse('usuarios:usuario_create'), self.datos_nuevo())
        self.assertEqual(UsuarioBiblioteca.objects.get(codigo_universitario='E-NUEVO').estado, 'bloqueado')

    def test_crear_usuario_rechaza_duplicados_y_claves_debiles(self):
        casos = {'codigo_universitario': 'E-001', 'identificacion': '200', 'email': 'LECTOR@uni.edu',
                 'username': 'lector', 'password': '123'}
        for campo, valor in casos.items():
            with self.subTest(campo=campo):
                r = self.c_bib.post(reverse('usuarios:usuario_create'), self.datos_nuevo(**{campo: valor}))
                self.assertEqual(r.status_code, 200)
                self.assertTrue(r.context['form'].errors.get(campo))
                self.assertFalse(User.objects.filter(username='ana').exists())

    def test_editar_nombre_correo_y_clave(self):
        self.c_bib.post(reverse('usuarios:usuario_edit', args=[self.lec.pk]),
                        self.datos_edicion(self.lec, first_name='Luis Alberto', email='nuevo@uni.edu'))
        self.lec_user.refresh_from_db()
        self.assertEqual((self.lec_user.first_name, self.lec_user.email), ('Luis Alberto', 'nuevo@uni.edu'))
        self.assertIsNotNone(authenticate(username='lector', password=CLAVE))
        self.lec.refresh_from_db()
        self.c_bib.post(reverse('usuarios:usuario_edit', args=[self.lec.pk]),
                        self.datos_edicion(self.lec, nueva_password='OtraClave#2026'))
        self.assertIsNotNone(authenticate(username='lector', password='OtraClave#2026'))
        self.assertIsNone(authenticate(username='lector', password=CLAVE))

    def test_bibliotecario_no_se_bloquea_ni_se_quita_el_rol_ni_se_elimina(self):
        for cambio, campo in [({'estado': 'bloqueado'}, 'estado'), ({'rol': 'estudiante'}, 'rol')]:
            with self.subTest(cambio=cambio):
                r = self.c_bib.post(reverse('usuarios:usuario_edit', args=[self.bib.pk]), self.datos_edicion(self.bib, **cambio))
                self.assertTrue(r.context['form'].errors.get(campo))
        r = self.c_bib.post(reverse('usuarios:usuario_delete', args=[self.bib.pk]), follow=True)
        self.assertContains(r, 'No puede eliminar su propia cuenta')
        self.bib.refresh_from_db()
        self.assertEqual((self.bib.estado, self.bib.rol), ('activo', 'bibliotecario'))

    def test_cambiar_su_propia_clave_no_cierra_sesion(self):
        self.c_bib.post(reverse('usuarios:usuario_edit', args=[self.bib.pk]),
                        self.datos_edicion(self.bib, nueva_password='NuevaClave#2026'))
        self.assertEqual(self.c_bib.get(reverse('usuarios:usuario_list')).status_code, 200)

    def test_no_se_elimina_usuario_con_prestamos(self):
        self.prestamo(estado='devuelto')
        r = self.c_bib.post(reverse('usuarios:usuario_delete', args=[self.lec.pk]), follow=True)
        self.assertContains(r, 'No se puede eliminar')
        self.assertTrue(UsuarioBiblioteca.objects.filter(pk=self.lec.pk).exists())

    def test_eliminar_usuario_sin_prestamos(self):
        self.c_bib.post(reverse('usuarios:usuario_delete', args=[self.lec.pk]))
        self.assertFalse(User.objects.filter(username='lector').exists())

    def test_historial_muestra_prestamos_del_usuario(self):
        self.prestamo(estado='devuelto')
        self.assertContains(self.c_lec.get(reverse('usuarios:mi_historial')), 'Cien años de soledad')
        self.assertContains(self.c_bib.get(reverse('usuarios:usuario_detail', args=[self.lec.pk])), 'Cien años de soledad')


# ---------------------------------------------------------------------------
# 6. Reportes
# ---------------------------------------------------------------------------
class ReportesTest(BaseBiblioteca):

    def test_libros_mas_prestados_por_periodo(self):
        self.prestamo(estado='devuelto', prestado_hace=60, vence_en=-45)
        url = reverse('reportes:libros_mas_prestados')
        self.assertNotIn(self.libro, list(self.c_bib.get(url).context['libros']))  # por defecto: 30 días
        r = self.c_bib.get(url, {'desde': hace(65).isoformat(), 'hasta': hace(55).isoformat()})
        self.assertIn(self.libro, list(r.context['libros']))

    def test_fechas_invalidas_no_rompen_los_reportes(self):
        for url in [reverse('reportes:libros_mas_prestados'), reverse('reportes:usuarios_mas_prestamos')]:
            for params in [{'desde': 'abc', 'hasta': 'xyz'}, {'desde': hace(0).isoformat(), 'hasta': hace(10).isoformat()}]:
                with self.subTest(url=url, params=params):
                    r = self.c_bib.get(url, params, follow=True)
                    self.assertEqual(r.status_code, 200)
                    self.assertContains(r, 'Se muestra el periodo por defecto')

    def test_usuarios_mas_prestamos_cuenta_solo_prestamos_reales(self):
        self.prestamo(estado='devuelto', prestado_hace=30, vence_en=-15)
        self.prestamo(ejemplar=self.ej2, estado='rechazado')
        self.prestamo(ejemplar=self.ej2, estado='pendiente')
        usuarios = list(self.c_bib.get(reverse('reportes:usuarios_mas_prestamos')).context['usuarios'])
        self.assertEqual(len(usuarios), 1)
        self.assertEqual((usuarios[0].total_prestamos, usuarios[0].total_devueltos), (1, 1))

    def test_inventario_y_dashboard(self):
        r = self.c_bib.get(reverse('reportes:inventario'))
        self.assertContains(r, 'T-003')
        r = self.c_bib.get(reverse('reportes:dashboard'))
        self.assertEqual((r.context['total_libros'], r.context['perdidos']), (2, 1))


# ---------------------------------------------------------------------------
# 7. Acceso (login)
# ---------------------------------------------------------------------------
class AccesoTest(BaseBiblioteca):

    def test_login_correcto_respeta_la_pagina_pedida(self):
        destino = reverse('usuarios:mi_historial')
        r = self.c_anon.post(reverse('login'), {'username': 'lector', 'password': CLAVE, 'next': destino})
        self.assertRedirects(r, destino, fetch_redirect_response=False)

    def test_login_sin_next_va_al_inicio(self):
        r = self.c_anon.post(reverse('login'), {'username': 'lector', 'password': CLAVE})
        self.assertRedirects(r, '/', fetch_redirect_response=False)

    def test_login_incorrecto_muestra_error_y_conserva_usuario(self):
        r = self.c_anon.post(reverse('login'), {'username': 'lector', 'password': 'equivocada'})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Usuario o contraseña incorrectos')
        self.assertContains(r, 'value="lector"')

    def test_login_lleva_el_next_de_la_url(self):
        r = self.c_anon.get(reverse('login'), {'next': '/usuarios/mi-historial/'})
        self.assertContains(r, 'name="next" value="/usuarios/mi-historial/"')
