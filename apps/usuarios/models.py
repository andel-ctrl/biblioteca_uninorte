from django.db import models
from django.contrib.auth.models import User


class Usuario(models.Model):
    """Supertipo de la especialización: lo que comparten todos los usuarios de la biblioteca.

    Especialización TOTAL y DISJUNTA: cada usuario es exactamente un Lector o un Bibliotecario
    (nunca ambos, nunca ninguno). La columna «tipo» es el discriminador.
    Lo DISJUNTO lo garantiza la base: cada subtipo guarda su tipo fijo y su llave foránea
    apunta al par (id, tipo) del usuario, así un usuario solo cabe en el subtipo de su tipo.
    Lo TOTAL lo garantiza la aplicación (crea las dos filas en una sola transacción).
    La cuenta de acceso (usuario, contraseña, nombres y correo) es la tabla auth_user de Django.
    """
    TIPO_CHOICES = [
        ('lector', 'Lector'),
        ('bibliotecario', 'Bibliotecario'),
    ]
    ESTADO_CHOICES = [
        ('activo', 'Activo'),
        ('bloqueado', 'Bloqueado'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    codigo_universitario = models.CharField(max_length=20, unique=True, verbose_name='Código universitario')
    identificacion = models.CharField(max_length=20, unique=True, verbose_name='Número de identificación')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='lector')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='activo')
    telefono = models.CharField(max_length=20, blank=True, verbose_name='Teléfono')
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'usuario'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        constraints = [
            # El par (id, tipo) es único: los subtipos lo referencian con su llave foránea compuesta
            models.UniqueConstraint(fields=['id', 'tipo'], name='usuario_id_tipo_key'),
            models.CheckConstraint(condition=models.Q(tipo__in=['lector', 'bibliotecario']), name='usuario_tipo_valido',
                violation_error_message='El tipo de usuario no es válido.'),
            models.CheckConstraint(condition=models.Q(estado__in=['activo', 'bloqueado']), name='usuario_estado_valido',
                violation_error_message='El estado de la cuenta no es válido.'),
        ]

    def __str__(self):
        return f"{self.user.get_full_name()} [{self.codigo_universitario}]"

    def get_nombre_completo(self):
        return self.user.get_full_name() or self.user.username

    def esta_activo(self):
        return self.estado == 'activo'

    def es_bibliotecario(self):
        return self.tipo == 'bibliotecario'

    def es_lector(self):
        return self.tipo == 'lector'

    # --- Datos del subtipo, para mostrarlos sin preguntar de qué tipo es ---------
    @property
    def rol(self):
        """Rol para mostrar: «bibliotecario», o el rol del lector (estudiante / docente)."""
        if self.es_bibliotecario():
            return 'bibliotecario'
        lector = getattr(self, 'lector', None)
        return lector.rol if lector else ''

    def get_rol_display(self):
        if self.es_bibliotecario():
            return 'Bibliotecario'
        lector = getattr(self, 'lector', None)
        return lector.get_rol_display() if lector else ''

    @property
    def carrera(self):
        lector = getattr(self, 'lector', None)
        return lector.carrera if lector else ''

    def get_turno_display(self):
        bibliotecario = getattr(self, 'bibliotecario', None)
        return bibliotecario.get_turno_display() if bibliotecario else ''

    # --- Reglas de préstamo: solo aplican a lectores ---------------------------------
    def restriccion_solicitudes(self):
        if self.es_bibliotecario():
            return {'tipo': 'bibliotecario'}
        return self.lector.restriccion_solicitudes()

    def mensaje_restriccion(self, para_el_lector=True):
        if self.es_bibliotecario():
            return 'El personal bibliotecario no solicita préstamos: aprueba y registra los de los lectores.'
        return self.lector.mensaje_restriccion(para_el_lector)


