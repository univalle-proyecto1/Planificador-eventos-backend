from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('eventos', '0005_tarealogistica_note_done_at'),
    ]

    operations = [
        migrations.CreateModel(
            name='Novedad',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo', models.CharField(choices=[('EVENTO_CREADO', 'Evento creado'), ('EVENTO_EDITADO', 'Evento editado'), ('SUBTAREA_AGREGADA', 'Subtarea agregada'), ('SUBTAREA_COMPLETADA', 'Subtarea completada')], max_length=24)),
                ('subtarea_titulo', models.CharField(blank=True, default='', max_length=200)),
                ('fecha', models.DateTimeField(auto_now_add=True)),
                ('evento', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='novedades', to='eventos.evento')),
            ],
            options={
                'ordering': ['-fecha'],
            },
        ),
    ]