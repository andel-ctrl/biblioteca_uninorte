-- =============================================================================
--  Sistema de préstamos de la Biblioteca Universitaria · Laboratorio 01
--  Script 2 de 3: DATOS BÁSICOS
--
--  Ejecutar después de 01_creacion_tablas.sql:
--      psql -U postgres -d biblioteca_db -v ON_ERROR_STOP=1 -f sql/02_datos_basicos.sql
--
--  Carga lo necesario para que la aplicación funcione: tarifa de multa, categorías,
--  autores, libros con sus portadas, ejemplares y usuarios de prueba. Son los mismos
--  datos de datos_iniciales.py. Al final hay una sección OPCIONAL con préstamos de
--  demostración para que los reportes y las consultas del script 3 muestren resultados.
--
--  Usuarios de prueba (usuario · rol · contraseña):
--    admin        bibliotecario  admin123
--    andel        bibliotecario  andeladmin
--    luisangel    bibliotecario  luisadmin
--    carcabria    bibliotecario  carbabriaadmin
--    dubalaguil   bibliotecario  dubalaguiladmin
--    matthewcis   bibliotecario  matthewcisadmin
--    pedrolector  estudiante     est123456
--    gatiella     estudiante     ao3_4_eva
--    pipe         estudiante     pipeestuvoaqui
--    mrsluis      estudiante     daynnite
--    mihovil      estudiante     eldering
--    ponllo09     estudiante     ponllo09
-- =============================================================================

BEGIN;

-- Tarifa de multa por día de retraso (1)
INSERT INTO tarifa_multa (id, valor_dia, vigente_desde, activa) VALUES
    (1, 500.00, '2026-01-01'::date, true);

-- Categorías (8)
INSERT INTO categoria (id, nombre, descripcion) VALUES
    (1, 'Ciencias', ''),
    (2, 'Humanidades', ''),
    (3, 'Tecnología', ''),
    (4, 'Literatura', ''),
    (5, 'Historia', ''),
    (6, 'Matemáticas', ''),
    (7, 'Derecho', ''),
    (8, 'Medicina', '');

-- Autores (27)
INSERT INTO autor (id, nombre, apellido, biografia) VALUES
    (1, 'Gabriel', 'García Márquez', ''),
    (2, 'Donald', 'Knuth', ''),
    (3, 'Robert', 'Martin', ''),
    (4, 'Andrew', 'Tanenbaum', ''),
    (5, 'Isabel', 'Allende', ''),
    (6, 'Hermano', 'Héctor', ''),
    (7, 'Gerald', 'Weinberg', ''),
    (8, 'Viktor', 'Frank', ''),
    (9, 'Scott', 'Mescudi', ''),
    (10, 'Dan', 'Brownstein', ''),
    (11, 'Arturo', 'Uslar', ''),
    (12, 'Marco', 'Cicerón', ''),
    (13, 'Antoine', 'Saint-Clair', ''),
    (14, 'Frank', 'Herbert', ''),
    (15, 'Mirko', 'Popovich', ''),
    (16, 'Guillermo', 'Cabrera', ''),
    (17, 'José', 'Barros', ''),
    (18, 'Brandon', 'Sanderson', ''),
    (19, 'Laura', 'Restrepo', ''),
    (20, 'Carl', 'Sagan', ''),
    (21, 'Bobby', 'Drake', ''),
    (22, 'Felipe', 'Peláez', ''),
    (23, 'Jane', 'Goodall', ''),
    (24, 'Eiichiro', 'Oda', ''),
    (25, 'Miles', 'Coltrane', ''),
    (26, 'Charles', 'Taze', ''),
    (27, 'Karl', 'Marxell', '');

