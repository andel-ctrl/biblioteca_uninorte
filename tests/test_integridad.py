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
from apps.prestamos.models import Devolucion, Multa, Prestamo, TarifaMulta
from apps.usuarios.models import Bibliotecario, Lector, Usuario

CLAVE = 'Clave#Segura2026'


def hace(dias):
    return timezone.localdate() - datetime.timedelta(days=dias)


def crear_lector(user, codigo, identificacion, rol='estudiante', carrera=''):
    """Usuario (supertipo) + su fila en lector. Devuelve el Usuario."""
    perfil = Usuario.objects.create(user=user, codigo_universitario=codigo, identificacion=identificacion, tipo='lector')
    Lector.objects.create(usuario=perfil, rol=rol, carrera=carrera)
    return perfil


def crear_bibliotecario(user, codigo, identificacion):
    """Usuario (supertipo) + su fila en bibliotecario. Devuelve el Usuario."""
    perfil = Usuario.objects.create(user=user, codigo_universitario=codigo, identificacion=identificacion, tipo='bibliotecario')
    Bibliotecario.objects.create(usuario=perfil)
    return perfil


class BaseBiblioteca(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.tarifa = TarifaMulta.objects.create(valor_dia=Decimal('500'), activa=True)
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
        cls.ej1 = Ejemplar.objects.create(libro=cls.libro, codigo_barras='T-001', sala='A', estante='1')
        cls.ej2 = Ejemplar.objects.create(libro=cls.libro, codigo_barras='T-002', sala='A', estante='1')
        cls.ej_perdido = Ejemplar.objects.create(libro=cls.libro_sin_stock, codigo_barras='T-003',
                                                 sala='B', estante='1', estado='perdido')
        cls.ej_libre = Ejemplar.objects.create(libro=cls.libro, codigo_barras='T-004', sala='A', estante='2')

        cls.bib_user = User.objects.create_user('biblio', 'biblio@uni.edu', CLAVE,
                                                first_name='Bea', last_name='Bibliotecaria')
        cls.bib = crear_bibliotecario(cls.bib_user, 'B-001', '100')
        cls.lec_user = User.objects.create_user('lector', 'lector@uni.edu', CLAVE,
                                                first_name='Luis', last_name='Lector')
        cls.lec = crear_lector(cls.lec_user, 'E-001', '200', carrera='Ingeniería de Sistemas')

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
        return Prestamo.objects.create(lector=(usuario or self.lec).lector, ejemplar=ejemplar, estado=estado, **datos)


# ---------------------------------------------------------------------------
# 1. Rutas y permisos por rol
# ---------------------------------------------------------------------------
class RutasYPermisosTest(BaseBiblioteca):

    def rutas_lector(self):
        return [
            reverse('catalogos:inicio'),
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
        self.assertRedirects(self.c_lec.get('/'), reverse('catalogos:inicio'), fetch_redirect_response=False)

    def test_lector_accede_a_sus_rutas(self):
        for url in self.rutas_lector():
            with self.subTest(url=url):
                self.assertEqual(self.c_lec.get(url).status_code, 200)

    def rutas_solo_lector(self):
        # Pedir libros y ver «mis préstamos» es propio del lector (especialización disjunta)
        return [reverse('usuarios:mi_historial'), reverse('prestamos:prestamo_solicitar', args=[self.ej_libre.pk])]

    def test_bibliotecario_accede_a_todo_menos_lo_del_lector(self):
        solo_lector = self.rutas_solo_lector()
        for url in [u for u in self.rutas_lector() if u not in solo_lector] + self.rutas_bibliotecario():
            with self.subTest(url=url):
                self.assertEqual(self.c_bib.get(url).status_code, 200)
        for url in solo_lector:
            with self.subTest(url=url):
                self.assertEqual(self.c_bib.get(url).status_code, 302)

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
        otro = crear_lector(otro_user, 'E-999', '999')
        ajeno = self.prestamo(usuario=otro)
        propio = self.prestamo(ejemplar=self.ej2)
        self.assertEqual(self.c_lec.get(reverse('prestamos:prestamo_detail', args=[propio.pk])).status_code, 200)
        r = self.c_lec.get(reverse('prestamos:prestamo_detail', args=[ajeno.pk]))
        self.assertRedirects(r, reverse('usuarios:mi_historial'), fetch_redirect_response=False)
        self.assertEqual(self.c_bib.get(reverse('prestamos:prestamo_detail', args=[ajeno.pk])).status_code, 200)

    def test_logout(self):
        r = self.c_lec.post(reverse('logout'))
        self.assertRedirects(r, reverse('login'), fetch_redirect_response=False)
        self.assertNotIn('_auth_user_id', self.c_lec.session)

    def test_logout_por_get_no_cierra_sesion(self):
        # Un enlace o una imagen de otra página no deben poder cerrar la sesión
        self.c_lec.get(reverse('logout'))
        self.assertIn('_auth_user_id', self.c_lec.session)


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
                          ['codigo_barras', 'sala', 'estante', 'estado', 'notas', 'fecha_adquisicion'])
        self.assertCampos(self.c_bib, reverse('catalogos:ejemplar_edit', args=[self.ej1.pk]),
                          ['codigo_barras', 'sala', 'estante', 'estado', 'notas', 'fecha_adquisicion'])
        self.assertCampos(self.c_bib, reverse('catalogos:autor_create'), ['nombre', 'apellido', 'biografia'])
        self.assertCampos(self.c_bib, reverse('catalogos:libro_delete', args=[self.libro.pk]), [])
        self.assertCampos(self.c_bib, reverse('catalogos:ejemplar_delete', args=[self.ej1.pk]), [])

    def test_formularios_de_usuarios(self):
        self.assertCampos(self.c_bib, reverse('usuarios:usuario_create'),
                          ['first_name', 'last_name', 'email', 'username', 'password', 'codigo_universitario',
                           'identificacion', 'rol', 'carrera', 'turno', 'estado', 'telefono'])
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
        # a tiempo: sin casilla de pago (no puede haber multa); con retraso: con casilla
        self.assertCampos(self.c_bib, reverse('prestamos:devolucion_registrar', args=[p_act.pk]),
                          ['fecha_devolucion', 'observacion', 'detalle_observacion'])
        p_tarde = self.prestamo(ejemplar=self.ej_libre, prestado_hace=20, vence_en=-2)
        self.assertCampos(self.c_bib, reverse('prestamos:devolucion_registrar', args=[p_tarde.pk]),
                          ['fecha_devolucion', 'observacion', 'detalle_observacion', 'multa_pagada'])
        self.assertCampos(self.c_bib, reverse('prestamos:prestamo_reportar_perdida', args=[p_act.pk]), [])
        self.assertCampos(self.c_bib, reverse('prestamos:multa_config'), ['valor_dia'])

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
        p = Prestamo.objects.get(lector=self.lec.lector, ejemplar=self.ej1)
        self.assertEqual(p.estado, 'pendiente')

    def test_no_se_solicita_dos_veces_el_mismo_ejemplar(self):
        self.prestamo(estado='pendiente')
        r = self.c_lec.post(reverse('prestamos:prestamo_solicitar', args=[self.ej1.pk]), follow=True)
        self.assertContains(r, 'Ya tienes una solicitud')
        self.assertEqual(Prestamo.objects.filter(lector=self.lec.lector, ejemplar=self.ej1).count(), 1)

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
                         ('activo', timezone.localdate(), vence, self.bib.bibliotecario))
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
        r = self.c_bib.post(reverse('prestamos:multa_config'), {'valor_dia': '800'}, follow=True)
        self.assertContains(r, 'Nueva tarifa de multa')
        self.assertEqual(TarifaMulta.valor_vigente(), Decimal('800'))
        self.assertEqual(TarifaMulta.objects.filter(activa=True).count(), 1)
        p2 = self.prestamo(ejemplar=self.ej2, prestado_hace=20, vence_en=-2)
        d2 = Devolucion.objects.create(prestamo=p2, fecha_devolucion=timezone.localdate())
        d1.refresh_from_db()
        self.assertEqual((d1.monto_multa, d2.monto_multa), (Decimal('1000.00'), Decimal('1600.00')))

    def test_tarifa_invalida(self):
        for valor in ['0', '-5', 'abc']:
            with self.subTest(valor=valor):
                r = self.c_bib.post(reverse('prestamos:multa_config'), {'valor_dia': valor})
                self.assertEqual(r.status_code, 200)
                self.assertEqual(TarifaMulta.objects.count(), 1)


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
                        {'codigo_barras': 'T-NUEVO', 'sala': 'C', 'estante': '1', 'estado': 'disponible'})
        ej = Ejemplar.objects.get(codigo_barras='T-NUEVO')
        self.c_bib.post(reverse('catalogos:ejemplar_edit', args=[ej.pk]),
                        {'codigo_barras': 'T-NUEVO', 'sala': 'D', 'estante': '4', 'estado': 'mantenimiento'})
        ej.refresh_from_db()
        self.assertEqual((ej.sala, ej.estante, ej.estado), ('D', '4', 'mantenimiento'))
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
        self.assertEqual(Usuario.objects.get(codigo_universitario='E-NUEVO').estado, 'bloqueado')

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
        # Al editar a un bibliotecario no se ofrecen rol ni estado; si llegan en el envío, se ignoran
        form = self.c_bib.get(reverse('usuarios:usuario_edit', args=[self.bib.pk])).context['form']
        self.assertNotIn('rol', form.fields)
        self.assertNotIn('estado', form.fields)
        self.c_bib.post(reverse('usuarios:usuario_edit', args=[self.bib.pk]),
                        self.datos_edicion(self.bib, estado='bloqueado', rol='estudiante'))
        r = self.c_bib.post(reverse('usuarios:usuario_delete', args=[self.bib.pk]), follow=True)
        self.assertContains(r, 'No puedes eliminar tu propia cuenta')
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
        self.assertTrue(Usuario.objects.filter(pk=self.lec.pk).exists())

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


