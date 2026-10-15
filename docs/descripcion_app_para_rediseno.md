# Sistema de Préstamo de Libros — Biblioteca Universitaria
## Descripción funcional y visual para rediseño de la interfaz

Este documento describe todo lo que hace la aplicación hoy, cómo se navega y cómo se ve, con el objetivo de proponer una nueva estructura visual que **conserve todas las funcionalidades** y mejore la usabilidad y la estética.

---

## 1. Contexto del proyecto

- **Curso:** Bases de Datos, periodo 202630. Laboratorio 01, trabajo en grupo (máximo 5 estudiantes).
- **Entrega:** 19 de octubre. **Sustentación:** 20 de octubre, en horas de clase.
- **Tecnología:**
  - Backend: Python + Django 5 (páginas renderizadas en el servidor con plantillas Django; no es una SPA).
  - Base de datos: PostgreSQL.
  - Frontend: HTML con plantillas Django, **Bootstrap 5.3.3** (CDN), **Bootstrap Icons 1.11.3**, un archivo `static/css/styles.css` propio y Google Fonts. No se usa React ni ningún framework de JavaScript; el JavaScript es solo el de Bootstrap (menús desplegables, cerrar alertas).
- **Restricciones para el rediseño:**
  - Se puede cambiar libremente el HTML de las plantillas y el CSS.
  - Deben mantenerse: las rutas (URLs), los nombres de los campos de los formularios (`name="..."`), el token CSRF en cada formulario `POST`, los permisos por rol y los mensajes del sistema (alertas de éxito, error y advertencia).
  - Todas las plantillas heredan de una plantilla base (`base.html`), que contiene la barra de navegación, la zona de mensajes y el pie de página. Un cambio en la base afecta a todas las pantallas.
  - La app debe verse bien en computador (uso principal del bibliotecario) y en celular (uso frecuente del estudiante).

---

## 2. Enunciado del laboratorio (texto del profesor)

### Indicaciones generales (correo del profesor)
En la plataforma está la actividad Laboratorio 01, en la cual desarrollarán una aplicación que haga uso de una base de datos relacional para gestionar un proceso de préstamo de libros en la biblioteca.
- El trabajo debe realizarse en grupos de máximo cinco (5) estudiantes.
- La fecha de entrega es el 19 de octubre y la sustentación será el 20 de octubre en horas de clase.
- Deberán aplicar los conceptos vistos en clase: diseño del modelo entidad-relación; creación de tablas y relaciones; uso de claves primarias y foráneas; restricciones de integridad; consultas SQL; operaciones de inserción, actualización y eliminación de datos.

### Objetivo
Afianzar los conocimientos de diseño y modelamiento de bases de datos relacionales a través de la implementación de un sistema de información apoyado con un motor de base de datos relacional.

### Instrucciones
1. Descargar el software de desarrollo: Python (con Flask o Django) o JavaScript (Node.js con Express).
2. Ubicar el driver de la base de datos según el motor elegido (SQLite, MySQL, PostgreSQL, MariaDB o SQL Server, con su herramienta gráfica correspondiente).
3. Anexar a la actividad: diagrama entidad-relación (MER), diagrama relacional, script de creación de tablas e insert de datos básicos para que la aplicación funcione, y archivos para ejecución de la aplicación.

Importante: los archivos solo debe enviarlos el líder del grupo, relacionando a todos los integrantes.

### Enunciado
La biblioteca de la universidad necesita modernizar y digitalizar el proceso de préstamo y devolución de libros, ya que actualmente se realiza de forma manual (o con herramientas dispersas). Se requiere desarrollar una aplicación que permita:

**1. Gestión del catálogo de libros**
- Libros (títulos): ISBN, título, autor(es), editorial, año, categoría/temas, descripción.
- Ejemplares físicos por libro: código de barras/ID, ubicación (sala/estante), estado (disponible, prestado, perdido).
- Búsqueda por: título, autor, ISBN, categoría y disponibilidad.

**2. Gestión de usuarios**
- Registrar usuarios con datos mínimos: código, identificación, nombres, correo, rol (estudiante/docente), carrera (opcional), estado (activo/bloqueado).
- Consultar historial de préstamos por usuario.

**3. Gestión de préstamos**
- Registrar un préstamo asociando: usuario + ejemplar + fecha de préstamo + fecha de vencimiento.
- Validar antes de prestar: que el usuario esté activo y que el ejemplar esté disponible.