-- Libros (títulos) (26)
INSERT INTO libro (id, isbn, titulo, editorial, anio_publicacion, descripcion, portada, creado_en, categoria_id) VALUES
    (1, '978-0-385-47348-3', 'Doscientos años de soledad', 'Editorial Sudamericana', 1967, '', 'portadas/doscientos.jpg', '2026-10-16T11:08:13.876506-05:00'::timestamptz, 4),
    (2, '978-0-201-83595-3', 'Como programar para gente que no sabe programar', 'Addison-Wesley', 1968, '', 'portadas/programar.jpg', '2026-10-16T11:08:13.885192-05:00'::timestamptz, 3),
    (3, '978-0-13-235088-4', 'La biblia: el reciente testamento', 'Church Editorial', 2008, '', 'portadas/biblia.jpg', '2026-10-16T11:08:13.887980-05:00'::timestamptz, 5),
    (4, '978-0-13-468599-1', 'La pasión de Baldor', 'Santillana', 2011, '', 'portadas/baldor.jpg', '2026-10-16T11:08:13.891138-05:00'::timestamptz, 4),
    (5, '978-958-04-1120-1', 'Yuropari', 'Editorial Amazonia', 1995, '', '', '2026-10-16T11:08:13.893727-05:00'::timestamptz, 4),
    (6, '978-84-344-0231-5', 'Tomas y Gerald: Analisis profundo de relaciones interpesonales', 'Paidós', 2005, '', 'portadas/tomasygerald.jpg', '2026-10-16T11:08:13.902943-05:00'::timestamptz, 2),
    (7, '978-84-254-1533-8', 'El hombre en busca de opiniones', 'Herder Editorial', 1982, '', 'portadas/opiniones.jpg', '2026-10-16T11:08:13.906026-05:00'::timestamptz, 2),
    (8, '978-0-06-231609-7', 'Day N Night', 'HarperCollins', 2015, '', 'portadas/dayandnight.jpg', '2026-10-16T11:08:13.908493-05:00'::timestamptz, 4),
    (9, '978-84-08-05294-4', 'Código De La Espriella', 'Planeta', 2006, '', 'portadas/espriella.jpg', '2026-10-16T11:08:13.910784-05:00'::timestamptz, 5),
    (10, '978-958-06-0341-5', '12 Ponllos Peregrinos', 'Norma', 1992, '', 'portadas/ponllos.jpg', '2026-10-16T11:08:13.913375-05:00'::timestamptz, 4),
    (11, '978-84-249-1402-9', '10 años de elocuencia', 'Gredos', 1978, '', 'portadas/elocuencia.jpg', '2026-10-16T11:08:13.916098-05:00'::timestamptz, 2),
    (12, '978-0-14-132104-2', 'Albert el chico volador', 'Puffin Books', 2001, '', 'portadas/albert.jpg', '2026-10-16T11:08:13.918588-05:00'::timestamptz, 4),
    (13, '978-84-9759-682-4', 'Perdidos en la arena', 'Debolsillo', 1984, '', 'portadas/arena.jpg', '2026-10-16T11:08:13.921014-05:00'::timestamptz, 4),
    (14, '978-84-339-0820-9', 'El Diario de Mirko', 'Anagrama', 1999, '', 'portadas/mirko.jpg', '2026-10-16T11:08:13.923601-05:00'::timestamptz, 5),
    (15, '978-958-8883-05-2', 'Joselo y sus vagancias', 'Caribe Editores', 2014, '', 'portadas/joselo.jpg', '2026-10-16T11:08:13.926199-05:00'::timestamptz, 4),
    (16, '978-958-9045-12-3', 'Lo que se llevo Jefferson', 'Editorial La Mojana', 1987, '', 'portadas/jefferson.jpg', '2026-10-16T11:08:13.928916-05:00'::timestamptz, 5),
    (17, '978-84-666-5881-2', 'Los secretos de la universidad del Monte', 'Nova', 2018, '', 'portadas/monte.jpg', '2026-10-16T11:08:13.931460-05:00'::timestamptz, 4),
    (18, '978-958-5446-21-2', 'Las aventuras del pollo Sammy', 'Alfaguara', 2016, '', 'portadas/sammy.jpg', '2026-10-16T11:08:13.934343-05:00'::timestamptz, 4),
    (19, '978-84-253-5100-6', '¿Y donde estan las monas?', 'Crítica', 1997, '', 'portadas/monas.jpg', '2026-10-16T11:08:13.937331-05:00'::timestamptz, 1),
    (20, '978-1-302-90123-4', 'Iceman el chico caliente', 'Marvel Press', 2017, '', 'portadas/iceman.jpg', '2026-10-16T11:08:13.940178-05:00'::timestamptz, 4),
    (21, '978-958-42-8811-0', '2 veces Pipe', 'Intermedio Editores', 2020, '', 'portadas/pipe.jpg', '2026-10-16T11:08:13.943037-05:00'::timestamptz, 4),
    (22, '978-84-9988-341-1', 'El Mono que pudo volar', 'Kairós', 2009, '', 'portadas/mono.jpg', '2026-10-16T11:08:13.945845-05:00'::timestamptz, 1),
    (23, '978-1-4215-3625-5', 'En camino al One Piece', 'Shueisha Jump Comics', 2003, '', 'portadas/onepiece.jpg', '2026-10-16T11:08:13.948289-05:00'::timestamptz, 4),
    (24, '978-84-92669-12-7', 'La guitarra saxofonista', 'Alba Editorial', 1991, '', 'portadas/guitarra.jpg', '2026-10-16T11:08:13.950906-05:00'::timestamptz, 4),
    (25, '978-0-7868-6124-9', 'Sentado en el Atalaya', 'Watchtower Press', 1989, '', 'portadas/atalaya.jpg', '2026-10-16T11:08:13.953108-05:00'::timestamptz, 5),
    (26, '978-84-460-2187-2', 'Matthew el comunista', 'Akal', 1974, '', 'portadas/matthew.jpg', '2026-10-16T11:08:13.955813-05:00'::timestamptz, 5);