# ---------------------------------------------------------------------------
# 8. Inicio del lector y catálogo completo (paginación, orden, filtros)
# ---------------------------------------------------------------------------
class InicioYCatalogoTest(BaseBiblioteca):

    def crear_libros(self, n):
        for i in range(n):
            Libro.objects.create(isbn=f'979-{i:04d}', titulo=f'Zeta {i:02d}', editorial='Ed',
                                 anio_publicacion=1990 + i, categoria=self.categoria)

    def test_inicio_muestra_saludo_y_estado_real(self):
        self.prestamo(ejemplar=self.ej1, prestado_hace=20, vence_en=-3)   # vencido
        self.prestamo(ejemplar=self.ej2, estado='pendiente')
        Prestamo.actualizar_vencidos()
        r = self.c_lec.get(reverse('catalogos:inicio'))
        self.assertContains(r, 'Hola, <em>Luis</em>')
        estado = r.context['estado']
        self.assertEqual((len(estado['vencidos']), len(estado['pendientes']), len(estado['activos'])), (1, 1, 0))
        self.assertEqual(estado['mora_total'], Decimal('1500'))
        self.assertContains(r, 'action="' + reverse('catalogos:libro_list') + '"')  # la búsqueda va al catálogo real

    def test_inicio_multas_pendientes(self):
        p = self.prestamo(prestado_hace=20, vence_en=-2)
        Devolucion.objects.create(prestamo=p, fecha_devolucion=timezone.localdate())
        r = self.c_lec.get(reverse('catalogos:inicio'))
        self.assertEqual(r.context['estado']['multas_total'], Decimal('1000.00'))

    def test_novedades_por_fecha_real_de_ingreso(self):
        self.crear_libros(3)
        Libro.objects.filter(titulo='Zeta 00').update(creado_en=timezone.now() + datetime.timedelta(days=1))
        novedades = self.c_lec.get(reverse('catalogos:inicio')).context['novedades']
        self.assertEqual(novedades[0].titulo, 'Zeta 00')
        self.assertLessEqual(len(novedades), 5)

    def test_inicio_limita_la_seleccion(self):
        self.crear_libros(30)
        r = self.c_lec.get(reverse('catalogos:inicio'))
        self.assertLessEqual(len(r.context['seleccion']), 20)
        self.assertEqual(r.context['total_titulos'], 32)

    def test_paginacion_conserva_filtros(self):
        self.crear_libros(15)
        url = reverse('catalogos:libro_list')
        r = self.c_lec.get(url, {'categoria': self.categoria.pk, 'orden': 'anio'})
        self.assertEqual(len(r.context['libros']), 12)
        html = r.content.decode()
        self.assertTrue(f'?categoria={self.categoria.pk}&amp;orden=anio&pagina=2' in html, 'el enlace a la página 2 no conserva los filtros')
        r2 = self.c_lec.get(url, {'categoria': self.categoria.pk, 'orden': 'anio', 'pagina': 2})
        self.assertEqual(len(r2.context['libros']), 4)  # 15 nuevos + 1 de la categoría

    def test_ordenamientos(self):
        self.crear_libros(3)
        url = reverse('catalogos:libro_list')
        anios = [l.anio_publicacion for l in self.c_lec.get(url, {'orden': 'anio'}).context['libros']]
        self.assertEqual(anios, sorted(anios, reverse=True))
        titulos = [l.titulo for l in self.c_lec.get(url, {'orden': 'titulo'}).context['libros']]
        self.assertEqual(titulos, sorted(titulos))

    def test_parametros_invalidos_no_rompen_el_catalogo(self):
        url = reverse('catalogos:libro_list')
        for params in [{'categoria': 'abc'}, {'orden': 'inexistente'}, {'pagina': '999'}, {'pagina': 'x'}]:
            with self.subTest(params=params):
                self.assertEqual(self.c_lec.get(url, params).status_code, 200)

    def test_disponibilidad_anotada(self):
        libros = {l.pk: l for l in self.c_lec.get(reverse('catalogos:libro_list')).context['libros']}
        self.assertEqual((libros[self.libro.pk].n_disponibles, libros[self.libro.pk].n_ejemplares), (3, 3))
        self.assertEqual(libros[self.libro_sin_stock.pk].n_disponibles, 0)


# ---------------------------------------------------------------------------
# 9. Mis préstamos
# ---------------------------------------------------------------------------
class MisPrestamosTest(BaseBiblioteca):

    def test_agrupa_y_calcula_el_plazo(self):
        activo = self.prestamo(ejemplar=self.ej1, prestado_hace=5, vence_en=5)     # mitad del plazo
        self.prestamo(ejemplar=self.ej2, prestado_hace=20, vence_en=-2)            # vencido
        self.prestamo(ejemplar=self.ej_libre, estado='pendiente')
        self.prestamo(ejemplar=self.ej_libre, estado='rechazado')
        r = self.c_lec.get(reverse('usuarios:mi_historial'))
        c = r.context
        self.assertEqual((len(c['en_curso']), len(c['pendientes']), len(c['historial'])), (2, 1, 1))
        fila = next(p for p in c['en_curso'] if p.pk == activo.pk)
        self.assertEqual((fila.progreso, fila.dias_restantes), (50, 5))
        self.assertContains(r, '2 días de retraso')
        self.assertContains(r, '2 en curso · 1 por aprobar · 1 en el historial')

    def test_multas_pendientes_y_pagadas(self):
        p1 = self.prestamo(ejemplar=self.ej1, prestado_hace=20, vence_en=-2)
        Devolucion.objects.create(prestamo=p1, fecha_devolucion=timezone.localdate())
        p2 = self.prestamo(ejemplar=self.ej2, prestado_hace=20, vence_en=-1)
        Devolucion(prestamo=p2, fecha_devolucion=timezone.localdate()).save(multa_pagada=True)
        r = self.c_lec.get(reverse('usuarios:mi_historial'))
        self.assertEqual(r.context['multas_pendientes_total'], Decimal('1000.00'))
        self.assertContains(r, 'Por pagar')
        self.assertContains(r, 'Pagada')

    def test_cuenta_bloqueada_se_avisa(self):
        self.lec.estado = 'bloqueado'
        self.lec.save()
        self.assertContains(self.c_lec.get(reverse('usuarios:mi_historial')), 'Tu cuenta está bloqueada')

    def test_sin_prestamos_invita_al_catalogo(self):
        self.assertContains(self.c_lec.get(reverse('usuarios:mi_historial')), 'Aún no tienes préstamos')