**4. Gestión de devolución**
- Registrar la devolución de un ejemplar y actualizar su estado a disponible.
- Si existe retraso, calcular automáticamente sanción/multa.
- Registrar observaciones del ejemplar al devolver: "dañado", "páginas faltantes".

**5. Reportes y consultas** (para el personal bibliotecario)
- Préstamos activos y vencidos.
- Libros más prestados por periodo.
- Usuarios con más préstamos.
- Inventario por estado (disponibles, prestados, perdidos).

**Restricciones**
- Un libro puede tener varios ejemplares y puede tener varios autores.
- El ejemplar debe indicar si está disponible, prestado o perdido.
- Un usuario puede prestar varios libros.
- Definir una tarifa de multa por día.
- Crear las operaciones CRUD para los libros, los ejemplares y los usuarios.
- Debe existir un usuario administrador o bibliotecario que se encargará de aprobar el préstamo y la devolución del libro.
- El usuario busca el libro y solicita el préstamo, el cual debe ser aprobado por el administrador.

---

## 3. Roles

| Rol | Quién es | Qué puede hacer |
|---|---|---|
| **Estudiante / Docente** | Lector. Tiene cuenta creada por el bibliotecario. | Buscar en el catálogo, ver el detalle de un libro, solicitar préstamos, ver su historial y sus multas. No puede crear, editar ni borrar nada. |
| **Bibliotecario (administrador)** | Personal de la biblioteca. | Todo lo del lector, más: gestionar libros, ejemplares, autores y usuarios; aprobar o rechazar solicitudes; registrar devoluciones y pérdidas; cambiar la tarifa de multa; ver el dashboard y los reportes. |

Al iniciar sesión, la app redirige según el rol: el bibliotecario va al **Dashboard** y el lector al **Catálogo**. Si un lector intenta abrir una página de bibliotecario, vuelve al catálogo con el aviso "Acceso restringido".

No existe registro público: los usuarios los crea el bibliotecario.

---

## 4. Navegación actual

### Barra superior (fija, translúcida, con desenfoque)
- **Izquierda:** logo/marca "Biblioteca Universitaria" (lleva al inicio).
- **Enlaces visibles según rol:**
  - Bibliotecario: "Dashboard".
  - Todos: "Catálogo".
  - Todos los que tienen perfil: "Mis Préstamos".
  - Bibliotecario: menú desplegable **"Gestión"** con: Usuarios, Préstamos, Autores, Tarifa de multa, (separador), Préstamos Activos, Libros más prestados, Lectores más activos, Inventario.
- **Derecha:** "píldora" con el nombre del usuario y una etiqueta con su rol (enlaza a Mis Préstamos) e ícono de cerrar sesión. Si no hay sesión: botón "Iniciar sesión".

### Mensajes del sistema
Debajo de la barra aparecen alertas de Bootstrap (éxito en verde, error en rojo, advertencia en ámbar, información en azul), con botón para cerrarlas. Se muestran una vez después de cada acción.

### Pie de página
"Biblioteca Universitaria — Catálogo & Préstamos" y "Bases de Datos © 2026".

---

## 5. Inventario de pantallas

Para cada pantalla: ruta, quién la usa, qué muestra, qué acciones tiene y cómo se ve hoy. "Estilo editorial" significa que usa el diseño personalizado (tipografía serif, encabezado con subtítulo en mayúsculas, tarjetas suaves). "Estilo plano" significa que usa Bootstrap casi sin personalizar; son las pantallas que más desentonan.

### 5.1 Acceso

**Iniciar sesión** — `/login/` — Todos
- Tarjeta centrada: título "Acceso a Biblioteca", texto "Ingresa tus credenciales para acceder a tus préstamos y catálogo", campos Usuario y Contraseña, botón de ingresar.
- Estilo editorial.

### 5.2 Catálogo (lector y bibliotecario)

**Catálogo de libros** — `/catalogos/libros/`
- Encabezado editorial "Catálogo de Libros".
- Barra de filtros: buscador de texto (título, autor o ISBN), selector de categoría ("Todas las categorías"), selector de disponibilidad ("Todos" / "Disponibles") y botón "Filtrar".
- Grilla de tarjetas de libro: portada (o marcador si no tiene), etiqueta de categoría, título (recortado a 48 caracteres), autores y disponibilidad ("X Disponibles" o "Agotado").
- Bibliotecario: botón para crear un libro nuevo.
- Estado vacío: "No se encontraron libros".
- Sin paginación.

