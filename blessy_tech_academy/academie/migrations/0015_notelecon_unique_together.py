from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('academie', '0014_add_check_constraints'),  # dernier fichier correct
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='notelecon',
            unique_together={('utilisateur', 'lecon')},
        ),
    ]