# ---------------------------------------------------------------------------
# 10. Mesa de trabajo del bibliotecario
# ---------------------------------------------------------------------------
class MesaDeTrabajoTest(BaseBiblioteca):

    def test_bandejas_con_datos_reales(self):
        self.prestamo(ejemplar=self.ej_libre, estado='pendiente')
        self.prestamo(ejemplar=self.ej1, prestado_hace=20, vence_en=-3)   # se volverá vencido
        self.prestamo(ejemplar=self.ej2, prestado_hace=10, vence_en=2)    # vence en 2 días
        c = self.c_bib.get(reverse('reportes:dashboard')).context
        self.assertEqual((len(c['solicitudes']), len(c['vencidos_lista']), len(c['proximos'])), (1, 1, 1))
        self.assertEqual((c['tareas'], c['atencion']), (3, 2))
        self.assertEqual(c['proximos'][0].dias_restantes, 2)
        self.assertEqual(c['inventario']['prestado'], 2)

    def test_aprobar_en_un_clic_vuelve_a_la_mesa(self):
        p = self.prestamo(ejemplar=self.ej_libre, estado='pendiente')
        mesa = reverse('reportes:dashboard')
        html = self.c_bib.get(mesa).content.decode()
        self.assertIn(f'action="{reverse("prestamos:prestamo_aprobar", args=[p.pk])}"', html)
        r = self.c_bib.post(reverse('prestamos:prestamo_aprobar', args=[p.pk]),
                            {'fecha_vencimiento': hace(-15).isoformat(), 'next': mesa})
        self.assertRedirects(r, mesa, fetch_redirect_response=False)
        p.refresh_from_db()
        self.assertEqual((p.estado, p.fecha_vencimiento), ('activo', hace(-15)))

    def test_next_externo_se_ignora(self):
        p = self.prestamo(ejemplar=self.ej_libre, estado='pendiente')
        r = self.c_bib.post(reverse('prestamos:prestamo_aprobar', args=[p.pk]),
                            {'fecha_vencimiento': hace(-15).isoformat(), 'next': 'https://sitio-externo.com/'})
        self.assertRedirects(r, reverse('prestamos:prestamo_list'), fetch_redirect_response=False)

    def test_lector_bloqueado_no_ofrece_aprobar(self):
        p = self.prestamo(ejemplar=self.ej_libre, estado='pendiente')
        self.lec.estado = 'bloqueado'
        self.lec.save()
        r = self.c_bib.get(reverse('reportes:dashboard'))
        self.assertContains(r, 'El lector está bloqueado')
        self.assertNotContains(r, f'action="{reverse("prestamos:prestamo_aprobar", args=[p.pk])}"')

    def test_actividad_reciente_mezcla_solicitudes_y_devoluciones(self):
        p = self.prestamo(prestado_hace=5, vence_en=5)
        Devolucion.objects.create(prestamo=p, fecha_devolucion=timezone.localdate())
        tipos = {e['tipo'] for e in self.c_bib.get(reverse('reportes:dashboard')).context['eventos']}
        self.assertEqual(tipos, {'solicitud', 'devolucion'})


# ---------------------------------------------------------------------------
# 11. Campos de fecha: el navegador necesita el formato AAAA-MM-DD
# ---------------------------------------------------------------------------
class CamposFechaTest(BaseBiblioteca):

    def test_devolucion_propone_la_fecha_de_hoy(self):
        p = self.prestamo()
        r = self.c_bib.get(reverse('prestamos:devolucion_registrar', args=[p.pk]))
        self.assertContains(r, f'value="{timezone.localdate().isoformat()}"')

    def test_editar_ejemplar_conserva_la_fecha_de_adquisicion(self):
        self.ej1.fecha_adquisicion = datetime.date(2024, 3, 9)
        self.ej1.save()
        r = self.c_bib.get(reverse('catalogos:ejemplar_edit', args=[self.ej1.pk]))
        self.assertContains(r, 'value="2024-03-09"')


# ---------------------------------------------------------------------------
# 12. Búsqueda de usuarios
# ---------------------------------------------------------------------------
class BusquedaUsuariosTest(BaseBiblioteca):

    def ids(self, **params):
        return {u.pk for u in self.c_bib.get(reverse('usuarios:usuario_list'), params).context['usuarios']}

    def test_busca_por_nombre_codigo_identificacion_y_correo(self):
        for q in ['Luis', 'E-001', '200', 'lector@uni']:
            with self.subTest(q=q):
                self.assertEqual(self.ids(q=q), {self.lec.pk})

    def test_filtros_de_rol_y_estado(self):
        self.assertEqual(self.ids(rol='bibliotecario'), {self.bib.pk})
        self.lec.estado = 'bloqueado'
        self.lec.save()
        self.assertEqual(self.ids(estado='bloqueado'), {self.lec.pk})
        self.assertEqual(len(self.ids(rol='inexistente')), 2)  # valor inválido: se ignora

    def test_cuenta_prestamos_en_curso(self):
        self.prestamo(ejemplar=self.ej1, prestado_hace=20, vence_en=-2)
        Prestamo.actualizar_vencidos()
        u = next(u for u in self.c_bib.get(reverse('usuarios:usuario_list')).context['usuarios'] if u.pk == self.lec.pk)
        self.assertEqual((u.n_activos, u.n_vencidos), (1, 1))


# ---------------------------------------------------------------------------
# 13. Login con sesión ya iniciada (al volver con el botón "atrás")
# ---------------------------------------------------------------------------
class LoginConSesionTest(BaseBiblioteca):

    def test_bibliotecario_con_sesion_no_ve_el_login(self):
        r = self.c_bib.get(reverse('login'))
        self.assertRedirects(r, '/', fetch_redirect_response=False)

    def test_lector_con_sesion_no_ve_el_login(self):
        r = self.c_lec.get(reverse('login'))
        self.assertRedirects(r, '/', fetch_redirect_response=False)

    def test_visitante_si_ve_el_login(self):
        self.assertEqual(self.c_anon.get(reverse('login')).status_code, 200)


# ---------------------------------------------------------------------------
# 14. Formulario del libro: autores con casillas, alta rápida de autor y editoriales sugeridas
# ---------------------------------------------------------------------------
class FormularioLibroTest(BaseBiblioteca):

    def test_autores_como_casillas_y_editoriales_sugeridas(self):
        html = self.c_bib.get(reverse('catalogos:libro_create')).content.decode()
        self.assertIn('type="checkbox" name="autores"', html)
        self.assertIn('<datalist id="editoriales-registradas">', html)
        self.assertIn('<option value="Sudamericana">', html)
        self.assertIn('list="editoriales-registradas"', html)

    def test_crear_libro_con_varios_autores(self):
        otro = Autor.objects.create(nombre='Isabel', apellido='Allende')
        self.c_bib.post(reverse('catalogos:libro_create'), {
            'isbn': '978-1-1111-1111', 'titulo': 'Dos autores', 'autores': [self.autor.pk, otro.pk],
            'editorial': 'Sudamericana', 'anio_publicacion': 2000,
        })
        self.assertEqual(set(Libro.objects.get(isbn='978-1-1111-1111').autores.values_list('pk', flat=True)), {self.autor.pk, otro.pk})

    def test_alta_rapida_de_autor(self):
        url = reverse('catalogos:autor_rapido')
        r = self.c_bib.post(url, {'nombre': 'Julio', 'apellido': 'Cortázar'})
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.json()['texto'], 'Cortázar, Julio')
        r = self.c_bib.post(url, {'nombre': 'julio', 'apellido': 'cortázar'})        # mismo autor: no se duplica
        self.assertEqual((r.status_code, r.json()['existente']), (200, True))
        self.assertEqual(Autor.objects.filter(apellido__iexact='Cortázar').count(), 1)
        r = self.c_bib.post(url, {'nombre': '', 'apellido': ''})                    # datos inválidos
        self.assertEqual(r.status_code, 400)
        self.assertIn('nombre', r.json()['errores'])

    def test_alta_rapida_solo_bibliotecario_y_solo_post(self):
        url = reverse('catalogos:autor_rapido')
        self.assertEqual(self.c_lec.post(url, {'nombre': 'X', 'apellido': 'Y'}).status_code, 302)
        self.assertEqual(self.c_bib.get(url).status_code, 405)
        self.assertFalse(Autor.objects.filter(apellido='Y').exists())