**Detalle del libro** — `/catalogos/libros/<id>/`
- Ruta de navegación (Catálogo > título).
- Columna izquierda: portada grande.
- Columna derecha: título, "Por" autores, ISBN, editorial, año, disponibilidad ("X disponibles" o "No disponible"), sinopsis/descripción.
- Bibliotecario: botones Editar y Eliminar libro, y "Agregar ejemplar".
- Tabla "Ejemplares Físicos en Biblioteca": código de barras, ubicación (sala/estante), estado (etiqueta de color) y acciones:
  - Lector: botón "Solicitar" en los ejemplares disponibles.
  - Bibliotecario: "Devolver" (si está prestado), Editar (ícono de lápiz) y Eliminar (ícono de papelera).
- Estilo editorial.

**Crear / editar libro** — `/catalogos/libros/nuevo/` y `/catalogos/libros/<id>/editar/` — Bibliotecario
- Campos: ISBN, título, autores (selección múltiple), editorial, año de publicación, categoría, descripción, portada (imagen). Al editar se muestra la portada actual.
- Debajo de autores: enlace "Crear nuevo autor" (abre otra pestaña; luego hay que recargar el formulario).
- Estilo plano.

**Eliminar libro** — `/catalogos/libros/<id>/eliminar/` — Bibliotecario
- Confirmación con advertencia de que también se borran sus ejemplares.
- Si algún ejemplar tiene préstamos, no se borra y aparece el mensaje "No se puede eliminar ... porque sus ejemplares tienen préstamos registrados. Esto protege el historial."
- Estilo plano.

**Crear / editar ejemplar** — `/catalogos/libros/<id>/ejemplares/nuevo/` y `/catalogos/ejemplares/<id>/editar/` — Bibliotecario
- Campos: código de barras, ubicación (ejemplo "Sala A / Estante 3"), estado, notas, fecha de adquisición.
- Estilo plano.

**Eliminar ejemplar** — `/catalogos/ejemplares/<id>/eliminar/` — Bibliotecario
- Confirmación con código, libro, ubicación y estado. Si tiene préstamos, no se borra y se sugiere marcarlo como perdido.
- Estilo plano.

**Autores** — `/catalogos/autores/` — Lista para todos; crear solo el bibliotecario
- Tabla: apellido, nombre, número de libros. Botón "Nuevo autor".
- **Nuevo autor** — `/catalogos/autores/nuevo/`: nombre, apellido, biografía.
- Estilo plano.

**Categorías:** hoy **no tienen pantalla** en la app; solo se gestionan desde el panel automático de Django (`/admin/`). Es un pendiente que el rediseño debería contemplar (lista y formulario simple: nombre y descripción).

### 5.3 Préstamos

**Solicitar préstamo** — `/prestamos/solicitar/<id_ejemplar>/` — Lector
- Pantalla "Solicitar Préstamo": "¿Confirmas la solicitud del préstamo para el siguiente ejemplar?", con libro, código, ubicación y estado, el aviso "La solicitud será revisada y aprobada por el bibliotecario" y los botones "Sí, solicitar" y "Cancelar".
- Validaciones con mensaje: el ejemplar debe estar disponible; el usuario debe estar activo; no puede tener ya una solicitud o préstamo de ese ejemplar.
- Al confirmar: "Solicitud de préstamo enviada. Espera la aprobación del bibliotecario." y lleva a Mis Préstamos.
- Estilo plano.

**Gestión de préstamos** — `/prestamos/` — Bibliotecario
- Encabezado editorial "Gestión de Préstamos".
- Filtro por estado: Todos, Pendiente de aprobación, Activo, Vencido, Devuelto, Rechazado, Perdido.
- Tabla: número, usuario, obra/ejemplar, fecha de solicitud, vencimiento (en rojo si está vencido), estado y acciones (ver detalle, aprobar y rechazar si está pendiente, devolver si está activo o vencido).
- Estilo editorial.

