/* Comportamientos mínimos de la interfaz. Sin dependencias; la app funciona igual si este archivo no carga. */
(function () {
    'use strict';

    // Botón en espera: un librito que pasa sus páginas mientras el servidor responde
    function marcarCargando(boton, activo) {
        boton.classList.toggle('is-cargando', activo);
        if (activo) {
            boton.setAttribute('aria-busy', 'true');
            if (!boton.querySelector('.libro-carga')) {
                boton.insertAdjacentHTML('afterbegin', '<span class="libro-carga" aria-hidden="true"><i></i><i></i><i></i></span>');
            }
        } else {
            boton.removeAttribute('aria-busy');
            var libro = boton.querySelector('.libro-carga');
            if (libro) libro.remove();
        }
    }

    // Cerrar avisos del sistema
    document.addEventListener('click', function (e) {
        var boton = e.target.closest('[data-cerrar-aviso]');
        if (boton) {
            var aviso = boton.closest('.aviso');
            if (aviso) aviso.remove();
        }
    });

    // Menú de la barra superior en celular (lector)
    var alternar = document.querySelector('[data-alternar-barra]');
    if (alternar) {
        alternar.addEventListener('click', function () {
            var barra = document.getElementById('barra');
            var abierta = barra.classList.toggle('abierta');
            alternar.setAttribute('aria-expanded', abierta ? 'true' : 'false');
        });
    }
    // Mostrar u ocultar la contraseña (login)
    document.addEventListener('click', function (e) {
        var boton = e.target.closest('[data-ver-clave]');
        if (!boton) return;
        var campo = document.getElementById(boton.getAttribute('data-ver-clave'));
        if (!campo) return;
        var visible = campo.type === 'password';
        campo.type = visible ? 'text' : 'password';
        boton.setAttribute('aria-pressed', visible ? 'true' : 'false');
        boton.setAttribute('aria-label', visible ? 'Ocultar contraseña' : 'Mostrar contraseña');
        var icono = boton.querySelector('.bi');
        if (icono) icono.className = 'bi ' + (visible ? 'bi-eye-slash' : 'bi-eye');
    });
    var movimientoReducido = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    // Parallax sutil de la foto de portada (inicio del lector)
    var foto = document.querySelector('[data-parallax] img');
    if (foto && !movimientoReducido) {
        var pendiente = false;
        var mover = function () {
            pendiente = false;
            var y = window.scrollY;
            if (y < window.innerHeight) foto.style.setProperty('--paralaje', (y * 0.32).toFixed(1) + 'px');
        };
        window.addEventListener('scroll', function () {
            if (!pendiente) { pendiente = true; window.requestAnimationFrame(mover); }
        }, { passive: true });
    }

    // Indicadores de la ficha de lector: abrir/cerrar con clic o toque; Escape y clic afuera cierran
    var botonesIndicador = document.querySelectorAll('.indicador__boton');
    var cerrarIndicadores = function (excepto) {
        botonesIndicador.forEach(function (b) { if (b !== excepto) b.setAttribute('aria-expanded', 'false'); });
    };
    botonesIndicador.forEach(function (boton) {
        boton.addEventListener('click', function (e) {
            e.stopPropagation();
            var abierto = boton.getAttribute('aria-expanded') === 'true';
            cerrarIndicadores(boton);
            boton.setAttribute('aria-expanded', abierto ? 'false' : 'true');
        });
    });
    if (botonesIndicador.length) {
        document.addEventListener('click', function () { cerrarIndicadores(null); });
        document.addEventListener('keydown', function (e) { if (e.key === 'Escape') cerrarIndicadores(null); });
    }

    // Aparición de bloques al entrar en pantalla
    var revelables = document.querySelectorAll('.revelar');
    if (revelables.length) {
        if (!('IntersectionObserver' in window) || movimientoReducido) {
            revelables.forEach(function (el) { el.classList.add('visible'); });
        } else {
            var observador = new IntersectionObserver(function (entradas) {
                entradas.forEach(function (entrada) {
                    if (entrada.isIntersecting) { entrada.target.classList.add('visible'); observador.unobserve(entrada.target); }
                });
            }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
            revelables.forEach(function (el) { observador.observe(el); });
        }
    }
    // Selector de autores del formulario del libro: buscar, ver elegidos y agregar uno nuevo sin salir
    var selector = document.querySelector('[data-selector-autores]');
    if (selector) {
        var lista = selector.querySelector('[data-lista-autores]');
        var elegidos = selector.querySelector('[data-elegidos]');
        var ninguno = selector.querySelector('[data-ninguno]');
        var filtro = selector.querySelector('[data-filtro-autores]');
        var sinResultados = selector.querySelector('[data-sin-resultados]');

        var pintarElegidos = function () {
            elegidos.querySelectorAll('.etiqueta-autor').forEach(function (e) { e.remove(); });
            var marcados = lista.querySelectorAll('input[type=checkbox]:checked');
            ninguno.hidden = marcados.length > 0;
            marcados.forEach(function (casilla) {
                var etiqueta = document.createElement('span');
                etiqueta.className = 'etiqueta-autor';
                etiqueta.textContent = casilla.parentElement.querySelector('span').textContent;
                var quitar = document.createElement('button');
                quitar.type = 'button';
                quitar.setAttribute('aria-label', 'Quitar ' + etiqueta.textContent);
                quitar.innerHTML = '<i class="bi bi-x" aria-hidden="true"></i>';
                quitar.addEventListener('click', function () { casilla.checked = false; pintarElegidos(); });
                etiqueta.appendChild(quitar);
                elegidos.appendChild(etiqueta);
            });
        };
        lista.addEventListener('change', pintarElegidos);
        pintarElegidos();

        var normalizar = function (t) { return t.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase(); };
        filtro.addEventListener('input', function () {
            var q = normalizar(filtro.value.trim()), visibles = 0;
            lista.querySelectorAll('.selector-autores__opcion').forEach(function (op) {
                var ver = !q || normalizar(op.textContent).indexOf(q) !== -1;
                op.hidden = !ver;
                if (ver) visibles++;
            });
            sinResultados.hidden = visibles > 0;
        });
        filtro.addEventListener('keydown', function (e) { if (e.key === 'Enter') e.preventDefault(); });

        var nuevo = selector.querySelector('[data-nuevo-autor]');
        var campoNombre = nuevo.querySelector('[data-nuevo-nombre]');
        var campoApellido = nuevo.querySelector('[data-nuevo-apellido]');
        var mensaje = nuevo.querySelector('[data-mensaje-autor]');
        var boton = nuevo.querySelector('[data-crear-autor]');
        var csrf = selector.closest('form').querySelector('[name=csrfmiddlewaretoken]').value;

        var crearAutor = function () {
            var datos = new FormData();
            datos.append('nombre', campoNombre.value.trim());
            datos.append('apellido', campoApellido.value.trim());
            datos.append('biografia', '');
            boton.disabled = true;
            marcarCargando(boton, true);
            mensaje.className = 'selector-autores__mensaje';
            mensaje.textContent = 'Guardando…';
            fetch(nuevo.getAttribute('data-url'), {
                method: 'POST', body: datos, credentials: 'same-origin',
                headers: { 'X-CSRFToken': csrf, 'X-Requested-With': 'XMLHttpRequest' }
            }).then(function (r) { return r.json().then(function (j) { return { ok: r.ok, datos: j }; }); })
              .then(function (res) {
                if (!res.ok) {
                    var errores = res.datos.errores || {};
                    mensaje.classList.add('es-error');
                    mensaje.textContent = 'Revisa los datos: ' + Object.keys(errores).map(function (c) { return c + ' (' + errores[c].join(' ') + ')'; }).join('; ');
                    return;
                }
                var a = res.datos;
                var casilla = lista.querySelector('input[value="' + a.id + '"]');
                if (!casilla) {
                    var opcion = document.createElement('label');
                    opcion.className = 'selector-autores__opcion es-nuevo';
                    casilla = document.createElement('input');
                    casilla.type = 'checkbox'; casilla.name = 'autores'; casilla.value = a.id;
                    casilla.className = 'form-check-input'; casilla.id = 'id_autores_nuevo_' + a.id;
                    opcion.setAttribute('for', casilla.id);
                    var texto = document.createElement('span'); texto.textContent = a.texto;
                    opcion.appendChild(casilla); opcion.appendChild(texto);
                    lista.prepend(opcion);
                }
                casilla.checked = true;
                pintarElegidos();
                mensaje.textContent = a.existente ? '«' + a.texto + '» ya existía: quedó seleccionado.' : '«' + a.texto + '» se agregó y quedó seleccionado.';
                campoNombre.value = ''; campoApellido.value = '';
            }).catch(function () {
                mensaje.classList.add('es-error');
                mensaje.textContent = 'No se pudo guardar el autor. Revisa tu conexión e inténtalo de nuevo.';
            }).finally(function () { boton.disabled = false; marcarCargando(boton, false); });
        };
        boton.addEventListener('click', crearAutor);
        [campoNombre, campoApellido].forEach(function (c) {
            c.addEventListener('keydown', function (e) { if (e.key === 'Enter') { e.preventDefault(); crearAutor(); } });
        });
    }

    // Avisar antes de salir de un formulario con cambios sin guardar.
    // Compara el contenido actual con el que tenía al abrirse; si el formulario volvió con errores,
    // lo escrito aún no está guardado, así que también avisa.
    document.querySelectorAll('form[data-avisar-cambios]').forEach(function (form) {
        var huella = function () {
            var partes = [];
            new FormData(form).forEach(function (valor, nombre) {
                if (nombre === 'csrfmiddlewaretoken') return;
                partes.push(nombre + '=' + (typeof valor === 'string' ? valor : valor.name + ':' + valor.size));
            });
            return partes.join('&');
        };
        var inicial = form.querySelector('.invalid-feedback, .aviso--error') ? null : huella();
        var enviando = false;
        form.addEventListener('submit', function () { enviando = true; });
        window.addEventListener('beforeunload', function (e) {
            if (enviando || huella() === inicial) return;
            e.preventDefault();
            e.returnValue = '';  // el navegador muestra su propio mensaje de confirmación
        });
    });

    // Formularios que guardan (POST): animación en el botón y sin doble envío.
    // Cerrar sesión es instantáneo y se excluye; data-sin-carga permite excluir otros.
    document.addEventListener('submit', function (e) {
        var form = e.target;
        if (e.defaultPrevented || (form.method || '').toLowerCase() !== 'post' || form.matches('.form-salir, [data-sin-carga]')) return;
        if (form.dataset.enviando) { e.preventDefault(); return; }
        form.dataset.enviando = '1';
        var boton = e.submitter || form.querySelector('[type=submit]');
        if (boton) marcarCargando(boton, true);
    });
    // Al volver con «Atrás» el navegador puede restaurar la página tal cual: se reactivan los botones
    window.addEventListener('pageshow', function (e) {
        if (!e.persisted) return;
        document.querySelectorAll('form[data-enviando]').forEach(function (f) { delete f.dataset.enviando; });
        document.querySelectorAll('.is-cargando').forEach(function (b) { marcarCargando(b, false); });
    });

    // Devolución: la multa se recalcula con la fecha elegida y la casilla de pago solo aparece si hay multa
    var panelMulta = document.querySelector('[data-multa-estimada]');
    var campoFecha = document.getElementById('id_fecha_devolucion');
    if (panelMulta && campoFecha) {
        var campoPago = document.querySelector('[data-campo-pago]');
        var vencimiento = new Date(panelMulta.dataset.vencimiento + 'T00:00:00');
        var tarifa = parseFloat(panelMulta.dataset.tarifa) || 0;
        var pesos = new Intl.NumberFormat('es-CO', { maximumFractionDigits: 0 });
        var hoy = new Date(); hoy.setHours(0, 0, 0, 0);
        var recalcular = function () {
            if (!campoFecha.value) return;
            var fecha = new Date(campoFecha.value + 'T00:00:00');
            var dias = Math.max(0, Math.round((fecha - vencimiento) / 86400000));
            var monto = dias * tarifa;
            panelMulta.querySelector('[data-multa-titulo]').textContent =
                fecha.getTime() === hoy.getTime() ? 'Multa si se devuelve hoy' : 'Multa con la fecha elegida';
            panelMulta.querySelector('[data-multa-monto]').textContent = '$' + pesos.format(monto);
            panelMulta.querySelector('[data-multa-detalle]').textContent = monto > 0
                ? dias + ' día' + (dias > 1 ? 's' : '') + ' de retraso × $' + pesos.format(tarifa) + ' por día'
                : 'Entrega a tiempo';
            panelMulta.classList.toggle('multa-estimada--mora', monto > 0);
            if (campoPago) {
                campoPago.hidden = monto <= 0;
                if (monto <= 0) campoPago.querySelector('input').checked = false;
            }
        };
        campoFecha.addEventListener('change', recalcular);
        campoFecha.addEventListener('input', recalcular);
        recalcular();
    }
})();