# ---------------------------------------------------------------------------
# Ampliar plazo de un préstamo activo
# ---------------------------------------------------------------------------
class AmpliarPlazoTest(BaseBiblioteca):
    def url(self, p):
        return reverse('prestamos:prestamo_ampliar', args=[p.pk])

    def test_amplia_y_deja_constancia(self):
        p = self.prestamo(prestado_hace=5, vence_en=10)
        nueva = hace(-25)
        r = self.c_bib.post(self.url(p), {'fecha_vencimiento': nueva.isoformat()}, follow=True)
        p.refresh_from_db()
        self.assertEqual(p.fecha_vencimiento, nueva)
        self.assertEqual(p.estado, 'activo')
        self.assertIn('Plazo ampliado del', p.observaciones)
        self.assertContains(r, 'Plazo ampliado')

    def test_detalle_muestra_boton_solo_si_se_puede(self):
        activo = self.prestamo(prestado_hace=5, vence_en=10)
        self.assertContains(self.c_bib.get(reverse('prestamos:prestamo_detail', args=[activo.pk])), self.url(activo))
        vencido = self.prestamo(ejemplar=self.ej2, estado='vencido', prestado_hace=20, vence_en=-3)
        self.assertNotContains(self.c_bib.get(reverse('prestamos:prestamo_detail', args=[vencido.pk])), self.url(vencido))

    def test_no_se_amplia_un_vencido(self):
        p = self.prestamo(estado='vencido', prestado_hace=20, vence_en=-3)
        antes = p.fecha_vencimiento
        r = self.c_bib.post(self.url(p), {'fecha_vencimiento': hace(-10).isoformat()}, follow=True)
        p.refresh_from_db()
        self.assertEqual(p.fecha_vencimiento, antes)
        self.assertContains(r, 'no se puede ampliar')

    def test_fechas_fuera_de_rango(self):
        p = self.prestamo(prestado_hace=5, vence_en=10)
        antes = p.fecha_vencimiento
        # antes del vencimiento actual
        r = self.c_bib.post(self.url(p), {'fecha_vencimiento': hace(-3).isoformat()})
        self.assertContains(r, 'posterior al vencimiento actual')
        # más de 60 días desde el préstamo
        r = self.c_bib.post(self.url(p), {'fecha_vencimiento': (p.fecha_prestamo + datetime.timedelta(days=61)).isoformat()})
        self.assertContains(r, 'no puede pasar de 60 días')
        p.refresh_from_db()
        self.assertEqual(p.fecha_vencimiento, antes)

    def test_al_maximo_ya_no_se_amplia(self):
        p = self.prestamo(prestado_hace=5, vence_en=10)
        p.fecha_vencimiento = p.fecha_limite_ampliacion(); p.save()
        r = self.c_bib.get(self.url(p), follow=True)
        self.assertContains(r, 'ya llegó al máximo')

    def test_lector_no_puede_ampliar(self):
        p = self.prestamo(prestado_hace=5, vence_en=10)
        antes = p.fecha_vencimiento
        self.c_lec.post(self.url(p), {'fecha_vencimiento': hace(-20).isoformat()})
        p.refresh_from_db()
        self.assertEqual(p.fecha_vencimiento, antes)


class AvisoCambiosSinGuardarTest(BaseBiblioteca):
    def test_formularios_de_edicion_llevan_el_aviso(self):
        for url in (reverse('catalogos:libro_edit', args=[self.libro.pk]), reverse('usuarios:usuario_edit', args=[self.lec.pk]),
                    reverse('catalogos:ejemplar_edit', args=[self.ej1.pk]), reverse('catalogos:autor_create')):
            self.assertContains(self.c_bib.get(url), 'data-avisar-cambios', msg_prefix=url)


# ---------------------------------------------------------------------------
# Editar y eliminar autores
# ---------------------------------------------------------------------------
class AutoresEdicionTest(BaseBiblioteca):
    def test_editar_corrige_el_nombre_en_sus_libros(self):
        r = self.c_bib.get(reverse('catalogos:autor_edit', args=[self.autor.pk]))
        self.assertContains(r, 'value="Gabriel"')  # precargado
        r = self.c_bib.post(reverse('catalogos:autor_edit', args=[self.autor.pk]),
                            {'nombre': 'Gabriel José', 'apellido': 'García Márquez', 'biografia': ''}, follow=True)
        self.assertContains(r, 'actualizado en su libro')
        self.assertContains(self.c_bib.get(reverse('catalogos:libro_detail', args=[self.libro.pk])), 'Gabriel José')

    def test_no_permite_renombrar_a_un_autor_existente(self):
        otro = Autor.objects.create(nombre='Isabel', apellido='Allende')
        r = self.c_bib.post(reverse('catalogos:autor_edit', args=[otro.pk]), {'nombre': 'gabriel', 'apellido': 'garcía márquez', 'biografia': ''})
        self.assertContains(r, 'Ya existe un autor registrado')
        otro.refresh_from_db()
        self.assertEqual(otro.nombre, 'Isabel')
        r = self.c_bib.post(reverse('catalogos:autor_create'), {'nombre': 'Gabriel', 'apellido': 'García Márquez', 'biografia': ''})
        self.assertContains(r, 'Ya existe un autor registrado')

    def test_alta_rapida_sigue_devolviendo_el_existente(self):
        r = self.c_bib.post(reverse('catalogos:autor_rapido'), {'nombre': 'gabriel', 'apellido': 'GARCÍA MÁRQUEZ'})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['id'], self.autor.pk)

    def test_eliminar_solo_sin_libros(self):
        r = self.c_bib.post(reverse('catalogos:autor_delete', args=[self.autor.pk]), follow=True)
        self.assertContains(r, 'No se puede eliminar')
        self.assertTrue(Autor.objects.filter(pk=self.autor.pk).exists())
        solo = Autor.objects.create(nombre='Sin', apellido='Libros')
        self.assertContains(self.c_bib.get(reverse('catalogos:autor_list')), reverse('catalogos:autor_delete', args=[solo.pk]))
        self.assertNotContains(self.c_bib.get(reverse('catalogos:autor_list')), reverse('catalogos:autor_delete', args=[self.autor.pk]))
        self.c_bib.post(reverse('catalogos:autor_delete', args=[solo.pk]))
        self.assertFalse(Autor.objects.filter(pk=solo.pk).exists())

    def test_lector_no_edita_ni_elimina(self):
        self.c_lec.post(reverse('catalogos:autor_edit', args=[self.autor.pk]), {'nombre': 'X', 'apellido': 'Y'})
        solo = Autor.objects.create(nombre='Sin', apellido='Libros')
        self.c_lec.post(reverse('catalogos:autor_delete', args=[solo.pk]))
        self.autor.refresh_from_db()
        self.assertEqual(self.autor.nombre, 'Gabriel')
        self.assertTrue(Autor.objects.filter(pk=solo.pk).exists())
        self.assertNotContains(self.c_lec.get(reverse('catalogos:autor_list')), 'Editar')



