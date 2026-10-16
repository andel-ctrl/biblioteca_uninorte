"""Préstamos sobre la especialización de usuarios y multa en tabla propia.

· prestamo.lector → lector (antes usuario); aprobado_por y devolucion.registrado_por → bibliotecario.
· La multa sale de devolucion (monto_multa, multa_pagada) a la tabla multa, enlazada a la tarifa
  con la que se calculó. Solo se crea si había monto mayor que cero.
· configuracionmulta pasa a tarifa_multa (valor_dia, vigente_desde).
· Préstamos pedidos por un bibliotecario (la nueva regla no lo permite) se eliminan con su devolución.
"""
import django.db.models.deletion
from django.db import migrations, models


def convertir(apps, schema_editor):
    Prestamo = apps.get_model('prestamos', 'Prestamo')
    Devolucion = apps.get_model('prestamos', 'Devolucion')
    Multa = apps.get_model('prestamos', 'Multa')
    TarifaMulta = apps.get_model('prestamos', 'TarifaMulta')
    Bibliotecario = apps.get_model('usuarios', 'Bibliotecario')
    bibliotecarios = set(Bibliotecario.objects.values_list('pk', flat=True))

    # 1. Préstamos pedidos por bibliotecarios: ya no son válidos (especialización disjunta)
    invalidos = Prestamo.objects.filter(usuario_id__in=bibliotecarios)
    if invalidos.exists():
        print(f'\n   Se eliminan {invalidos.count()} préstamo(s) pedidos por bibliotecarios (la nueva regla no lo permite).')
        Devolucion.objects.filter(prestamo__in=invalidos).delete()
        invalidos.delete()

    # 2. El lector tiene la misma llave que su usuario; el aprobador solo se conserva si es bibliotecario
    for p in Prestamo.objects.all():
        p.lector_id = p.usuario_id
        p.aprobado_por_nuevo_id = p.aprobado_por_id if p.aprobado_por_id in bibliotecarios else None
        p.save(update_fields=['lector', 'aprobado_por_nuevo'])

    # 3. Devoluciones: quién la registró, y su multa en la tabla nueva
    for d in Devolucion.objects.all():
        d.registrado_por_nuevo_id = d.registrado_por_id if d.registrado_por_id in bibliotecarios else None
        d.save(update_fields=['registrado_por_nuevo'])
        if d.monto_multa and d.monto_multa > 0:
            tarifa = (TarifaMulta.objects.filter(vigente_desde__lte=d.fecha_devolucion).order_by('-vigente_desde', '-pk').first()
                      or TarifaMulta.objects.order_by('-vigente_desde', '-pk').first())
            Multa.objects.create(
                devolucion=d, tarifa=tarifa, monto=d.monto_multa, pagada=d.multa_pagada,
                fecha_pago=d.fecha_devolucion if d.multa_pagada else None,
                cobrada_por_id=d.registrado_por_nuevo_id if d.multa_pagada else None,
            )
    # Las llaves foráneas son diferidas: se verifican ya, para que los cambios de estructura
    # que siguen en esta migración no choquen con verificaciones pendientes de PostgreSQL
    schema_editor.execute('SET CONSTRAINTS ALL IMMEDIATE')


class Migration(migrations.Migration):

    dependencies = [
        ('prestamos', '0003_restricciones_check'),
        ('usuarios', '0003_especializacion'),
        ('catalogos', '0004_tablas_y_ubicacion'),
    ]

    operations = [
        # --- Tarifa ---------------------------------------------------------------
        migrations.RenameModel('ConfiguracionMulta', 'TarifaMulta'),
        migrations.RemoveConstraint('tarifamulta', 'tarifa_multa_positiva'),
        migrations.RenameField('tarifamulta', 'tarifa_por_dia', 'valor_dia'),
        migrations.RenameField('tarifamulta', 'vigencia_desde', 'vigente_desde'),
        migrations.AlterField('tarifamulta', 'valor_dia',
                              models.DecimalField(decimal_places=2, max_digits=8, verbose_name='Valor por día ($)')),
        migrations.AddConstraint('tarifamulta', models.CheckConstraint(
            condition=models.Q(valor_dia__gt=0), name='tarifa_multa_positiva',
            violation_error_message='La tarifa debe ser mayor que cero.')),
        migrations.AlterModelOptions('tarifamulta', options={'verbose_name': 'Tarifa de multa',
                                                             'verbose_name_plural': 'Tarifas de multa'}),

        # --- Columnas nuevas (temporales mientras se copian los datos) -------------
        migrations.AddField('prestamo', 'lector', models.ForeignKey(
            null=True, on_delete=django.db.models.deletion.PROTECT, related_name='prestamos', to='usuarios.lector')),
        migrations.AddField('prestamo', 'aprobado_por_nuevo', models.ForeignKey(
            blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
            related_name='prestamos_aprobados', to='usuarios.bibliotecario')),
        migrations.AddField('devolucion', 'registrado_por_nuevo', models.ForeignKey(
            blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
            related_name='devoluciones_registradas', to='usuarios.bibliotecario')),
        migrations.CreateModel(
            name='Multa',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('monto', models.DecimalField(decimal_places=2, max_digits=10)),
                ('pagada', models.BooleanField(default=False)),
                ('fecha_pago', models.DateField(blank=True, null=True)),
                ('cobrada_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                                                  related_name='multas_cobradas', to='usuarios.bibliotecario')),
                ('devolucion', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT,
                                                    related_name='multa', to='prestamos.devolucion')),
                ('tarifa', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,
                                             related_name='multas', to='prestamos.tarifamulta')),
            ],
            options={
                'verbose_name': 'Multa', 'verbose_name_plural': 'Multas', 'db_table': 'multa',
                'constraints': [
                    models.CheckConstraint(condition=models.Q(monto__gt=0), name='multa_monto_positivo',
                                           violation_error_message='El monto de la multa debe ser mayor que cero.'),
                    models.CheckConstraint(
                        condition=models.Q(pagada=True, fecha_pago__isnull=False) | models.Q(pagada=False, fecha_pago__isnull=True),
                        name='multa_pago_coherente',
                        violation_error_message='Una multa pagada necesita fecha de pago, y una pendiente no la tiene.'),
                ],
            },
        ),

        # --- Copia de datos ----------------------------------------------------------
        migrations.RunPython(convertir, migrations.RunPython.noop),

        # --- Se retiran las columnas viejas y las nuevas toman su nombre ---------------
        migrations.RemoveField('prestamo', 'usuario'),
        migrations.RemoveField('prestamo', 'aprobado_por'),
        migrations.RenameField('prestamo', 'aprobado_por_nuevo', 'aprobado_por'),
        migrations.AlterField('prestamo', 'lector', models.ForeignKey(
            on_delete=django.db.models.deletion.PROTECT, related_name='prestamos', to='usuarios.lector')),
        migrations.RemoveField('devolucion', 'registrado_por'),
        migrations.RenameField('devolucion', 'registrado_por_nuevo', 'registrado_por'),
        migrations.RemoveConstraint('devolucion', 'devolucion_multa_no_negativa'),
        migrations.RemoveField('devolucion', 'monto_multa'),
        migrations.RemoveField('devolucion', 'multa_pagada'),

        # --- Nombres de tabla del diseño ------------------------------------------------
        migrations.AlterModelTable('prestamo', 'prestamo'),
        migrations.AlterModelTable('devolucion', 'devolucion'),
        migrations.AlterModelTable('tarifamulta', 'tarifa_multa'),
    ]
