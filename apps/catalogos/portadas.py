"""
Recorte automático de portadas.

Muchas imágenes de portada traen el libro fotografiado sobre un fondo liso
(blanco, gris, transparente) con márgenes y sombra. El catálogo dibuja el libro
con volumen, así que la imagen debe ser exactamente la tapa: aquí se detecta el
fondo por las esquinas y se recorta hasta el borde del libro.
"""
import os
from io import BytesIO

from django.core.files.uploadedfile import InMemoryUploadedFile
from PIL import Image, ImageChops, ImageOps

UMBRAL = 60          # diferencia mínima con el fondo para considerar que es tapa (ignora sombras suaves)
TOLERANCIA_FONDO = 24  # las cuatro esquinas deben parecerse entre sí para tratarlas como fondo
FRACCION = 0.6        # fracción de la diferencia mediana que separa tapa de sombra
AREA_MINIMA = 0.08     # no recortar si lo detectado es diminuto
RELLENO_MINIMO = 0.85  # un libro fotografiado es un bloque lleno; una ilustración sobre tapa blanca no
ALTO_MAXIMO = 1400     # las portadas más grandes se reducen; el sitio nunca las muestra mayores


def _caja_util(imagen):
    """Devuelve la caja (izq, arriba, der, abajo) de la tapa o None si no hay fondo que quitar."""
    if imagen.mode in ('RGBA', 'LA') or (imagen.mode == 'P' and 'transparency' in imagen.info):
        alfa = imagen.convert('RGBA').getchannel('A').point(lambda v: 255 if v > 40 else 0)
        return alfa.getbbox()

    rgb = imagen.convert('RGB')
    ancho, alto = rgb.size
    esquinas = [rgb.getpixel(p) for p in ((0, 0), (ancho - 1, 0), (0, alto - 1), (ancho - 1, alto - 1))]
    if max(max(abs(a - b) for a, b in zip(e, esquinas[0])) for e in esquinas) > TOLERANCIA_FONDO:
        return None  # sin fondo uniforme: la imagen ya es la tapa
    fondo = tuple(sum(c) // 4 for c in zip(*esquinas))
    diferencia = ImageChops.difference(rgb, Image.new('RGB', rgb.size, fondo)).convert('L')
    mascara = diferencia.point(lambda v: 255 if v > UMBRAL else 0)
    caja = mascara.getbbox()
    if not caja:
        return None
    # Afinar: la tapa se aparta mucho del fondo; la sombra proyectada, poco. Se conservan
    # las filas y columnas cuya diferencia media supera una fracción de la mediana
    zona = diferencia.crop(caja)
    columnas = zona.resize((zona.width, 1), Image.BOX).tobytes()
    filas = zona.resize((1, zona.height), Image.BOX).tobytes()

    def tramo(perfil):
        corte = sorted(perfil)[len(perfil) // 2] * FRACCION
        llenas = [i for i, v in enumerate(perfil) if v > corte]
        return llenas[0], llenas[-1] + 1

    (x0, x1), (y0, y1) = tramo(columnas), tramo(filas)
    return (caja[0] + x0, caja[1] + y0, caja[0] + x1, caja[1] + y1)


def _relleno(imagen, caja):
    """Fracción de la caja que se aparta del fondo (1 = bloque sólido, como la tapa de un libro)."""
    if imagen.mode in ('RGBA', 'LA') or (imagen.mode == 'P' and 'transparency' in imagen.info):
        mascara = imagen.convert('RGBA').getchannel('A').point(lambda v: 255 if v > 40 else 0)
    else:
        rgb = imagen.convert('RGB')
        fondo = rgb.getpixel((0, 0))
        mascara = ImageChops.difference(rgb, Image.new('RGB', rgb.size, fondo)).convert('L').point(lambda v: 255 if v > UMBRAL else 0)
    zona = mascara.crop(caja).resize((1, 1), Image.BOX)
    return zona.getpixel((0, 0)) / 255


def recortar_portada(archivo):
    """Recibe el archivo subido y devuelve uno nuevo con solo la tapa (o el mismo si no hay nada que hacer)."""
    try:
        imagen = ImageOps.exif_transpose(Image.open(archivo))
    except Exception:
        return archivo  # la validación de Django ya informa si no es una imagen
    ancho, alto = imagen.size
    caja = _caja_util(imagen)
    recortar = bool(caja) and caja != (0, 0, ancho, alto) and \
        (caja[2] - caja[0]) * (caja[3] - caja[1]) >= AREA_MINIMA * ancho * alto and _relleno(imagen, caja) >= RELLENO_MINIMO
    if not recortar and alto <= ALTO_MAXIMO:
        archivo.seek(0)
        return archivo

    if recortar:
        imagen = imagen.crop(caja)
    if imagen.height > ALTO_MAXIMO:
        imagen = imagen.resize((round(imagen.width * ALTO_MAXIMO / imagen.height), ALTO_MAXIMO), Image.LANCZOS)

    salida = BytesIO()
    con_alfa = imagen.mode in ('RGBA', 'LA', 'P')
    if con_alfa:
        imagen.convert('RGBA').save(salida, 'PNG', optimize=True)
        extension, tipo = '.png', 'image/png'
    else:
        imagen.convert('RGB').save(salida, 'JPEG', quality=90, optimize=True)
        extension, tipo = '.jpg', 'image/jpeg'
    nombre = os.path.splitext(os.path.basename(archivo.name))[0] + extension
    return InMemoryUploadedFile(salida, 'portada', nombre, tipo, salida.getbuffer().nbytes, None)