# ---------------------------------------------------------------------------
# Auditoría funcional: reglas que se corrigieron
# ---------------------------------------------------------------------------
class ReglasAuditoriaTest(BaseBiblioteca):
    def test_devolucion_no_acepta_fecha_futura_ni_anterior_al_prestamo(self):
        p = self.prestamo(prestado_hace=5, vence_en=10)
        url = reverse('prestamos:devolucion_registrar', args=[p.pk])
        r = self.c_bib.post(url, {'fecha_devolucion': hace(-3).isoformat(), 'observacion': ''})
        self.assertContains(r, 'no puede ser posterior a hoy')
        r = self.c_bib.post(url, {'fecha_devolucion': hace(9).isoformat(), 'observacion': ''})
        self.assertContains(r, 'no puede ser anterior al préstamo')
        p.refresh_from_db()
        self.assertEqual(p.estado, 'activo')
        self.c_bib.post(url, {'fecha_devolucion': hace(0).isoformat(), 'observacion': ''})
        p.refresh_from_db()
        self.assertEqual(p.estado, 'devuelto')

    def test_aprobar_rechaza_las_otras_solicitudes_del_ejemplar(self):
        otro_user = User.objects.create_user('otro', 'otro@uni.edu', CLAVE)
        otro = crear_lector(otro_user, 'E-777', '777')
        p1 = self.prestamo(ejemplar=self.ej_libre, estado='pendiente')
        p2 = self.prestamo(ejemplar=self.ej_libre, estado='pendiente', usuario=otro)
        r = self.c_bib.post(reverse('prestamos:prestamo_aprobar', args=[p1.pk]), {'fecha_vencimiento': hace(-15).isoformat()}, follow=True)
        p2.refresh_from_db()
        self.assertEqual(p2.estado, 'rechazado')
        self.assertIn('otra solicitud', p2.observaciones)
        self.assertContains(r, 'Se rechazaron automáticamente 1 solicitud')

    def test_aprobar_un_ejemplar_ya_prestado_falla_sin_duplicar(self):
        p1 = self.prestamo(ejemplar=self.ej_libre, estado='pendiente')
        self.ej_libre.estado = 'prestado'; self.ej_libre.save()
        with self.assertRaises(ValueError):
            p1.aprobar(self.bib.bibliotecario)
        p1.refresh_from_db()
        self.assertEqual(p1.estado, 'pendiente')

    def test_estado_del_ejemplar_no_se_cambia_a_mano_con_prestamo_en_curso(self):
        p = self.prestamo(ejemplar=self.ej1)
        url = reverse('catalogos:ejemplar_edit', args=[self.ej1.pk])
        self.c_bib.post(url, {'codigo_barras': 'T-001', 'sala': 'A', 'estante': '1', 'estado': 'disponible', 'notas': '', 'fecha_adquisicion': ''})
        self.ej1.refresh_from_db()
        self.assertEqual(self.ej1.estado, 'prestado')
        self.assertContains(self.c_bib.get(url), 'Tiene un préstamo en curso')

    def test_prestado_no_se_elige_a_mano(self):
        url = reverse('catalogos:ejemplar_edit', args=[self.ej_libre.pk])
        self.assertNotContains(self.c_bib.get(url), 'value="prestado"')
        r = self.c_bib.post(url, {'codigo_barras': 'T-004', 'sala': 'A', 'estante': '2', 'estado': 'prestado', 'notas': '', 'fecha_adquisicion': ''})
        self.ej_libre.refresh_from_db()
        self.assertEqual(self.ej_libre.estado, 'disponible')
        self.assertEqual(r.status_code, 200)  # vuelve al formulario con el error de opción inválida

    def test_registrar_pago_de_multa_despues_de_la_devolucion(self):
        p = self.prestamo(prestado_hace=20, vence_en=-4)
        self.c_bib.post(reverse('prestamos:devolucion_registrar', args=[p.pk]), {'fecha_devolucion': hace(0).isoformat(), 'observacion': ''})
        d = Devolucion.objects.get(prestamo=p)
        self.assertGreater(d.monto_multa, 0)
        self.assertFalse(d.multa_pagada)
        url = reverse('prestamos:multa_pagar', args=[p.pk])
        self.assertContains(self.c_bib.get(reverse('prestamos:prestamo_detail', args=[p.pk])), url)
        self.c_lec.post(url)                       # el lector no puede
        d.refresh_from_db(); self.assertFalse(d.multa_pagada)
        self.c_bib.get(url)                        # GET solo muestra la confirmación
        d.refresh_from_db(); self.assertFalse(d.multa_pagada)
        r = self.c_bib.post(url, follow=True)
        d.refresh_from_db(); self.assertTrue(d.multa_pagada)
        self.assertContains(r, 'Pago de $2.000 registrado')
        self.assertNotContains(self.c_lec.get(reverse('usuarios:mi_historial')), 'en multas pendientes')


# ---------------------------------------------------------------------------
# Lector al día: con vencidos o multas sin pagar no puede pedir libros
# ---------------------------------------------------------------------------
class LectorAlDiaTest(BaseBiblioteca):
    def solicitar(self, ejemplar):
        return self.c_lec.post(reverse('prestamos:prestamo_solicitar', args=[ejemplar.pk]), follow=True)

    def test_con_prestamo_vencido_no_solicita_y_la_ficha_lo_explica(self):
        self.prestamo(ejemplar=self.ej1, estado='vencido', prestado_hace=20, vence_en=-2)
        r = self.solicitar(self.ej_libre)
        self.assertContains(r, 'Tienes 1 préstamo vencido')
        self.assertFalse(Prestamo.objects.filter(ejemplar=self.ej_libre).exists())
        ficha = self.c_lec.get(reverse('catalogos:libro_detail', args=[self.libro.pk]))
        self.assertContains(ficha, 'Devuélvelo para volver a solicitar')
        self.assertNotContains(ficha, reverse('prestamos:prestamo_solicitar', args=[self.ej_libre.pk]))

    def test_activo_ya_pasado_de_fecha_cuenta_como_vencido(self):
        self.prestamo(ejemplar=self.ej1, estado='activo', prestado_hace=20, vence_en=-1)
        self.assertContains(self.solicitar(self.ej_libre), 'préstamo vencido')

    def test_con_multa_sin_pagar_no_solicita_y_al_pagar_si(self):
        p = self.prestamo(ejemplar=self.ej1, prestado_hace=20, vence_en=-4)
        self.c_bib.post(reverse('prestamos:devolucion_registrar', args=[p.pk]), {'fecha_devolucion': hace(0).isoformat(), 'observacion': ''})
        self.assertContains(self.solicitar(self.ej_libre), 'en multas sin pagar')
        self.c_bib.post(reverse('prestamos:multa_pagar', args=[p.pk]))
        self.assertContains(self.solicitar(self.ej_libre), 'Solicitud de préstamo enviada')

    def test_no_se_aprueba_ni_se_ofrece_en_la_mesa(self):
        pendiente = self.prestamo(ejemplar=self.ej_libre, estado='pendiente')
        self.prestamo(ejemplar=self.ej1, estado='vencido', prestado_hace=20, vence_en=-2)
        mesa = self.c_bib.get(reverse('reportes:dashboard'))
        self.assertContains(mesa, 'vencido sin devolver: no se puede aprobar')
        r = self.c_bib.post(reverse('prestamos:prestamo_aprobar', args=[pendiente.pk]), {'fecha_vencimiento': hace(-15).isoformat()}, follow=True)
        self.assertContains(r, 'No se puede aprobar todavía')
        pendiente.refresh_from_db()
        self.assertEqual(pendiente.estado, 'pendiente')

    def test_al_dia_puede_solicitar(self):
        self.assertContains(self.solicitar(self.ej_libre), 'Solicitud de préstamo enviada')


# ---------------------------------------------------------------------------
# Restricciones CHECK en la base de datos y búsqueda sin tildes
# ---------------------------------------------------------------------------
class RestriccionesBDTest(BaseBiblioteca):
    def rechaza(self, crear):
        from django.db import IntegrityError, transaction
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                crear()

    def test_la_bd_rechaza_datos_invalidos_aunque_se_salte_el_formulario(self):
        self.rechaza(lambda: Prestamo.objects.create(lector=self.lec.lector, ejemplar=self.ej_libre, estado='activo',
                                                     fecha_prestamo=hace(0), fecha_vencimiento=hace(5)))
        self.rechaza(lambda: Prestamo.objects.create(lector=self.lec.lector, ejemplar=self.ej_libre, estado='activo'))
        self.rechaza(lambda: Prestamo.objects.create(lector=self.lec.lector, ejemplar=self.ej_libre, estado='inventado'))
        self.rechaza(lambda: TarifaMulta.objects.create(valor_dia=Decimal('-5'), activa=False))
        self.rechaza(lambda: TarifaMulta.objects.create(valor_dia=Decimal('0'), activa=False))
        self.rechaza(lambda: Libro.objects.create(isbn='X-0', titulo='x', editorial='x', anio_publicacion=0))
        self.rechaza(lambda: Ejemplar.objects.filter(pk=self.ej1.pk).update(estado='robado'))
        self.rechaza(lambda: Lector.objects.filter(pk=self.lec.pk).update(rol='rector'))
        self.rechaza(lambda: Usuario.objects.filter(pk=self.lec.pk).update(tipo='rector'))
        p = self.prestamo(ejemplar=self.ej2, estado='devuelto', prestado_hace=10, vence_en=-1)
        d = Devolucion.objects.create(prestamo=p, fecha_devolucion=hace(0))  # save() crea la multa; se fuerza un negativo con update
        self.rechaza(lambda: Multa.objects.filter(devolucion=d).update(monto=Decimal('-100')))

    def test_formulario_muestra_el_mensaje_de_la_restriccion(self):
        r = self.c_bib.post(reverse('catalogos:libro_create'), {'isbn': '978-1', 'titulo': 'Viejo', 'editorial': 'X',
                                                                'anio_publicacion': 999, 'autores': [self.autor.pk]})
        self.assertContains(r, 'El año de publicación debe estar entre 1000 y 2100.')

    def test_buscar_sin_tildes_ni_mayusculas(self):
        for q in ('garcia', 'GARCÍA', 'García', 'marquez', 'cien anos'):
            r = self.c_lec.get(reverse('catalogos:libro_list'), {'q': q})
            self.assertContains(r, 'Cien años de soledad', msg_prefix=q)
        r = self.c_bib.get(reverse('usuarios:usuario_list'), {'q': 'BEA'})
        self.assertContains(r, 'Bibliotecaria')