-- Autores de cada libro (muchos a muchos) (28)
INSERT INTO libro_autor (id, libro_id, autor_id) VALUES
    (1, 1, 1),
    (2, 2, 2),
    (3, 3, 3),
    (4, 4, 4),
    (5, 5, 6),
    (6, 6, 7),
    (7, 7, 8),
    (8, 8, 9),
    (9, 9, 10),
    (10, 10, 1),
    (11, 10, 11),
    (12, 11, 12),
    (13, 12, 13),
    (14, 13, 14),
    (15, 14, 15),
    (16, 15, 16),
    (17, 16, 17),
    (18, 17, 18),
    (19, 18, 19),
    (20, 18, 5),
    (21, 19, 20),
    (22, 20, 21),
    (23, 21, 22),
    (24, 22, 23),
    (25, 23, 24),
    (26, 24, 25),
    (27, 25, 26),
    (28, 26, 27);

-- Ejemplares (copias físicas) (31)
INSERT INTO ejemplar (id, codigo_barras, sala, estante, estado, notas, fecha_adquisicion, libro_id) VALUES
    (1, 'CB-001', 'A', '1', 'disponible', '', NULL, 1),
    (2, 'CB-002', 'A', '1', 'disponible', '', NULL, 1),
    (3, 'CB-003', 'B', '2', 'disponible', '', NULL, 2),
    (4, 'CB-004', 'B', '3', 'disponible', '', NULL, 3),
    (5, 'CB-005', 'B', '3', 'disponible', '', NULL, 3),
    (6, 'CB-006', 'B', '4', 'disponible', '', NULL, 4),
    (7, 'CB-007', 'A', '2', 'disponible', '', NULL, 5),
    (8, 'CB-008', 'C', '1', 'disponible', '', NULL, 6),
    (9, 'CB-009', 'C', '1', 'disponible', '', NULL, 6),
    (10, 'CB-010', 'C', '2', 'disponible', '', NULL, 7),
    (11, 'CB-011', 'A', '3', 'disponible', '', NULL, 8),
    (12, 'CB-012', 'B', '1', 'disponible', '', NULL, 9),
    (13, 'CB-013', 'A', '1', 'disponible', '', NULL, 10),
    (14, 'CB-014', 'C', '3', 'disponible', '', NULL, 11),
    (15, 'CB-015', 'A', '4', 'disponible', '', NULL, 12),
    (16, 'CB-016', 'A', '4', 'disponible', '', NULL, 13),
    (17, 'CB-017', 'B', '2', 'disponible', '', NULL, 14),
    (18, 'CB-018', 'A', '5', 'disponible', '', NULL, 15),
    (19, 'CB-019', 'B', '3', 'disponible', '', NULL, 16),
    (20, 'CB-021', 'A', '6', 'disponible', '', NULL, 17),
    (21, 'CB-022', 'A', '6', 'disponible', '', NULL, 17),
    (22, 'CB-023', 'A', '7', 'disponible', '', NULL, 18),
    (23, 'CB-024', 'D', '1', 'disponible', '', NULL, 19),
    (24, 'CB-025', 'A', '8', 'disponible', '', NULL, 20),
    (25, 'CB-026', 'C', '4', 'disponible', '', NULL, 21),
    (26, 'CB-027', 'D', '2', 'disponible', '', NULL, 22),
    (27, 'CB-028', 'A', '9', 'disponible', '', NULL, 23),
    (28, 'CB-029', 'A', '9', 'disponible', '', NULL, 23),
    (29, 'CB-030', 'C', '5', 'disponible', '', NULL, 24),
    (30, 'CB-031', 'B', '4', 'disponible', '', NULL, 25),
    (31, 'CB-032', 'B', '5', 'disponible', '', NULL, 26);

