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
})();
