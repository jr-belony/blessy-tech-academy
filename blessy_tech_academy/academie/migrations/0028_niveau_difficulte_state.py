from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('academie', '0027_examen_competences_liees_competencevalidee'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AddField(
                    model_name='projetetudiant',
                    name='niveau_difficulte',
                    field=models.CharField(default='debutant', max_length=20),
                ),
            ],
        ),
    ]