-- Cuentas de acceso (contraseñas cifradas con pbkdf2; ver tabla de usuarios de prueba arriba) (12)
INSERT INTO auth_user (id, password, is_superuser, username, first_name, last_name, email, is_staff, is_active, date_joined) VALUES
    (1, 'pbkdf2_sha256$1500000$UfrkpXNT3CkAsV8A8XsFDK$6xlWR3kFEblD92HfqSddO+mKr4sip1e758aFvCtynqk=', true, 'admin', 'Administrador', 'Biblioteca', 'admin@biblioteca.edu', true, true, '2026-10-16T11:08:13.959411-05:00'::timestamptz),
    (2, 'pbkdf2_sha256$1500000$W9O46m7hg1y6g91w1oOy1q$qPg4hmSU2l/Fi1+e66WTOw3CXP/TBXEzsumMY5Su0to=', true, 'andel', 'Angelo', 'De León', 'adeleon@biblioteca.edu', true, true, '2026-10-16T11:08:14.152500-05:00'::timestamptz),
    (3, 'pbkdf2_sha256$1500000$F3tY3A5mSFjuV4wOkqjDXE$7IPd6NqoccONO6dF1so09P0izauHNBwgd3GUHN/zZcQ=', true, 'luisangel', 'Luis Angel', 'Cuellar', 'lcuellar@biblioteca.edu', true, true, '2026-10-16T11:08:14.332295-05:00'::timestamptz),
    (4, 'pbkdf2_sha256$1500000$sJBb0wzHppTz9LsUgvSTbW$p6375Z69/+fU1GnZ53b4IL0Y1JWAARFO891y/nl3JzQ=', true, 'carcabria', 'Carlos', 'Calabria', 'ccalabria@biblioteca.edu', true, true, '2026-10-16T11:08:14.512646-05:00'::timestamptz),
    (5, 'pbkdf2_sha256$1500000$U37hHeWwhoaqkvoM0Htvbu$5HigYneIFZOii3NHb+6ArT3uY3gaQYlC2EGTrrGy9ZI=', true, 'dubalaguil', 'Dubal', 'Aguilar', 'daguilar@biblioteca.edu', true, true, '2026-10-16T11:08:14.693961-05:00'::timestamptz),
    (6, 'pbkdf2_sha256$1500000$qzvRRQA6szENAbWTN1qwrD$NnED6Ck31CdoUxzx+f4nJWY4KerjnUepc4vSEPEQ7hY=', true, 'matthewcis', 'Mateo', 'Cisneros', 'mcisneros@biblioteca.edu', true, true, '2026-10-16T11:08:14.900437-05:00'::timestamptz),
    (7, 'pbkdf2_sha256$1500000$v4O4IaEv3UD2ousgBtjPHP$N4bjKOQW7pWrQ8W7IkQT2ul+c8v6ANhqgSUsUNBuCLM=', false, 'pedrolector', 'Pedro', 'De Leon', 'estudiante1@universidad.edu', false, true, '2026-10-16T11:08:15.121377-05:00'::timestamptz),
    (8, 'pbkdf2_sha256$1500000$UMjxaq5mnnuWtALp1La1lx$sXchUticeqgkchVMMSiAOqB4Z7IWWav0zeDD1khz3kY=', false, 'gatiella', 'Gabriella', 'Llanta', 'gllanta@uninorte.edu.co', false, true, '2026-10-16T11:08:15.316948-05:00'::timestamptz),
    (9, 'pbkdf2_sha256$1500000$bo8rc4TT5y2nff7lr7q2mC$Q7+LiugZwnZoS+wBpk7KoGztA4A6QLDMmUY9OEPm6kk=', false, 'pipe', 'Andres', 'Palacio', 'apalacio@uninorte.edu.co', false, true, '2026-10-16T11:08:15.506403-05:00'::timestamptz),
    (10, 'pbkdf2_sha256$1500000$e7NJhbPgsU5M3VsfS9io3l$d/zx51W4neI2AZ35HLMXtwSbPwFREHFQ7/ToKszwcdc=', false, 'mrsluis', 'Luis', 'Cortéz', 'lcortez@uninorte.edu.co', false, true, '2026-10-16T11:08:15.703355-05:00'::timestamptz),
    (11, 'pbkdf2_sha256$1500000$PCCDLn9Cc5fzSLRKr6rfh7$1CpZZUb9m3n4sCJk4QgfZKmjKI0ocIDLOxpYKabM6VA=', false, 'mihovil', 'Mirko', 'Notengopila', 'mnotengopila@uninorte.edu.co', false, true, '2026-10-16T11:08:15.959464-05:00'::timestamptz),
    (12, 'pbkdf2_sha256$1500000$czg9M3DMQrU0fJDbTrTibX$zT6kbI/OeY+dTnyynCFr6joccxo5xwKsnzbxgU5yNI0=', false, 'ponllo09', 'Rafael', 'Llantos', 'rllantos@uninorte.edu.co', false, true, '2026-10-16T11:08:16.143361-05:00'::timestamptz);

