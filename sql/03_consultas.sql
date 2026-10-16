-- =============================================================================
--  Sistema de préstamos de la Biblioteca Universitaria · Laboratorio 01
--  Script 3 de 3: CONSULTAS SQL
--
--  Las mismas consultas que usa la aplicación para sus reportes, escritas en SQL,
--  más consultas de apoyo y operaciones de ejemplo. Se puede ejecutar completo:
--      psql -U postgres -d biblioteca_db -f sql/03_consultas.sql
--  o copiar cada consulta en pgAdmin (Query Tool).
--
--  Con los préstamos de demostración del script 2, todas devuelven resultados.
-- =============================================================================


-- -----------------------------------------------------------------------------
--  0. Marcar como vencidos los préstamos activos cuya fecha ya pasó
--     (la aplicación lo hace sola cada vez que se abren las pantallas de préstamos)
-- -----------------------------------------------------------------------------
UPDATE prestamo
SET estado = 'vencido'
WHERE estado = 'activo' AND fecha_vencimiento < CURRENT_DATE;


-- -----------------------------------------------------------------------------
--  1. REPORTE · Préstamos activos y vencidos, con días de retraso y mora acumulada
--     Mora = días de retraso × tarifa vigente (la activa más reciente).
--     Los días de retraso no se guardan: se calculan con las fechas.
-- -----------------------------------------------------------------------------
WITH tarifa AS (
    SELECT valor_dia FROM tarifa_multa
    WHERE activa ORDER BY vigente_desde DESC, id DESC LIMIT 1
)
SELECT p.id                                              AS prestamo,
       a.first_name || ' ' || a.last_name                AS lector,
       u.codigo_universitario                            AS codigo,
       l.titulo,
       e.codigo_barras                                   AS ejemplar,
       p.fecha_prestamo,
       p.fecha_vencimiento,
       p.estado,
       GREATEST(CURRENT_DATE - p.fecha_vencimiento, 0)   AS dias_retraso,
       GREATEST(CURRENT_DATE - p.fecha_vencimiento, 0) * t.valor_dia AS mora_acumulada
FROM prestamo p
JOIN usuario u    ON u.id = p.lector_id          -- el lector tiene la misma llave que su usuario
JOIN auth_user a  ON a.id = u.user_id
JOIN ejemplar e   ON e.id = p.ejemplar_id
JOIN libro l      ON l.id = e.libro_id
CROSS JOIN tarifa t
WHERE p.estado IN ('activo', 'vencido')
ORDER BY p.fecha_vencimiento;


-- -----------------------------------------------------------------------------
--  2. REPORTE · Libros más prestados en un periodo
--     Cuenta solo préstamos que realmente salieron (con fecha de préstamo):
--     las solicitudes pendientes y rechazadas no cuentan. Cambiar las fechas del periodo.
-- -----------------------------------------------------------------------------
WITH periodo AS (SELECT CURRENT_DATE - 30 AS desde, CURRENT_DATE AS hasta)
SELECT l.titulo,
       string_agg(DISTINCT au.apellido || ', ' || au.nombre, '; ') AS autores,
       c.nombre                                                     AS categoria,
       COUNT(DISTINCT p.id)                                         AS total_prestamos
FROM libro l
JOIN ejemplar e           ON e.libro_id = l.id
JOIN prestamo p           ON p.ejemplar_id = e.id
LEFT JOIN categoria c     ON c.id = l.categoria_id
LEFT JOIN libro_autor la  ON la.libro_id = l.id
LEFT JOIN autor au        ON au.id = la.autor_id
CROSS JOIN periodo
WHERE p.fecha_prestamo IS NOT NULL
  AND p.fecha_prestamo BETWEEN periodo.desde AND periodo.hasta
GROUP BY l.id, l.titulo, c.nombre
ORDER BY total_prestamos DESC, l.titulo
LIMIT 20;


-- -----------------------------------------------------------------------------
--  3. REPORTE · Lectores con más préstamos, con el desglose por estado
--     (histórico completo; para un periodo, agregar el filtro de fecha_prestamo)
-- -----------------------------------------------------------------------------
SELECT a.first_name || ' ' || a.last_name                      AS lector,
       u.codigo_universitario                                   AS codigo,
       lec.rol,
       COUNT(p.id)                                              AS total_prestamos,
       COUNT(p.id) FILTER (WHERE p.estado = 'activo')           AS activos,
       COUNT(p.id) FILTER (WHERE p.estado = 'vencido')          AS vencidos,
       COUNT(p.id) FILTER (WHERE p.estado = 'devuelto')         AS devueltos,
       COUNT(p.id) FILTER (WHERE p.estado = 'perdido')          AS perdidos
