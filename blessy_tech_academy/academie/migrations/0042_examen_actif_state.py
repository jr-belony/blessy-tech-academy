from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('academie', '0041_ambassadeur'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AddField(
                    model_name='examen',
                    name='actif',
                    field=models.BooleanField(default=True),
                ),
            ],
        ),
    ]