-- Usuarios (supertipo) (12)
INSERT INTO usuario (id, codigo_universitario, identificacion, tipo, estado, telefono, fecha_registro, user_id) VALUES
    (1, 'ADMIN-001', '0000000001', 'bibliotecario', 'activo', '', '2026-10-16T11:08:14.147354-05:00'::timestamptz, 1),
    (2, 'ADMIN-002', '1042781920', 'bibliotecario', 'activo', '', '2026-10-16T11:08:14.330056-05:00'::timestamptz, 2),
    (3, 'ADMIN-003', '1043892011', 'bibliotecario', 'activo', '', '2026-10-16T11:08:14.508190-05:00'::timestamptz, 3),
    (4, 'ADMIN-004', '1044903122', 'bibliotecario', 'activo', '', '2026-10-16T11:08:14.691745-05:00'::timestamptz, 4),
    (5, 'ADMIN-005', '1045014233', 'bibliotecario', 'activo', '', '2026-10-16T11:08:14.898947-05:00'::timestamptz, 5),
    (6, 'ADMIN-006', '1046125344', 'bibliotecario', 'activo', '', '2026-10-16T11:08:15.119170-05:00'::timestamptz, 6),
    (7, 'EST-2024-001', '1234567890', 'lector', 'activo', '', '2026-10-16T11:08:15.313064-05:00'::timestamptz, 7),
    (8, 'EST-2024-002', '1143209841', 'lector', 'activo', '', '2026-10-16T11:08:15.504333-05:00'::timestamptz, 8),
    (9, 'EST-2024-003', '1143310952', 'lector', 'activo', '', '2026-10-16T11:08:15.700557-05:00'::timestamptz, 9),
    (10, 'EST-2024-004', '1143421063', 'lector', 'activo', '', '2026-10-16T11:08:15.956900-05:00'::timestamptz, 10),
    (11, 'EST-2024-005', '1143532174', 'lector', 'activo', '', '2026-10-16T11:08:16.140478-05:00'::timestamptz, 11),
    (12, 'EST-2024-006', '1143643285', 'lector', 'activo', '', '2026-10-16T11:08:16.331156-05:00'::timestamptz, 12);

-- Lectores (subtipo): estudiantes y docentes. La columna tipo toma su valor fijo por defecto (6)
INSERT INTO lector (usuario_id, rol, carrera) VALUES
    (7, 'estudiante', 'Ingeniería de Sistemas'),
    (8, 'estudiante', 'Diseño Gráfico'),
    (9, 'estudiante', 'Ingeniería Mecánica'),
    (10, 'estudiante', 'Música'),
    (11, 'estudiante', 'Ingeniería Eléctrica'),
    (12, 'estudiante', 'Ciencia Política');

