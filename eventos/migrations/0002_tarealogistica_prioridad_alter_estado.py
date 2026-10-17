from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('eventos', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='tarealogistica',
            name='prioridad',
            field=models.CharField(
                choices=[('NORMAL', 'Normal'), ('ALTA', 'Alta'), ('CRITICA', 'Crítica')],
                default='NORMAL',
                max_length=10,
            ),
        ),
        migrations.AlterField(
            model_name='tarealogistica',
            name='estado',
            field=models.CharField(
                choices=[
                    ('PENDIENTE', 'Pendiente'),
                    ('EN_PROGRESO', 'En Progreso'),
                    ('HECHO', 'Hecho'),
                    ('POSPUESTO', 'Pospuesto'),
                ],
                default='PENDIENTE',
                max_length=15,
            ),
        ),
    ]
