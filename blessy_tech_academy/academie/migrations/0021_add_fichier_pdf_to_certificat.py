import django.db.models.deletion
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('academie', '0020_add_examen_origine_to_certificat'),
    ]

    operations = [
        migrations.AddField(
            model_name='certificat',
            name='fichier_pdf',
            field=models.FileField(upload_to='certificats/', null=True, blank=True),
        ),
    ]