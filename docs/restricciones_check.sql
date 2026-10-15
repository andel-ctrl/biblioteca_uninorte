-- Restricciones CHECK y extensión unaccent agregadas en la auditoría funcional (15/10/2026).
-- Generado con: python manage.py sqlmigrate <app> <migración>. Agregar al script de creación de tablas.

--
-- Create constraint ejemplar_estado_valido on model ejemplar
--
ALTER TABLE "catalogos_ejemplar" ADD CONSTRAINT "ejemplar_estado_valido" CHECK ("estado" IN ('disponible', 'prestado', 'perdido', 'mantenimiento'));
--
-- Create constraint libro_anio_publicacion_valido on model libro
--
ALTER TABLE "catalogos_libro" ADD CONSTRAINT "libro_anio_publicacion_valido" CHECK (("anio_publicacion" >= 1000 AND "anio_publicacion" <= 2100));

--
-- Extensión unaccent (búsqueda sin tildes)
--
CREATE EXTENSION IF NOT EXISTS unaccent;

--
-- Create constraint usuario_rol_valido on model usuariobiblioteca
--
ALTER TABLE "usuarios_usuariobiblioteca" ADD CONSTRAINT "usuario_rol_valido" CHECK ("rol" IN ('estudiante', 'docente', 'bibliotecario'));
--
-- Create constraint usuario_estado_valido on model usuariobiblioteca
--
ALTER TABLE "usuarios_usuariobiblioteca" ADD CONSTRAINT "usuario_estado_valido" CHECK ("estado" IN ('activo', 'bloqueado'));

--
-- Create constraint tarifa_multa_positiva on model configuracionmulta
--
ALTER TABLE "prestamos_configuracionmulta" ADD CONSTRAINT "tarifa_multa_positiva" CHECK ("tarifa_por_dia" > 0);
--
-- Create constraint devolucion_multa_no_negativa on model devolucion
--
ALTER TABLE "prestamos_devolucion" ADD CONSTRAINT "devolucion_multa_no_negativa" CHECK ("monto_multa" >= 0);
--
-- Create constraint prestamo_estado_valido on model prestamo
--
ALTER TABLE "prestamos_prestamo" ADD CONSTRAINT "prestamo_estado_valido" CHECK ("estado" IN ('pendiente', 'activo', 'vencido', 'devuelto', 'rechazado', 'perdido'));
--
-- Create constraint prestamo_vencimiento_posterior on model prestamo
--
ALTER TABLE "prestamos_prestamo" ADD CONSTRAINT "prestamo_vencimiento_posterior" CHECK (("fecha_prestamo" IS NULL OR "fecha_vencimiento" IS NULL OR "fecha_vencimiento" >= ("fecha_prestamo")));
--
-- Create constraint prestamo_aprobado_con_fechas on model prestamo
--
ALTER TABLE "prestamos_prestamo" ADD CONSTRAINT "prestamo_aprobado_con_fechas" CHECK (("estado" IN ('pendiente', 'rechazado') OR ("fecha_prestamo" IS NOT NULL AND "fecha_vencimiento" IS NOT NULL)));

