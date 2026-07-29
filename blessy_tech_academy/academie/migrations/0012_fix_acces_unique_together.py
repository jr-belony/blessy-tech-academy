from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('academie', '0011_outilrecommande_alter_moyenpaiement_icone_and_more'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='accesformationdebloque',
            unique_together={('utilisateur', 'formation')},
        ),
    ]