-- Bibliotecarios (subtipo), con su turno (6)
INSERT INTO bibliotecario (usuario_id, turno) VALUES
    (1, 'manana'),
    (2, 'tarde'),
    (3, 'noche'),
    (4, 'manana'),
    (5, 'tarde'),
    (6, 'noche');

-- Migraciones de Django que equivalen al script 01 (33): la app sabe que la base está al día
INSERT INTO django_migrations (app, name, applied) VALUES
    ('contenttypes', '0001_initial', now()),
    ('auth', '0001_initial', now()),
    ('admin', '0001_initial', now()),
    ('admin', '0002_logentry_remove_auto_add', now()),
    ('admin', '0003_logentry_add_action_flag_choices', now()),
    ('contenttypes', '0002_remove_content_type_name', now()),
    ('auth', '0002_alter_permission_name_max_length', now()),
    ('auth', '0003_alter_user_email_max_length', now()),
    ('auth', '0004_alter_user_username_opts', now()),
    ('auth', '0005_alter_user_last_login_null', now()),
    ('auth', '0006_require_contenttypes_0002', now()),
    ('auth', '0007_alter_validators_add_error_messages', now()),
    ('auth', '0008_alter_user_username_max_length', now()),
    ('auth', '0009_alter_user_last_name_max_length', now()),
    ('auth', '0010_alter_group_name_max_length', now()),
    ('auth', '0011_update_proxy_permissions', now()),
    ('auth', '0012_alter_user_first_name_max_length', now()),
    ('catalogos', '0001_initial', now()),
    ('catalogos', '0002_restricciones_check', now()),
    ('catalogos', '0003_extension_unaccent', now()),
    ('catalogos', '0004_tablas_y_ubicacion', now()),
    ('usuarios', '0001_initial', now()),
    ('usuarios', '0002_restricciones_check', now()),
    ('prestamos', '0001_initial', now()),
    ('prestamos', '0002_estado_perdido', now()),
    ('prestamos', '0003_restricciones_check', now()),
    ('usuarios', '0003_especializacion', now()),
    ('prestamos', '0004_multa_y_especializacion', now()),
    ('prestamos', '0005_nombres_de_restricciones', now()),
    ('sessions', '0001_initial', now()),
    ('usuarios', '0004_bibliotecario_turno', now()),
    ('usuarios', '0005_subtipos_disjuntos', now()),
    ('prestamos', '0006_valores_por_defecto', now());

-- Los próximos registros creados desde la app continúan después de los id insertados
SELECT setval(pg_get_serial_sequence('tarifa_multa', 'id'), (SELECT MAX(id) FROM tarifa_multa));
SELECT setval(pg_get_serial_sequence('categoria', 'id'), (SELECT MAX(id) FROM categoria));
SELECT setval(pg_get_serial_sequence('autor', 'id'), (SELECT MAX(id) FROM autor));
SELECT setval(pg_get_serial_sequence('libro', 'id'), (SELECT MAX(id) FROM libro));
SELECT setval(pg_get_serial_sequence('libro_autor', 'id'), (SELECT MAX(id) FROM libro_autor));
SELECT setval(pg_get_serial_sequence('ejemplar', 'id'), (SELECT MAX(id) FROM ejemplar));
SELECT setval(pg_get_serial_sequence('auth_user', 'id'), (SELECT MAX(id) FROM auth_user));
SELECT setval(pg_get_serial_sequence('usuario', 'id'), (SELECT MAX(id) FROM usuario));

COMMIT;


-- =============================================================================
--  OPCIONAL · PRÉSTAMOS DE DEMOSTRACIÓN
--  Un caso de cada estado, con fechas relativas a hoy (siempre coherentes con el día en
--  que se ejecute). Si no se quieren, basta con no ejecutar esta parte.
--  Las multas usan la tarifa 1 ($500 por día). Aprueba, registra y cobra «admin».
-- =============================================================================

BEGIN;

INSERT INTO prestamo
    (fecha_solicitud, fecha_prestamo, fecha_vencimiento, estado, observaciones, lector_id, ejemplar_id, aprobado_por_id)
SELECT now() - make_interval(days => d.dias_solicitud), CURRENT_DATE - d.prestado_hace, CURRENT_DATE - d.vence_hace,
       d.estado, '', l.usuario_id, e.id,
       CASE WHEN d.estado = 'pendiente' THEN NULL ELSE bib.usuario_id END   -- quien aprobó o rechazó
