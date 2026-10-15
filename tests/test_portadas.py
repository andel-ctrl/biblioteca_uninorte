"""Recorte automático de portadas: la imagen guardada debe ser solo la tapa."""
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase
from PIL import Image, ImageDraw

from apps.catalogos.portadas import recortar_portada


def _imagen(fondo='white', tapa=(40, 70, 50), caja=(100, 80, 500, 680), tamano=(600, 760), sombra=True, modo='RGB', formato='JPEG'):
    im = Image.new(modo, tamano, fondo)
    d = ImageDraw.Draw(im)
    if sombra:  # sombra gris suave abajo y a la derecha, como en las fotos de catálogo
        d.rectangle((caja[0] + 12, caja[1] + 12, caja[2] + 14, caja[3] + 16), fill=(205, 205, 205) if modo == 'RGB' else (0, 0, 0, 60))
    d.rectangle((caja[0], caja[1], caja[2] - 1, caja[3] - 1), fill=tapa)
    d.rectangle((caja[0] + 60, caja[1] + 60, caja[0] + 200, caja[1] + 120), fill=(220, 190, 120))  # un título claro
    salida = BytesIO()
    im.save(salida, formato)
    return SimpleUploadedFile('portada.' + formato.lower(), salida.getvalue(), content_type='image/' + formato.lower())


class RecortePortadaTests(SimpleTestCase):
    def test_quita_fondo_blanco_y_sombra(self):
        resultado = Image.open(recortar_portada(_imagen()))
        ancho, alto = resultado.size
        self.assertAlmostEqual(ancho, 400, delta=4)
        self.assertAlmostEqual(alto, 600, delta=4)

    def test_fondo_transparente_usa_canal_alfa(self):
        archivo = _imagen(fondo=(0, 0, 0, 0), tapa=(40, 70, 50, 255), modo='RGBA', formato='PNG', sombra=False)
        resultado = Image.open(recortar_portada(archivo))
        self.assertEqual(resultado.size, (400, 600))

    def test_imagen_que_ya_es_la_tapa_no_cambia(self):
        archivo = _imagen(caja=(0, 0, 600, 760), sombra=False)
        resultado = recortar_portada(archivo)
        self.assertIs(resultado, archivo)
        self.assertEqual(Image.open(resultado).size, (600, 760))

    def test_archivo_que_no_es_imagen_se_devuelve_igual(self):
        archivo = SimpleUploadedFile('x.jpg', b'no soy una imagen', content_type='image/jpeg')
        self.assertIs(recortar_portada(archivo), archivo)

    def test_libro_pequeno_en_foto_grande_tambien_se_recorta(self):
        # el libro ocupa menos de un tercio de la foto
        resultado = Image.open(recortar_portada(_imagen(caja=(150, 100, 450, 550), tamano=(600, 800))))
        self.assertAlmostEqual(resultado.width, 300, delta=4)
        self.assertAlmostEqual(resultado.height, 450, delta=4)

    def test_tapa_minimalista_blanca_no_se_recorta(self):
        # tapa blanca con una ilustración pequeña al centro: no es un libro sobre fondo, no se toca
        im = Image.new('RGB', (600, 900), 'white')
        d = ImageDraw.Draw(im)
        d.ellipse((220, 300, 380, 460), fill=(150, 30, 60))
        d.text((240, 600), 'TITULO', fill=(20, 20, 20))
        salida = BytesIO(); im.save(salida, 'JPEG')
        archivo = SimpleUploadedFile('min.jpg', salida.getvalue(), content_type='image/jpeg')
        self.assertEqual(Image.open(recortar_portada(archivo)).size, (600, 900))
