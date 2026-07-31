import django.db.models.deletion
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('academie', '0019_alter_certificat_numero'),
    ]

    operations = [
        migrations.AddField(
            model_name='certificat',
            name='examen_origine',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to='academie.examen',
            ),
        ),
    ]