# ---------------------------------------------------------------------------
# Personaje de la ficha de cuenta: al azar en cada inicio de sesión, según el rol
# ---------------------------------------------------------------------------
class PersonajeTest(BaseBiblioteca):
    def personaje(self, cliente):
        return cliente.session.get('personaje', '')

    def test_estudiante_recibe_un_estudiante_y_se_conserva_en_la_sesion(self):
        self.c_lec.get(reverse('catalogos:inicio'))
        p = self.personaje(self.c_lec)
        self.assertRegex(p, r'^img/personajes/estudiante-\d{2}\.webp$')
        self.assertContains(self.c_lec.get(reverse('catalogos:libro_list')), p)
        self.assertEqual(self.personaje(self.c_lec), p)

    def test_docente_recibe_uno_con_birrete(self):
        u = User.objects.create_user('profe', 'profe@uni.edu', CLAVE)
        crear_lector(u, 'D-1', 'D1', rol='docente')
        c = self.client_class(); c.force_login(u)
        self.assertRegex(self.personaje(c), r'^img/personajes/docente-0[1-4]\.webp$')

    def test_cambia_al_azar_entre_inicios_de_sesion(self):
        vistos = set()
        for _ in range(15):
            c = self.client_class(); c.post(reverse('login'), {'username': 'lector', 'password': CLAVE})
            vistos.add(self.personaje(c))
        self.assertGreater(len(vistos), 1)

    def test_todos_los_archivos_existen(self):
        from django.contrib.staticfiles import finders
        from apps.usuarios.personajes import PERSONAJES
        for ruta in PERSONAJES['docente'] + PERSONAJES['estudiante']:
            self.assertIsNotNone(finders.find(ruta), ruta)

    def test_bibliotecario_no_lleva_personaje(self):
        self.assertNotIn('ficha-cuenta__personaje', self.c_bib.get(reverse('reportes:dashboard')).content.decode())


# ---------------------------------------------------------------------------
# Devolución: la casilla de pago solo cuando puede haber multa
# ---------------------------------------------------------------------------
class DevolucionPagoTest(BaseBiblioteca):
    def test_a_tiempo_no_muestra_la_casilla_de_pago(self):
        p = self.prestamo(prestado_hace=3, vence_en=10)
        r = self.c_bib.get(reverse('prestamos:devolucion_registrar', args=[p.pk]))
        self.assertNotContains(r, 'name="multa_pagada"')
        self.assertContains(r, 'Entrega a tiempo')

    def test_con_retraso_si_la_muestra_y_trae_la_tarifa(self):
        p = self.prestamo(prestado_hace=20, vence_en=-3)
        r = self.c_bib.get(reverse('prestamos:devolucion_registrar', args=[p.pk]))
        self.assertContains(r, 'name="multa_pagada"')
        self.assertContains(r, 'data-tarifa="500')
        self.assertContains(r, '3 días de retraso × $500 por día')

    def test_sin_multa_nunca_queda_como_pagada(self):
        p = self.prestamo(prestado_hace=3, vence_en=10)
        self.c_bib.post(reverse('prestamos:devolucion_registrar', args=[p.pk]),
                        {'fecha_devolucion': hace(0).isoformat(), 'observacion': '', 'multa_pagada': 'on'})
        d = Devolucion.objects.get(prestamo=p)
        self.assertEqual(d.monto_multa, 0)
        self.assertFalse(d.multa_pagada)


# ---------------------------------------------------------------------------
# Especialización de usuarios: total y disjunta (lector | bibliotecario)
# ---------------------------------------------------------------------------
class EspecializacionTest(BaseBiblioteca):
    def datos_nuevo(self, n, rol, carrera=''):
        return {'first_name': 'Nuevo', 'last_name': rol, 'email': f'n{n}@uni.edu', 'username': f'nuevo{n}', 'password': CLAVE,
                'codigo_universitario': f'N-{n}', 'identificacion': f'50{n}', 'rol': rol, 'carrera': carrera,
                'estado': 'activo', 'telefono': ''}

    def assertExactamenteUnSubtipo(self):
        for u in Usuario.objects.all():
            with self.subTest(usuario=u.codigo_universitario):
                es_lector = Lector.objects.filter(pk=u.pk).exists()
                es_bib = Bibliotecario.objects.filter(pk=u.pk).exists()
                self.assertTrue(es_lector != es_bib, 'debe estar en un subtipo y solo en uno')
                self.assertEqual(u.tipo, 'lector' if es_lector else 'bibliotecario', 'el discriminador no coincide')

    def test_el_formulario_crea_cada_usuario_en_su_subtipo(self):
        for n, (rol, carrera) in enumerate([('bibliotecario', 'Se ignora'), ('docente', 'Derecho'), ('estudiante', 'Música')]):
            self.c_bib.post(reverse('usuarios:usuario_create'), self.datos_nuevo(n, rol, carrera))
        bib = Usuario.objects.get(codigo_universitario='N-0')
        docente = Usuario.objects.get(codigo_universitario='N-1')
        estudiante = Usuario.objects.get(codigo_universitario='N-2')
        self.assertEqual((bib.tipo, bib.rol), ('bibliotecario', 'bibliotecario'))
        self.assertEqual((docente.tipo, docente.lector.rol, docente.lector.carrera), ('lector', 'docente', 'Derecho'))
        self.assertEqual((estudiante.tipo, estudiante.lector.rol), ('lector', 'estudiante'))
        self.assertExactamenteUnSubtipo()

    def test_lector_cambia_de_rol_pero_no_pasa_a_bibliotecario(self):
        url = reverse('usuarios:usuario_edit', args=[self.lec.pk])
        datos = {'first_name': 'Luis', 'last_name': 'Lector', 'email': 'lector@uni.edu', 'codigo_universitario': 'E-001',
                 'identificacion': '200', 'carrera': 'Derecho', 'estado': 'activo', 'telefono': '', 'nueva_password': ''}
        self.c_bib.post(url, dict(datos, rol='docente'))
        self.lec.lector.refresh_from_db()
        self.assertEqual((self.lec.lector.rol, self.lec.lector.carrera), ('docente', 'Derecho'))
        r = self.c_bib.post(url, dict(datos, rol='bibliotecario'))
        self.assertTrue(r.context['form'].errors.get('rol'))
        self.assertFalse(Bibliotecario.objects.filter(pk=self.lec.pk).exists())
        self.assertExactamenteUnSubtipo()

    def test_bibliotecario_no_solicita_prestamos(self):
        r = self.c_bib.post(reverse('prestamos:prestamo_solicitar', args=[self.ej_libre.pk]), follow=True)
        self.assertContains(r, 'El personal bibliotecario no solicita préstamos')
        self.assertFalse(Prestamo.objects.exists())

    def test_bibliotecario_sin_mis_prestamos(self):
        r = self.c_bib.get(reverse('usuarios:mi_historial'), follow=True)
        self.assertRedirects(r, reverse('reportes:dashboard'))
        self.assertNotContains(self.c_bib.get(reverse('reportes:dashboard')), reverse('usuarios:mi_historial'))
        self.assertContains(self.c_lec.get(reverse('catalogos:inicio')), reverse('usuarios:mi_historial'))

    def test_ficha_del_bibliotecario_no_habla_de_carrera(self):
        r = self.c_bib.get(reverse('usuarios:usuario_detail', args=[self.bib.pk]))
        self.assertNotContains(r, 'Sin carrera registrada')
        self.assertContains(self.c_bib.get(reverse('usuarios:usuario_detail', args=[self.lec.pk])), 'Ingeniería de Sistemas')

    def test_filtro_de_usuarios_por_rol(self):
        u = User.objects.create_user('profe', 'profe@uni.edu', CLAVE)
        profe = crear_lector(u, 'D-1', 'D1', rol='docente')
        ids = lambda rol: {x.pk for x in self.c_bib.get(reverse('usuarios:usuario_list'), {'rol': rol}).context['usuarios']}
        self.assertEqual(ids('bibliotecario'), {self.bib.pk})
        self.assertEqual(ids('docente'), {profe.pk})
        self.assertEqual(ids('estudiante'), {self.lec.pk})

    def test_la_bd_no_deja_que_un_bibliotecario_sea_lector_de_un_prestamo(self):
        # La llave foránea prestamo.lector_id apunta a la tabla lector: un bibliotecario no está ahí
        from django.db import IntegrityError, connection, transaction
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Prestamo.objects.create(lector_id=self.bib.pk, ejemplar=self.ej_libre, estado='pendiente')
                connection.cursor().execute('SET CONSTRAINTS ALL IMMEDIATE')  # verifica ya la llave diferida
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                p = self.prestamo(estado='pendiente')
                Prestamo.objects.filter(pk=p.pk).update(aprobado_por_id=self.lec.pk)  # un lector no aprueba
                connection.cursor().execute('SET CONSTRAINTS ALL IMMEDIATE')