**Detalle del préstamo** — `/prestamos/<id>/` — Bibliotecario, o el lector dueño del préstamo
- Datos: usuario, libro, ejemplar, fecha de solicitud, fecha de préstamo, vencimiento, estado, aprobado por.
- Panel lateral que cambia según el estado:
  - Pendiente: botones Aprobar y Rechazar (bibliotecario).
  - Activo o vencido: "Préstamo en Curso", alerta de multa acumulada si hay retraso, botones "Registrar Devolución" y "Reportar pérdida".
  - Devuelto: "Devolución Registrada" con fecha, estado del libro (observación), monto de multa y si fue pagada. Indica el estado actual del ejemplar (disponible o en mantenimiento).
  - Perdido: "Pérdida Registrada" con fecha del reporte y multa.
- Estilo editorial.

**Aprobar préstamo** — `/prestamos/<id>/aprobar/` — Bibliotecario
- Resumen (usuario, libro, ejemplar, fecha de solicitud) y campo **fecha de vencimiento** (por defecto hoy + 15 días; mínimo mañana, máximo 60 días). La fecha de préstamo es hoy.
- Validaciones: el ejemplar debe seguir disponible y el usuario debe seguir activo.
- Estilo plano.

**Rechazar préstamo** — `/prestamos/<id>/rechazar/` — Bibliotecario
- Confirmación simple.
- Estilo plano.

**Registrar devolución** — `/prestamos/<id>/devolver/` — Bibliotecario
- Ficha resumen: lector, ejemplar, vencimiento y cálculo de mora ("$X de multa acumulada" o "Sin mora").
- Campos: fecha de devolución, observación (sin observaciones, en buen estado, dañado, páginas faltantes, otro), detalle de la observación, multa pagada (casilla).
- Regla: con "dañado" o "páginas faltantes" el ejemplar queda **en mantenimiento**; en otro caso queda **disponible**. La multa se calcula sola: días de retraso por tarifa vigente.
- Estilo editorial.

**Reportar pérdida** — `/prestamos/<id>/perdida/` — Bibliotecario
- Confirmación: explica que el préstamo y el ejemplar quedarán como perdidos y muestra la multa por mora que se registrará.
- Estilo plano, con encabezado rojo.

**Tarifa de multa** — `/prestamos/multa/` — Bibliotecario
- Tarjeta con la tarifa vigente (por ejemplo "$500,00 por día, desde el 09/10/2026").
- Formulario para definir una nueva tarifa (mayor que cero).
- Tabla de historial de tarifas (vigente / anterior).
- Estilo plano.

### 5.4 Usuarios

**Mis Préstamos** — `/usuarios/mi-historial/` — Lector (y bibliotecario con perfil)
- Encabezado editorial "Mis Préstamos & Solicitudes".
- Tabla "Historial Completo": número, libro, ejemplar, fecha de solicitud, vencimiento (en rojo si vencido), estado y multa (pagada, pendiente o mora acumulada).
- Estilo editorial.

**Usuarios** — `/usuarios/` — Bibliotecario
- Botón "Nuevo Usuario".
- Tabla: nombre, código, correo, rol, estado (activo/bloqueado), préstamos activos y acciones (editar, eliminar).
- Sin buscador ni paginación.
- Estilo plano.

**Detalle de usuario** — `/usuarios/<id>/` — Bibliotecario
- Tarjeta con código, identificación, correo, rol, carrera, estado y botón Editar.
- Tabla con su historial de préstamos: libro, fecha, estado, multa.
- Estilo plano.

**Crear usuario** — `/usuarios/nuevo/` — Bibliotecario
- Campos: nombres, apellidos, correo, usuario, contraseña, código universitario, identificación, rol (estudiante, docente, bibliotecario), carrera, estado (activo/bloqueado), teléfono.
- Validaciones: correo, usuario, código e identificación únicos; contraseña segura (mínimo 8 caracteres, no común, no solo números, no parecida al usuario).
- Estilo plano.

**Editar usuario** — `/usuarios/<id>/editar/` — Bibliotecario
- Los mismos datos más "Nueva contraseña" (opcional; vacía conserva la actual).
- Protecciones: el bibliotecario no puede bloquearse, quitarse el rol de bibliotecario ni eliminarse a sí mismo.
- Estilo plano.

**Eliminar usuario** — `/usuarios/<id>/eliminar/` — Bibliotecario
- Confirmación. Si tiene préstamos, no se borra y se sugiere bloquearlo.
- Estilo plano.

### 5.5 Dashboard y reportes (bibliotecario)