FROM (VALUES
    -- usuario,      ejemplar,  estado,      días desde la solicitud, prestado hace, vence hace (negativo = en el futuro)
    ('pedrolector', 'CB-001', 'activo',     5,  5,    -10),   -- en curso, vence en 10 días
    ('gatiella',    'CB-003', 'vencido',    20, 20,   4),     -- vencido hace 4 días: mora de $2.000 y no puede pedir más
    ('pipe',        'CB-004', 'devuelto',   30, 30,   15),    -- devuelto 3 días tarde: multa de $1.500 sin pagar
    ('pedrolector', 'CB-006', 'devuelto',   25, 25,   10),    -- devuelto a tiempo: sin multa
    ('mihovil',     'CB-012', 'devuelto',   22, 22,   9),     -- devuelto 2 días tarde: multa de $1.000 ya pagada
    ('mrsluis',     'CB-008', 'pendiente',  0,  NULL, NULL),  -- solicitud esperando aprobación
    ('mihovil',     'CB-010', 'rechazado',  3,  NULL, NULL),  -- solicitud rechazada
    ('ponllo09',    'CB-011', 'perdido',    40, 40,   25)     -- reportado como perdido con 23 días de mora
) AS d(usuario, codigo, estado, dias_solicitud, prestado_hace, vence_hace)
JOIN auth_user a  ON a.username = d.usuario
JOIN usuario u    ON u.user_id = a.id
JOIN lector l     ON l.usuario_id = u.id          -- solo un lector puede pedir
JOIN ejemplar e   ON e.codigo_barras = d.codigo
CROSS JOIN (SELECT b.usuario_id FROM bibliotecario b JOIN usuario u ON u.id = b.usuario_id
            JOIN auth_user a ON a.id = u.user_id WHERE a.username = 'admin') AS bib;

-- Devoluciones de los préstamos cerrados
INSERT INTO devolucion (fecha_devolucion, observacion, detalle_observacion, prestamo_id, registrado_por_id)
SELECT d.fecha, d.observacion, d.detalle, p.id, bib.usuario_id
FROM (VALUES
    ('CB-004', CURRENT_DATE - 12, '',        ''),
    ('CB-006', CURRENT_DATE - 12, 'bueno',   ''),
    ('CB-012', CURRENT_DATE - 7,  'bueno',   ''),
    ('CB-011', CURRENT_DATE - 2,  'perdido', 'Pérdida reportada por el lector')
) AS d(codigo, fecha, observacion, detalle)
JOIN ejemplar e ON e.codigo_barras = d.codigo
JOIN prestamo p ON p.ejemplar_id = e.id AND p.estado IN ('devuelto', 'perdido')
CROSS JOIN (SELECT b.usuario_id FROM bibliotecario b JOIN usuario u ON u.id = b.usuario_id
            JOIN auth_user a ON a.id = u.user_id WHERE a.username = 'admin') AS bib;

-- Multas: solo de las devoluciones tardías. monto = días de retraso × valor_dia de la tarifa.
-- La de CB-012 se pagó el mismo día de la devolución (tiene fecha de pago y quién la cobró).
INSERT INTO multa (devolucion_id, tarifa_id, monto, pagada, fecha_pago, cobrada_por_id)
SELECT dv.id, t.id, (dv.fecha_devolucion - p.fecha_vencimiento) * t.valor_dia,
       x.pagada, CASE WHEN x.pagada THEN dv.fecha_devolucion END,
       CASE WHEN x.pagada THEN dv.registrado_por_id END
FROM (VALUES ('CB-004', false), ('CB-012', true), ('CB-011', false)) AS x(codigo, pagada)
JOIN ejemplar e      ON e.codigo_barras = x.codigo
JOIN prestamo p      ON p.ejemplar_id = e.id
JOIN devolucion dv   ON dv.prestamo_id = p.id
JOIN tarifa_multa t  ON t.id = 1
WHERE dv.fecha_devolucion > p.fecha_vencimiento;

-- Estado de los ejemplares según sus préstamos
UPDATE ejemplar SET estado = 'prestado' WHERE codigo_barras IN ('CB-001', 'CB-003');
UPDATE ejemplar SET estado = 'perdido'  WHERE codigo_barras = 'CB-011';

COMMIT;
