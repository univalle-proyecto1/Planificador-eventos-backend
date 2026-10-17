from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('eventos', '0004_evento_fecha_evento_evento_hora_evento_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='tarealogistica',
            name='note',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='tarealogistica',
            name='done_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]