FROM lector lec
JOIN usuario u    ON u.id = lec.usuario_id
JOIN auth_user a  ON a.id = u.user_id
JOIN prestamo p   ON p.lector_id = lec.usuario_id
WHERE p.fecha_prestamo IS NOT NULL
GROUP BY lec.usuario_id, a.first_name, a.last_name, u.codigo_universitario, lec.rol
ORDER BY total_prestamos DESC, a.last_name
LIMIT 20;


-- -----------------------------------------------------------------------------
--  4. REPORTE · Inventario por estado
-- -----------------------------------------------------------------------------
-- 4a. Resumen: cuántos ejemplares hay en cada estado
SELECT estado, COUNT(*) AS ejemplares
FROM ejemplar
GROUP BY estado
ORDER BY CASE estado WHEN 'disponible' THEN 1 WHEN 'prestado' THEN 2 WHEN 'perdido' THEN 3 ELSE 4 END;

-- 4b. Detalle: cada ejemplar con su libro y su ubicación (sala y estante)
SELECT e.estado, e.codigo_barras, l.titulo, l.editorial, l.anio_publicacion, e.sala, e.estante
FROM ejemplar e
JOIN libro l ON l.id = e.libro_id
ORDER BY e.estado, l.titulo, e.codigo_barras;


-- =============================================================================
--  CONSULTAS DE APOYO
-- =============================================================================

-- 5. Búsqueda en el catálogo por título, autor o ISBN sin importar tildes ni mayúsculas,
--    con la disponibilidad de cada libro (ejemplares disponibles de N)
SELECT l.titulo,
       string_agg(DISTINCT au.apellido || ', ' || au.nombre, '; ')    AS autores,
       COUNT(DISTINCT e.id) FILTER (WHERE e.estado = 'disponible')     AS disponibles,
       COUNT(DISTINCT e.id)                                            AS ejemplares
FROM libro l
LEFT JOIN libro_autor la ON la.libro_id = l.id
LEFT JOIN autor au       ON au.id = la.autor_id
LEFT JOIN ejemplar e     ON e.libro_id = l.id
WHERE l.id IN (
    SELECT l2.id
    FROM libro l2
    LEFT JOIN libro_autor la2 ON la2.libro_id = l2.id
    LEFT JOIN autor au2       ON au2.id = la2.autor_id
    WHERE unaccent(l2.titulo)    ILIKE unaccent('%garcia%')
       OR unaccent(au2.nombre)   ILIKE unaccent('%garcia%')
       OR unaccent(au2.apellido) ILIKE unaccent('%garcia%')
       OR l2.isbn ILIKE '%garcia%'
)
GROUP BY l.id, l.titulo
ORDER BY l.titulo;

-- 6. Libros por categoría con su disponibilidad
SELECT COALESCE(c.nombre, 'Sin categoría')                          AS categoria,
       COUNT(DISTINCT l.id)                                          AS titulos,
       COUNT(e.id)                                                   AS ejemplares,
       COUNT(e.id) FILTER (WHERE e.estado = 'disponible')            AS disponibles
FROM libro l
LEFT JOIN categoria c ON c.id = l.categoria_id
LEFT JOIN ejemplar e  ON e.libro_id = l.id
GROUP BY c.nombre
ORDER BY categoria;

-- 7. Historial de préstamos de un lector, con su multa si la hubo (cambiar el nombre de usuario)
SELECT p.id AS prestamo, l.titulo, e.codigo_barras AS ejemplar, p.fecha_solicitud::date AS solicitado,
       p.fecha_prestamo, p.fecha_vencimiento, p.estado,
       d.fecha_devolucion, d.observacion,
       COALESCE(m.monto, 0) AS multa, m.pagada
FROM prestamo p
JOIN usuario u          ON u.id = p.lector_id
JOIN auth_user a        ON a.id = u.user_id
JOIN ejemplar e         ON e.id = p.ejemplar_id
JOIN libro l            ON l.id = e.libro_id
LEFT JOIN devolucion d  ON d.prestamo_id = p.id
LEFT JOIN multa m       ON m.devolucion_id = d.id
WHERE a.username = 'pedrolector'
ORDER BY p.fecha_solicitud DESC;