# ---------------------------------------------------------------------------
# Multa en su propia tabla: 0 o 1 por devolución, con la tarifa con que se calculó
# ---------------------------------------------------------------------------
class MultaTablaTest(BaseBiblioteca):
    def devolver(self, prestamo, **kwargs):
        d = Devolucion(prestamo=prestamo, fecha_devolucion=hace(0), registrado_por=self.bib.bibliotecario)
        d.save(**kwargs)
        return d

    def test_a_tiempo_no_crea_multa(self):
        d = self.devolver(self.prestamo(prestado_hace=3, vence_en=5))
        self.assertFalse(Multa.objects.filter(devolucion=d).exists())
        self.assertIsNone(d.multa_registrada)

    def test_con_retraso_crea_una_multa_con_la_tarifa_vigente(self):
        d = self.devolver(self.prestamo(prestado_hace=20, vence_en=-3))
        m = Multa.objects.get(devolucion=d)
        self.assertEqual((m.tarifa, m.dias_retraso(), m.monto), (self.tarifa, 3, Decimal('1500.00')))
        self.assertEqual((m.pagada, m.fecha_pago, m.cobrada_por), (False, None, None))

    def test_pagada_al_devolver_guarda_fecha_y_quien_cobro(self):
        d = self.devolver(self.prestamo(prestado_hace=20, vence_en=-2), multa_pagada=True)
        m = d.multa
        self.assertEqual((m.pagada, m.fecha_pago, m.cobrada_por), (True, hace(0), self.bib.bibliotecario))

    def test_pago_posterior_registra_fecha_y_bibliotecario(self):
        p = self.prestamo(prestado_hace=20, vence_en=-2)
        self.devolver(p)
        self.c_bib.post(reverse('prestamos:multa_pagar', args=[p.pk]))
        m = Multa.objects.get(devolucion__prestamo=p)
        self.assertEqual((m.pagada, m.fecha_pago, m.cobrada_por), (True, timezone.localdate(), self.bib.bibliotecario))
        r = self.c_bib.get(reverse('prestamos:prestamo_detail', args=[p.pk]))
        self.assertContains(r, 'Pagada el')
        self.assertContains(r, '2 días × $500')

    def test_cada_multa_conserva_su_tarifa(self):
        m1 = self.devolver(self.prestamo(prestado_hace=20, vence_en=-2)).multa
        self.c_bib.post(reverse('prestamos:multa_config'), {'valor_dia': '800'})
        nueva = TarifaMulta.vigente()
        m2 = self.devolver(self.prestamo(ejemplar=self.ej2, prestado_hace=20, vence_en=-2)).multa
        m1.refresh_from_db()
        self.assertEqual((m1.tarifa, m1.monto), (self.tarifa, Decimal('1000.00')))
        self.assertEqual((m2.tarifa, m2.monto), (nueva, Decimal('1600.00')))

    def test_no_se_borra_una_tarifa_ni_una_devolucion_con_multas(self):
        from django.db.models import ProtectedError
        d = self.devolver(self.prestamo(prestado_hace=20, vence_en=-2))
        with self.assertRaises(ProtectedError):
            self.tarifa.delete()
        with self.assertRaises(ProtectedError):
            d.delete()

    def test_la_bd_rechaza_multas_incoherentes(self):
        from django.db import IntegrityError, transaction
        d = self.devolver(self.prestamo(prestado_hace=20, vence_en=-2))
        casos = [{'monto': Decimal('0')},                           # una multa existe solo si hay monto
                 {'pagada': True},                                  # pagada sin fecha de pago
                 {'fecha_pago': hace(0)}]                           # pendiente con fecha de pago
        for cambio in casos:
            with self.subTest(cambio=cambio):
                with self.assertRaises(IntegrityError):
                    with transaction.atomic():
                        Multa.objects.filter(devolucion=d).update(**cambio)
        with self.assertRaises(IntegrityError):                     # una sola multa por devolución
            with transaction.atomic():
                Multa.objects.create(devolucion=d, tarifa=self.tarifa, monto=Decimal('100'))


# ---------------------------------------------------------------------------
# Ubicación del ejemplar en dos columnas: sala y estante
# ---------------------------------------------------------------------------
class UbicacionTest(BaseBiblioteca):
    def test_sala_y_estante_obligatorios_y_texto_combinado(self):
        url = reverse('catalogos:ejemplar_create', args=[self.libro.pk])
        r = self.c_bib.post(url, {'codigo_barras': 'T-SIN', 'sala': '', 'estante': '', 'estado': 'disponible'})
        self.assertTrue(r.context['form'].errors.get('sala'))
        self.assertTrue(r.context['form'].errors.get('estante'))
        self.assertFalse(Ejemplar.objects.filter(codigo_barras='T-SIN').exists())
        self.assertEqual(self.ej1.ubicacion, 'Sala A / Estante 1')
        self.assertContains(self.c_lec.get(reverse('catalogos:libro_detail', args=[self.libro.pk])), 'Sala A / Estante 1')

    def test_la_migracion_separa_el_texto_viejo(self):
        import importlib
        patron = importlib.import_module('apps.catalogos.migrations.0004_tablas_y_ubicacion').PATRON
        casos = {'Sala A / Estante 1': ('A', '1'), 'sala b/estante 12': ('b', '12'),
                 'Sala Norte / Estante 3 / Nivel 2': ('Norte', '3')}
        for texto, esperado in casos.items():
            with self.subTest(texto=texto):
                m = patron.match(texto)
                self.assertEqual((m.group('sala'), m.group('estante')), esperado)
        self.assertIsNone(patron.match('Depósito'))  # formato libre: la migración lo guarda entero en sala


# ---------------------------------------------------------------------------
# Turno: atributo propio (y opcional) del bibliotecario
# ---------------------------------------------------------------------------
class TurnoBibliotecarioTest(BaseBiblioteca):
    def datos_edicion_bib(self, **cambios):
        datos = {'first_name': 'Bea', 'last_name': 'Bibliotecaria', 'email': 'biblio@uni.edu', 'codigo_universitario': 'B-001',
                 'identificacion': '100', 'rol': 'bibliotecario', 'estado': 'activo', 'telefono': '', 'nueva_password': ''}
        datos.update(cambios)
        return datos

    def test_es_opcional(self):
        self.assertEqual(self.bib.bibliotecario.turno, '')
        self.assertEqual(self.bib.get_turno_display(), '')

    def test_crear_bibliotecario_con_turno(self):
        self.c_bib.post(reverse('usuarios:usuario_create'), {
            'first_name': 'Tomas', 'last_name': 'Noche', 'email': 'tn@uni.edu', 'username': 'tnoche', 'password': CLAVE,
            'codigo_universitario': 'B-002', 'identificacion': '101', 'rol': 'bibliotecario', 'turno': 'noche',
            'carrera': '', 'estado': 'activo', 'telefono': ''})
        nuevo = Usuario.objects.get(codigo_universitario='B-002')
        self.assertEqual((nuevo.tipo, nuevo.bibliotecario.turno), ('bibliotecario', 'noche'))

    def test_editar_turno_y_verlo_en_la_ficha_y_la_lista(self):
        self.c_bib.post(reverse('usuarios:usuario_edit', args=[self.bib.pk]), self.datos_edicion_bib(turno='tarde'))
        self.bib.bibliotecario.refresh_from_db()
        self.assertEqual(self.bib.bibliotecario.turno, 'tarde')
        self.assertContains(self.c_bib.get(reverse('usuarios:usuario_detail', args=[self.bib.pk])), 'Turno de la tarde')
        self.assertContains(self.c_bib.get(reverse('usuarios:usuario_list')), 'Turno de la tarde')

    def test_turno_invalido_se_rechaza(self):
        r = self.c_bib.post(reverse('usuarios:usuario_edit', args=[self.bib.pk]), self.datos_edicion_bib(turno='madrugada'))
        self.assertTrue(r.context['form'].errors.get('turno'))
        from django.db import IntegrityError, transaction
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Bibliotecario.objects.filter(pk=self.bib.pk).update(turno='madrugada')

    def test_el_lector_no_tiene_turno(self):
        html = self.c_bib.get(reverse('usuarios:usuario_edit', args=[self.lec.pk])).content.decode()
        self.assertNotIn('name="turno"', html)
        self.assertIn('name="carrera"', html)
        html = self.c_bib.get(reverse('usuarios:usuario_edit', args=[self.bib.pk])).content.decode()
        self.assertIn('name="turno"', html)
        self.assertNotIn('name="carrera"', html)


