from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('eventos', '0003_evento_usuario'),
    ]

    operations = [
        migrations.AddField(
            model_name='evento',
            name='fecha_evento',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='evento',
            name='hora_evento',
            field=models.TimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='tarealogistica',
            name='hora_asignada',
            field=models.TimeField(blank=True, null=True),
        ),
    ]