class Lector(models.Model):
    """Subtipo: usuario que solicita préstamos. «rol» distingue estudiante y docente (discriminador)."""
    ROL_CHOICES = [
        ('estudiante', 'Estudiante'),
        ('docente', 'Docente'),
    ]

    # La llave primaria es también la referencia al supertipo. La llave foránea real es compuesta,
    # (usuario_id, tipo) → usuario (id, tipo), y se crea en la migración 0005 (Django no las declara)
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, primary_key=True, related_name='lector',
                                   db_constraint=False)
    tipo = models.CharField(max_length=20, db_default='lector', editable=False)  # siempre 'lector'
    rol = models.CharField(max_length=20, choices=ROL_CHOICES, default='estudiante')
    carrera = models.CharField(max_length=150, blank=True)

    class Meta:
        db_table = 'lector'
        verbose_name = 'Lector'
        verbose_name_plural = 'Lectores'
        constraints = [
            models.CheckConstraint(condition=models.Q(tipo='lector'), name='lector_tipo_fijo',
                violation_error_message='La tabla lector solo admite usuarios de tipo lector.'),
            models.CheckConstraint(condition=models.Q(rol__in=['estudiante', 'docente']), name='lector_rol_valido',
                violation_error_message='El rol del lector no es válido.'),
        ]

    def __str__(self):
        return str(self.usuario)

    def get_nombre_completo(self):
        return self.usuario.get_nombre_completo()

    @property
    def codigo_universitario(self):
        return self.usuario.codigo_universitario

    def esta_activo(self):
        return self.usuario.esta_activo()

    def prestamos_activos(self):
        return self.prestamos.filter(estado__in=['activo', 'vencido']).count()

    def restriccion_solicitudes(self):
        """Por qué no puede pedir libros ahora (o None si puede): cuenta bloqueada,
        préstamos vencidos sin devolver o multas sin pagar. Se pone al día y queda libre."""
        from django.db.models import Q, Sum
        from django.utils import timezone
        if not self.esta_activo():
            return {'tipo': 'bloqueada'}
        hoy = timezone.localdate()
        vencidos = self.prestamos.filter(Q(estado='vencido') | Q(estado='activo', fecha_vencimiento__lt=hoy)).count()
        if vencidos:
            return {'tipo': 'vencidos', 'n': vencidos}
        deuda = self.prestamos.filter(devolucion__multa__pagada=False).aggregate(
            total=Sum('devolucion__multa__monto'))['total']
        if deuda:
            return {'tipo': 'multas', 'monto': deuda}
        return None

    def mensaje_restriccion(self, para_el_lector=True):
        from apps.catalogos.formato import formato_pesos
        r = self.restriccion_solicitudes()
        if not r:
            return ''
        nombre = self.get_nombre_completo()
        if r['tipo'] == 'bloqueada':
            return ('Tu cuenta está bloqueada. Contacta al personal bibliotecario.' if para_el_lector
                    else f'{nombre} tiene la cuenta bloqueada.')
        if r['tipo'] == 'vencidos':
            n, s = r['n'], 's' if r['n'] > 1 else ''
            return (f'Tienes {n} préstamo{s} vencido{s}. Devuélvelo{s} para volver a solicitar libros.' if para_el_lector
                    else f'{nombre} tiene {n} préstamo{s} vencido{s} sin devolver.')
        monto = formato_pesos(r['monto'])
        return (f'Tienes {monto} en multas sin pagar. Págalas en el mostrador de la biblioteca para volver a solicitar libros.'
                if para_el_lector else f'{nombre} tiene {monto} en multas sin pagar.')


class Bibliotecario(models.Model):
    """Subtipo: personal que aprueba préstamos, registra devoluciones y cobra multas.
    Existe sobre todo por sus relaciones (las llaves foráneas de préstamo, devolución y multa
    apuntan aquí, así la base garantiza quién puede hacer qué). Su atributo propio, el turno,
    no está en el enunciado: es opcional y no cambia ninguna regla de préstamo."""
    TURNO_CHOICES = [
        ('manana', 'Mañana'),
        ('tarde', 'Tarde'),
        ('noche', 'Noche'),
    ]

    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, primary_key=True, related_name='bibliotecario',
                                   db_constraint=False)   # llave foránea compuesta: ver Lector
    tipo = models.CharField(max_length=20, db_default='bibliotecario', editable=False)  # siempre 'bibliotecario'
    turno = models.CharField(max_length=10, choices=TURNO_CHOICES, blank=True)  # vacío: sin asignar

    class Meta:
        db_table = 'bibliotecario'
        verbose_name = 'Bibliotecario'
        verbose_name_plural = 'Bibliotecarios'
        constraints = [
            models.CheckConstraint(condition=models.Q(tipo='bibliotecario'), name='bibliotecario_tipo_fijo',
                violation_error_message='La tabla bibliotecario solo admite usuarios de tipo bibliotecario.'),
            models.CheckConstraint(condition=models.Q(turno__in=['', 'manana', 'tarde', 'noche']),
                name='bibliotecario_turno_valido',
                violation_error_message='El turno debe ser mañana, tarde o noche.'),
        ]

    def __str__(self):
        return str(self.usuario)

    def get_nombre_completo(self):
        return self.usuario.get_nombre_completo()