# ---------------------------------------------------------------------------
# La base garantiza que la especialización es disjunta y que el tipo es coherente
# (llave foránea compuesta de cada subtipo hacia el par (id, tipo) del usuario)
# ---------------------------------------------------------------------------
class SubtiposDisjuntosTest(BaseBiblioteca):
    def rechaza(self, operacion):
        from django.db import IntegrityError, connection, transaction
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                operacion()
                connection.cursor().execute('SET CONSTRAINTS ALL IMMEDIATE')  # verifica ya las llaves diferidas

    def test_un_bibliotecario_no_cabe_en_lector_ni_al_reves(self):
        self.rechaza(lambda: Lector.objects.create(usuario=self.bib, rol='estudiante'))
        self.rechaza(lambda: Bibliotecario.objects.create(usuario=self.lec))

    def test_no_se_cambia_el_tipo_de_quien_ya_esta_en_su_subtipo(self):
        self.rechaza(lambda: Usuario.objects.filter(pk=self.lec.pk).update(tipo='bibliotecario'))
        self.rechaza(lambda: Lector.objects.filter(pk=self.lec.pk).update(tipo='bibliotecario'))

    def test_el_subtipo_toma_su_tipo_solo(self):
        self.assertEqual(Lector.objects.get(pk=self.lec.pk).tipo, 'lector')
        self.assertEqual(Bibliotecario.objects.get(pk=self.bib.pk).tipo, 'bibliotecario')


# ---------------------------------------------------------------------------
# Quién es bibliotecario lo decide la tabla bibliotecario, no la marca is_staff
# ---------------------------------------------------------------------------
class AccesoSoloBibliotecarioTest(BaseBiblioteca):
    def test_lector_marcado_como_staff_no_entra_a_lo_del_personal(self):
        self.lec_user.is_staff = True
        self.lec_user.save()
        r = self.c_lec.get(reverse('reportes:dashboard'))
        self.assertRedirects(r, reverse('catalogos:libro_list'), fetch_redirect_response=False)

    def test_cuenta_sin_ficha_de_biblioteca_no_entra_aunque_sea_superusuario(self):
        jefe = User.objects.create_superuser('jefe', 'jefe@uni.edu', CLAVE)
        c = self.client_class(); c.force_login(jefe)
        self.assertEqual(c.get(reverse('usuarios:usuario_list')).status_code, 302)

    def test_el_bibliotecario_si_entra(self):
        self.assertEqual(self.c_bib.get(reverse('usuarios:usuario_list')).status_code, 200)


# ---------------------------------------------------------------------------
# Formulario de usuario: solo los campos que aplican según el rol
# ---------------------------------------------------------------------------
class FormularioUsuarioPorRolTest(BaseBiblioteca):
    def datos(self, **cambios):
        datos = {'first_name': 'Nuevo', 'last_name': 'Usuario', 'email': 'nuevo@uni.edu', 'username': 'nuevo', 'password': CLAVE,
                 'codigo_universitario': 'N-1', 'identificacion': '501', 'rol': 'estudiante', 'carrera': '', 'turno': '',
                 'estado': 'activo', 'telefono': ''}
        datos.update(cambios)
        return datos

    def test_alta_marca_los_campos_que_dependen_del_rol(self):
        html = self.c_bib.get(reverse('usuarios:usuario_create')).content.decode()
        for seccion in ('Tipo de usuario', 'Datos personales', 'En la biblioteca', 'Cuenta de acceso'):
            self.assertIn(seccion, html)
        self.assertRegex(html, r'data-solo-para="lector">\s*<div class="campo[^"]*">\s*<label[^>]*for="id_estado"')
        self.assertRegex(html, r'data-solo-para="bibliotecario">\s*<div class="campo[^"]*">\s*<label[^>]*for="id_turno"')
        self.assertRegex(html, r'data-solo-para="lector">\s*<div class="campo[^"]*">\s*<label[^>]*for="id_carrera"')
        # el rol va primero: decide qué campos aplican
        self.assertLess(html.index('name="rol"'), html.index('name="first_name"'))

    def test_bibliotecario_nuevo_siempre_activo_y_sin_carrera(self):
        self.c_bib.post(reverse('usuarios:usuario_create'), self.datos(rol='bibliotecario', estado='bloqueado',
                                                                         carrera='No aplica', turno='tarde'))
        u = Usuario.objects.get(codigo_universitario='N-1')
        self.assertEqual((u.tipo, u.estado, u.carrera, u.bibliotecario.turno), ('bibliotecario', 'activo', '', 'tarde'))

    def test_lector_nuevo_ignora_el_turno(self):
        self.c_bib.post(reverse('usuarios:usuario_create'), self.datos(rol='docente', carrera='Derecho', turno='noche',
                                                                         estado='bloqueado'))
        u = Usuario.objects.get(codigo_universitario='N-1')
        self.assertEqual((u.tipo, u.estado, u.lector.rol, u.lector.carrera), ('lector', 'bloqueado', 'docente', 'Derecho'))
        self.assertFalse(Bibliotecario.objects.filter(pk=u.pk).exists())

    def test_edicion_del_bibliotecario_muestra_el_rol_como_texto(self):
        r = self.c_bib.get(reverse('usuarios:usuario_edit', args=[self.bib.pk]))
        self.assertContains(r, 'El tipo de usuario no se cambia al editar.')
        self.assertNotContains(r, 'name="rol"')
        self.assertNotContains(r, 'name="estado"')
        self.assertContains(r, 'name="turno"')


# ---------------------------------------------------------------------------
# Autores repetidos: se detectan sin importar mayúsculas ni tildes (como el buscador)
# ---------------------------------------------------------------------------
class AutorSinTildesTest(BaseBiblioteca):
    def test_formulario_rechaza_el_mismo_autor_escrito_sin_tildes(self):
        r = self.c_bib.post(reverse('catalogos:autor_create'), {'nombre': 'GABRIEL', 'apellido': 'Garcia Marquez', 'biografia': ''})
        self.assertContains(r, 'Ya existe un autor registrado')
        self.assertEqual(Autor.objects.filter(nombre__iexact='gabriel').count(), 1)

    def test_alta_rapida_devuelve_el_existente_aunque_falten_tildes(self):
        Autor.objects.create(nombre='Julio', apellido='Cortázar')
        r = self.c_bib.post(reverse('catalogos:autor_rapido'), {'nombre': 'julio', 'apellido': 'CORTAZAR'})
        self.assertEqual((r.status_code, r.json()['existente']), (200, True))
        r = self.c_bib.post(reverse('catalogos:autor_rapido'), {'nombre': 'Ana', 'apellido': 'Núñez'})
        r2 = self.c_bib.post(reverse('catalogos:autor_rapido'), {'nombre': 'ANA', 'apellido': 'nunez'})
        self.assertEqual((r.status_code, r2.status_code, r2.json()['id']), (201, 200, r.json()['id']))

    def test_autores_distintos_siguen_siendo_distintos(self):
        r = self.c_bib.post(reverse('catalogos:autor_create'), {'nombre': 'Gabriela', 'apellido': 'García Márquez', 'biografia': ''}, follow=True)
        self.assertContains(r, 'Autor creado')
