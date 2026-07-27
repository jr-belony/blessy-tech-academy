from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('academie', '0004_move_forum_models'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.DeleteModel('Article'),
                migrations.DeleteModel('OutilRecommande'),
                migrations.DeleteModel('Temoignage'),
                migrations.DeleteModel('ProjetEtudiant'),
                migrations.DeleteModel('Certificat'),
            ],
            database_operations=[],
        )
    ]