**Dashboard** — `/reportes/`
- Encabezado editorial "Métricas & Operaciones".
- Fila de 4 indicadores (KPI): Títulos en catálogo, Copias disponibles, Ejemplares prestados, Préstamos en mora.
- Segunda fila de 3 tarjetas con acceso directo: Solicitudes en espera (lleva a préstamos pendientes), Usuarios registrados, Copias reportadas perdidas (lleva a inventario).
- Tabla "Últimos Movimientos de Préstamos" (10 más recientes): número, usuario, libro, fecha de solicitud, estado y enlace al detalle.
- Estilo editorial.

**Préstamos activos y vencidos** — `/reportes/prestamos-activos/`
- Tabla ordenada por vencimiento: usuario, libro, fechas, estado, días de mora y multa estimada. Las filas vencidas se resaltan en rojo.
- Estilo editorial.

**Libros más prestados** — `/reportes/libros-mas-prestados/`
- Filtro de periodo con campos Desde y Hasta, y atajos: últimos 7, 30 y 90 días, último año. Por defecto los últimos 30 días.
- Ranking (top 20): posición (1, 2 y 3 con medallas de color), portada, título y autores, categoría, ejemplares disponibles, total de préstamos y botón "Ver obra".
- Estilo editorial.

**Usuarios con más préstamos** — `/reportes/usuarios-mas-prestamos/`
- Mismo filtro de fechas, más el atajo "Histórico" (por defecto: histórico total).
- Ranking (top 20): posición, nombre y correo, código, rol, estado, total de préstamos y desglose en activos, vencidos (en rojo), devueltos y perdidos. Botón "Ver historial".
- Solo cuenta préstamos aprobados (no pendientes ni rechazados).
- Estilo editorial.

**Inventario por estado** — `/reportes/inventario/`
- Encabezado "Auditoría de Fondos / Inventario por Estado".
- Una sección por estado (disponible, prestado, perdido, en mantenimiento) con el conteo de copias y una tabla: código de barras, título, ubicación y enlace a la ficha.
- Estilo editorial.

---

## 6. Flujos principales

**Ciclo de un préstamo**
```
Lector solicita  ->  PENDIENTE
                       |-- bibliotecario rechaza  ->  RECHAZADO
                       '-- bibliotecario aprueba (elige vencimiento)  ->  ACTIVO      (ejemplar: prestado)
                                                                          |-- pasa la fecha  ->  VENCIDO (acumula multa)
                                                                          |-- devolución     ->  DEVUELTO (ejemplar: disponible o en mantenimiento)
                                                                          '-- pérdida        ->  PERDIDO  (ejemplar: perdido)
```

**Recorrido típico del lector:** Iniciar sesión, buscar en el Catálogo, abrir el libro, elegir un ejemplar disponible y pulsar "Solicitar", confirmar, y esperar la aprobación revisando "Mis Préstamos".

**Recorrido típico del bibliotecario:** Dashboard, ver "Solicitudes en espera", abrir la lista de préstamos pendientes, aprobar (elegir vencimiento) o rechazar; cuando el lector trae el libro, buscar el préstamo y registrar la devolución con la observación; revisar reportes.

**Multas:** se calculan solas al registrar la devolución o la pérdida (días de retraso por tarifa vigente ese día). La tarifa se cambia en "Tarifa de multa" y queda historial. Las multas ya registradas no cambian.

---

## 7. Estados y su representación visual actual

| Entidad | Estado | Etiqueta actual |
|---|---|---|
| Ejemplar | Disponible | Verde |
| Ejemplar | Prestado | Ámbar |
| Ejemplar | Perdido | Rojo arcilla |
| Ejemplar | En mantenimiento | Gris |
| Préstamo | Pendiente | Ámbar |
| Préstamo | Activo | Verde |
| Préstamo | Vencido | Rojo arcilla |
| Préstamo | Devuelto | Gris |
| Préstamo | Rechazado | Rojo arcilla (igual que vencido) |
| Préstamo | Perdido | Rojo arcilla |
| Usuario | Activo / Bloqueado | Verde / Rojo |

Observación: varios estados distintos comparten el mismo color (rechazado, vencido y perdido), lo que reduce la claridad.

---

## 8. Diseño visual actual

**Concepto declarado en el CSS:** "Diseño editorial moderno", paleta cálida, minimalismo botánico y tipografía refinada.

**Tipografía**
- Títulos: Playfair Display (serif), peso 600.
- Texto: Plus Jakarta Sans (sans serif).

