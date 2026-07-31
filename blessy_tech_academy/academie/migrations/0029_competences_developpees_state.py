from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('academie', '0028_niveau_difficulte_state'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AddField(
                    model_name='projetetudiant',
                    name='competences_developpees',
                    field=models.CharField(blank=True, default='', max_length=500),
                ),
            ],
        ),
    ]