/* Comportamientos mínimos de la interfaz. Sin dependencias; la app funciona igual si este archivo no carga. */
(function () {
    'use strict';

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
})();