-- 8. Multas pendientes de pago por lector
SELECT a.first_name || ' ' || a.last_name AS lector, u.codigo_universitario AS codigo,
       COUNT(*) AS multas, SUM(m.monto) AS total_por_pagar
FROM multa m
JOIN devolucion d  ON d.id = m.devolucion_id
JOIN prestamo p    ON p.id = d.prestamo_id
JOIN usuario u     ON u.id = p.lector_id
JOIN auth_user a   ON a.id = u.user_id
WHERE NOT m.pagada
GROUP BY u.id, a.first_name, a.last_name, u.codigo_universitario
ORDER BY total_por_pagar DESC;

-- 9. ¿Quién puede pedir libros hoy? Regla de la app: solo lectores, con la cuenta activa,
--    sin préstamos vencidos y sin multas por pagar
SELECT a.username,
       u.estado,
       COUNT(DISTINCT p.id) FILTER (WHERE p.estado = 'vencido'
                                       OR (p.estado = 'activo' AND p.fecha_vencimiento < CURRENT_DATE)) AS vencidos,
       COALESCE(SUM(m.monto) FILTER (WHERE NOT m.pagada), 0)                                           AS deuda,
       (u.estado = 'activo'
        AND COUNT(DISTINCT p.id) FILTER (WHERE p.estado = 'vencido'
                                            OR (p.estado = 'activo' AND p.fecha_vencimiento < CURRENT_DATE)) = 0
        AND COALESCE(SUM(m.monto) FILTER (WHERE NOT m.pagada), 0) = 0)                                  AS puede_solicitar
FROM lector lec
JOIN usuario u          ON u.id = lec.usuario_id
JOIN auth_user a        ON a.id = u.user_id
LEFT JOIN prestamo p    ON p.lector_id = lec.usuario_id
LEFT JOIN devolucion d  ON d.prestamo_id = p.id
LEFT JOIN multa m       ON m.devolucion_id = d.id
GROUP BY a.username, u.estado
ORDER BY puede_solicitar, a.username;

-- 10. Detalle de cada multa: cómo se calculó y quién la cobró
SELECT p.id                                        AS prestamo,
       a.first_name || ' ' || a.last_name          AS lector,
       d.fecha_devolucion - p.fecha_vencimiento    AS dias_retraso,     -- derivado de las fechas
       t.valor_dia                                 AS tarifa_aplicada,
       m.monto,
       m.pagada,
       m.fecha_pago,
       ca.first_name || ' ' || ca.last_name        AS cobrada_por
FROM multa m
JOIN tarifa_multa t     ON t.id = m.tarifa_id
JOIN devolucion d       ON d.id = m.devolucion_id
JOIN prestamo p         ON p.id = d.prestamo_id
JOIN usuario u          ON u.id = p.lector_id
JOIN auth_user a        ON a.id = u.user_id
LEFT JOIN usuario cu    ON cu.id = m.cobrada_por_id
LEFT JOIN auth_user ca  ON ca.id = cu.user_id
ORDER BY d.fecha_devolucion DESC;


-- =============================================================================
--  ESPECIALIZACIÓN DE USUARIOS
-- =============================================================================

-- 11. Todos los usuarios con su subtipo: se une el supertipo con cada subtipo (LEFT JOIN)
SELECT u.codigo_universitario,
       a.first_name || ' ' || a.last_name  AS nombre,
       u.tipo,                                         -- discriminador
       lec.rol,                                        -- solo lectores: estudiante | docente
       lec.carrera,
       bib.turno,                                      -- solo bibliotecarios: manana | tarde | noche
       u.estado
FROM usuario u
JOIN auth_user a              ON a.id = u.user_id
LEFT JOIN lector lec          ON lec.usuario_id = u.id
LEFT JOIN bibliotecario bib   ON bib.usuario_id = u.id
ORDER BY u.tipo, lec.rol, a.last_name;

-- 12. Verificación de la especialización TOTAL y DISJUNTA: debe devolver 0 filas.
--     Muestra usuarios que estén en ambos subtipos, en ninguno, o cuyo «tipo» no
--     coincida con la tabla del subtipo donde están. Lo disjunto y la coherencia del tipo
--     ya los impide la base (llaves foráneas compuestas, ver 14e); lo que solo revisa esta
--     consulta es lo TOTAL: un usuario sin fila en ningún subtipo.
SELECT u.id, u.codigo_universitario, u.tipo,
       (lec.usuario_id IS NOT NULL) AS esta_en_lector,
       (bib.usuario_id IS NOT NULL) AS esta_en_bibliotecario