**Paleta (variables CSS en `:root`)**
| Uso | Color |
|---|---|
| Fondo (papel lino) | `#FAF7F2` |
| Superficie / tarjetas | `#FFFFFF` |
| Superficie suave | `#F5EFE6` |
| Bordes | `#E8E2D7` |
| Texto principal | `#23201D` |
| Texto secundario | `#6F6961` |
| Acento principal (verde bosque) | `#2B3A2C` |
| Acento secundario (terracota) | `#B86B49` |
| Ámbar | `#8A641E` |
| Rojo arcilla | `#963527` |

**Otros elementos:** sombras muy suaves, radios de 8, 14 y 20 px, botones con forma de píldora, barra superior translúcida con desenfoque, tarjetas KPI con ícono en círculo de color, etiquetas de estado redondeadas.

**Componentes personalizados existentes:** tarjeta de libro (portada, categoría, título, autor), etiquetas de estado, tarjetas KPI, píldora de usuario, botones "forest" y "terracotta", tarjeta de filtros, tablas suaves, alertas recoloreadas.

**No hay modo oscuro.**

---

## 9. Problemas de usabilidad y estética detectados

1. **Dos estilos mezclados:** unas pantallas tienen el diseño editorial y otras (usuarios, formularios, confirmaciones, autores, tarifa, aprobar/rechazar) son Bootstrap casi sin personalizar. La app se siente inconsistente.
2. **Toda la gestión está escondida en un único menú desplegable "Gestión"** con 8 opciones mezcladas (administración y reportes). Para el bibliotecario, que trabaja todo el día en la app, una navegación lateral o por secciones sería más directa.
3. **La tarea más frecuente del bibliotecario (aprobar solicitudes pendientes) requiere varios clics:** Dashboard, luego la lista filtrada, luego el detalle o la pantalla de aprobar. No hay una bandeja de pendientes con acción directa.
4. **Registrar una devolución obliga a encontrar el préstamo** navegando por listas. No hay búsqueda por código de barras del ejemplar ni por usuario en la lista de préstamos.
5. **Muchas acciones son solo íconos** (lápiz, papelera) sin texto; poco claros y pequeños en celular.
6. **Crear un autor desde el formulario del libro** abre otra pestaña y obliga a recargar.
7. **Categorías sin pantalla propia** (solo en `/admin/`).
8. **Listas sin buscador ni paginación** (usuarios, autores, préstamos, catálogo). Funciona con pocos datos, pero no escala.
9. **Tablas anchas** (préstamos, reportes) que en celular obligan a desplazarse de lado.
10. **Colores de estado repetidos** (rechazado, vencido y perdido se ven iguales).
11. **"Mis Préstamos" aparece dos veces** en la barra (enlace y píldora de usuario).
12. **Cerrar sesión es solo un ícono** sin texto.
13. **Las confirmaciones destructivas** (eliminar, rechazar, pérdida) son páginas completas; podrían ser diálogos o tener un diseño unificado.
14. **El lector no ve de un vistazo su situación:** cuántos préstamos tiene activos, cuál vence pronto y si debe multas.

---

## 10. Qué se pide para el rediseño

Proponer una nueva estructura de interfaz que:

1. **Conserve todas las funcionalidades** descritas en las secciones 5 y 6, y respete las restricciones técnicas de la sección 1.
2. **Organice la navegación por rol:**
   - Lector: catálogo, detalle del libro, solicitar y mis préstamos.
   - Bibliotecario: operación diaria (solicitudes pendientes, préstamos en curso, devoluciones), catálogo (libros, ejemplares, autores, categorías), usuarios, reportes y configuración (tarifa).
3. **Unifique el sistema visual:** un solo estilo para todas las pantallas, con componentes reutilizables (encabezado de página, tarjeta, tabla, formulario, confirmación, etiqueta de estado, estado vacío, filtros).
4. **Reduzca clics en las tareas frecuentes** (aprobar, devolver, buscar un ejemplar o un usuario).
5. **Funcione bien en celular**, en especial las pantallas del lector.
6. **Use colores de estado distintos y coherentes** para ejemplares, préstamos y usuarios.

Entregables esperados del rediseño:
- Mapa de navegación (estructura de menús por rol).
- Disposición (layout) de cada pantalla, indicando qué va dónde.
- Sistema de componentes y guía visual (tipografía, paleta, espaciados, estados).
- Después de aprobar la estructura: el detalle visual para implementarlo con Bootstrap 5.3 y CSS propio en las plantillas Django.
