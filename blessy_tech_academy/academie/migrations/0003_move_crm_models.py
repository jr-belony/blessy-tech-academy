from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('academie', '0002_formation_illustration'),   # Dernière migration existante avant celle-ci
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.DeleteModel('Inscription'),
                migrations.DeleteModel('InteractionCRM'),
            ],
            database_operations=[],
        )
    ]