FROM usuario u
LEFT JOIN lector lec         ON lec.usuario_id = u.id
LEFT JOIN bibliotecario bib  ON bib.usuario_id = u.id
WHERE (lec.usuario_id IS NOT NULL) = (bib.usuario_id IS NOT NULL)        -- ambos o ninguno
   OR (u.tipo = 'lector'        AND lec.usuario_id IS NULL)
   OR (u.tipo = 'bibliotecario' AND bib.usuario_id IS NULL);

-- 13. Lectores por rol y bibliotecarios: cuántos hay de cada uno
SELECT COALESCE(lec.rol, 'bibliotecario') AS grupo, COUNT(*) AS usuarios
FROM usuario u
LEFT JOIN lector lec ON lec.usuario_id = u.id
GROUP BY COALESCE(lec.rol, 'bibliotecario')
ORDER BY grupo;


-- =============================================================================
--  14. OPERACIONES DE EJEMPLO: inserción, actualización y eliminación
--      Todo va dentro de una transacción que se DESHACE al final (ROLLBACK):
--      muestra cómo trabaja la aplicación sin cambiar los datos.
-- =============================================================================
BEGIN;
-- Las llaves foráneas son diferidas (se revisan al confirmar). Para ver los errores en el
-- momento, en esta transacción se revisan de inmediato:
SET CONSTRAINTS ALL IMMEDIATE;

-- 14a. Un lector solicita un ejemplar disponible (INSERT): queda «pendiente»
INSERT INTO prestamo (lector_id, ejemplar_id)
SELECT lec.usuario_id, e.id
FROM lector lec
JOIN usuario u   ON u.id = lec.usuario_id
JOIN auth_user a ON a.id = u.user_id,
     ejemplar e
WHERE a.username = 'pedrolector' AND e.codigo_barras = 'CB-002' AND e.estado = 'disponible';

-- 14b. Un bibliotecario lo aprueba (UPDATE del préstamo y del ejemplar). Para el ejemplo se
--      simula que se aprobó hace 18 días con 15 de plazo: venció hace 3 días
UPDATE prestamo p
SET estado = 'activo', fecha_prestamo = CURRENT_DATE - 18, fecha_vencimiento = CURRENT_DATE - 3,
    aprobado_por_id = (SELECT b.usuario_id FROM bibliotecario b JOIN usuario u ON u.id = b.usuario_id
                       JOIN auth_user a ON a.id = u.user_id WHERE a.username = 'admin')
FROM ejemplar e
WHERE e.id = p.ejemplar_id AND e.codigo_barras = 'CB-002' AND p.estado = 'pendiente';
UPDATE ejemplar SET estado = 'prestado' WHERE codigo_barras = 'CB-002';

-- 14c. Se registra la devolución hoy, 3 días tarde (INSERT en devolucion), y su multa con la
--      tarifa vigente: 3 × $500 (INSERT en multa)
INSERT INTO devolucion (prestamo_id, fecha_devolucion, observacion, registrado_por_id)
SELECT p.id, CURRENT_DATE, 'bueno', p.aprobado_por_id
FROM prestamo p JOIN ejemplar e ON e.id = p.ejemplar_id
WHERE e.codigo_barras = 'CB-002' AND p.estado = 'activo';

INSERT INTO multa (devolucion_id, tarifa_id, monto)
SELECT d.id, t.id, (d.fecha_devolucion - p.fecha_vencimiento) * t.valor_dia
FROM devolucion d
JOIN prestamo p ON p.id = d.prestamo_id
JOIN ejemplar e ON e.id = p.ejemplar_id
CROSS JOIN (SELECT id, valor_dia FROM tarifa_multa WHERE activa
            ORDER BY vigente_desde DESC, id DESC LIMIT 1) AS t
WHERE e.codigo_barras = 'CB-002' AND p.estado = 'activo'
  AND d.fecha_devolucion > p.fecha_vencimiento;             -- sin retraso no hay multa

UPDATE prestamo p SET estado = 'devuelto'
FROM ejemplar e WHERE e.id = p.ejemplar_id AND e.codigo_barras = 'CB-002' AND p.estado = 'activo';
UPDATE ejemplar SET estado = 'disponible' WHERE codigo_barras = 'CB-002';

-- 14d. El lector paga la multa en el mostrador (UPDATE): fecha de pago y quién la cobró
UPDATE multa m
SET pagada = true, fecha_pago = CURRENT_DATE, cobrada_por_id = d.registrado_por_id
FROM devolucion d JOIN prestamo p ON p.id = d.prestamo_id JOIN ejemplar e ON e.id = p.ejemplar_id
WHERE m.devolucion_id = d.id AND e.codigo_barras = 'CB-002' AND p.estado = 'devuelto';

SELECT p.estado, d.fecha_devolucion, m.monto AS multa_esperada_1500, m.pagada, m.fecha_pago
FROM prestamo p
JOIN ejemplar e   ON e.id = p.ejemplar_id
JOIN devolucion d ON d.prestamo_id = p.id
JOIN multa m      ON m.devolucion_id = d.id
WHERE e.codigo_barras = 'CB-002';

-- 14e. Restricciones de integridad en acción: cada intento inválido es rechazado por la base
DO $$
BEGIN
    BEGIN  -- DISJUNTA: un bibliotecario no puede estar también en la tabla lector
        INSERT INTO lector (usuario_id) SELECT usuario_id FROM bibliotecario LIMIT 1;
        RAISE NOTICE 'ERROR: un usuario quedó en los dos subtipos';
    EXCEPTION WHEN foreign_key_violation THEN
        RAISE NOTICE 'Bloqueado (lector_usuario_id_tipo_fkey): ese usuario es de tipo bibliotecario, no cabe en lector';
    END;
    BEGIN  -- DISJUNTA: un lector no puede estar también en la tabla bibliotecario
        INSERT INTO bibliotecario (usuario_id) SELECT usuario_id FROM lector LIMIT 1;
        RAISE NOTICE 'ERROR: un usuario quedó en los dos subtipos';
    EXCEPTION WHEN foreign_key_violation THEN
        RAISE NOTICE 'Bloqueado (bibliotecario_usuario_id_tipo_fkey): ese usuario es de tipo lector, no cabe en bibliotecario';
    END;
    BEGIN  -- TIPO COHERENTE: no se cambia el tipo de un usuario que ya está en su subtipo
        UPDATE usuario SET tipo = 'bibliotecario' WHERE id = (SELECT usuario_id FROM lector LIMIT 1);
        RAISE NOTICE 'ERROR: un lector quedó con tipo bibliotecario';
    EXCEPTION WHEN foreign_key_violation THEN
        RAISE NOTICE 'Bloqueado (lector_usuario_id_tipo_fkey): el lector dejaría de coincidir con su usuario';
    END;
    BEGIN  -- CHECK: el turno solo puede ser mañana, tarde o noche
        UPDATE bibliotecario SET turno = 'madrugada';
        RAISE NOTICE 'ERROR: se aceptó un turno inventado';
    EXCEPTION WHEN check_violation THEN
        RAISE NOTICE 'Bloqueado (CHECK bibliotecario_turno_valido): el turno es manana, tarde o noche';
    END;
    BEGIN  -- LLAVE FORÁNEA al subtipo: un bibliotecario no puede ser el lector de un préstamo
        INSERT INTO prestamo (lector_id, ejemplar_id)
        SELECT b.usuario_id, e.id FROM bibliotecario b, ejemplar e WHERE e.codigo_barras = 'CB-005' LIMIT 1;
        RAISE NOTICE 'ERROR: un bibliotecario quedó como lector de un préstamo';
    EXCEPTION WHEN foreign_key_violation THEN
        RAISE NOTICE 'Bloqueado (prestamo_lector_id_fkey): un bibliotecario no está en la tabla lector, no puede pedir libros';
    END;
    BEGIN  -- LLAVE FORÁNEA al subtipo: un lector no puede aprobar préstamos
        UPDATE prestamo SET aprobado_por_id = lector_id WHERE estado = 'activo';
        RAISE NOTICE 'ERROR: un lector quedó como aprobador';
    EXCEPTION WHEN foreign_key_violation THEN
        RAISE NOTICE 'Bloqueado (prestamo_aprobado_por_id_fkey): solo un bibliotecario aprueba préstamos';
    END;
    BEGIN  -- ON DELETE RESTRICT: no se borra un ejemplar con historial de préstamos
        DELETE FROM ejemplar WHERE codigo_barras = 'CB-002';
        RAISE NOTICE 'ERROR: se borró un ejemplar con préstamos';
    EXCEPTION WHEN restrict_violation OR foreign_key_violation THEN
        RAISE NOTICE 'Bloqueado (prestamo_ejemplar_id_fkey): el ejemplar CB-002 tiene préstamos registrados';
    END;
    BEGIN  -- UNIQUE: a lo sumo una multa por devolución
        INSERT INTO multa (devolucion_id, tarifa_id, monto) SELECT devolucion_id, tarifa_id, 100 FROM multa LIMIT 1;
        RAISE NOTICE 'ERROR: una devolución quedó con dos multas';
    EXCEPTION WHEN unique_violation THEN
        RAISE NOTICE 'Bloqueado (UNIQUE multa_devolucion_id_key): la devolución ya tiene su multa';
    END;
    BEGIN  -- CHECK: una multa pagada debe tener fecha de pago
        UPDATE multa SET pagada = true, fecha_pago = NULL WHERE NOT pagada;
        RAISE NOTICE 'ERROR: se aceptó una multa pagada sin fecha de pago';
    EXCEPTION WHEN check_violation THEN
        RAISE NOTICE 'Bloqueado (CHECK multa_pago_coherente): pagada exige fecha de pago';
    END;
    BEGIN  -- CHECK: una multa existe solo si hay algo que cobrar
        UPDATE multa SET monto = 0;
        RAISE NOTICE 'ERROR: se aceptó una multa de $0';
    EXCEPTION WHEN check_violation THEN
        RAISE NOTICE 'Bloqueado (CHECK multa_monto_positivo): el monto debe ser mayor que cero';
    END;
    BEGIN  -- CHECK: la tarifa debe ser mayor que cero
        INSERT INTO tarifa_multa (valor_dia) VALUES (-100);
        RAISE NOTICE 'ERROR: se aceptó una tarifa negativa';
    EXCEPTION WHEN check_violation THEN
        RAISE NOTICE 'Bloqueado (CHECK tarifa_multa_positiva): la tarifa debe ser mayor que cero';
    END;
    BEGIN  -- CHECK: el vencimiento no puede ser anterior al préstamo
        UPDATE prestamo SET fecha_vencimiento = fecha_prestamo - 1 WHERE fecha_prestamo IS NOT NULL;
        RAISE NOTICE 'ERROR: se aceptó un vencimiento anterior al préstamo';
    EXCEPTION WHEN check_violation THEN
        RAISE NOTICE 'Bloqueado (CHECK prestamo_vencimiento_posterior): el vencimiento no puede ser anterior al préstamo';
    END;
    BEGIN  -- CHECK: el rol del lector solo puede ser estudiante o docente
        UPDATE lector SET rol = 'bibliotecario';
        RAISE NOTICE 'ERROR: un lector quedó con rol bibliotecario';
    EXCEPTION WHEN check_violation THEN
        RAISE NOTICE 'Bloqueado (CHECK lector_rol_valido): un lector es estudiante o docente';
    END;
    BEGIN  -- UNIQUE: el ISBN no se repite
        INSERT INTO libro (isbn, titulo, editorial, anio_publicacion)
        SELECT isbn, 'Copia', 'X', 2000 FROM libro LIMIT 1;
        RAISE NOTICE 'ERROR: se aceptó un ISBN repetido';
    EXCEPTION WHEN unique_violation THEN
        RAISE NOTICE 'Bloqueado (UNIQUE libro_isbn_key): ya existe un libro con ese ISBN';
    END;
    BEGIN  -- CHECK: estados válidos del ejemplar
        UPDATE ejemplar SET estado = 'robado' WHERE codigo_barras = 'CB-005';
        RAISE NOTICE 'ERROR: se aceptó un estado inventado';
    EXCEPTION WHEN check_violation THEN
        RAISE NOTICE 'Bloqueado (CHECK ejemplar_estado_valido): «robado» no es un estado válido';
    END;
END $$;

-- 14f. Eliminación permitida: un autor sin libros (DELETE)
INSERT INTO autor (nombre, apellido) VALUES ('Autor', 'De prueba');
DELETE FROM autor WHERE nombre = 'Autor' AND apellido = 'De prueba';

ROLLBACK;  -- nada de la sección 14 queda guardado
