from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('academie', '0003_move_crm_models'),   # la dernière migration CRM appliquée
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.DeleteModel('Sujet'),
                migrations.DeleteModel('Reponse'),
                migrations.DeleteModel('Reaction'),
                migrations.DeleteModel('BadgeForum'),
            ],
            database_operations=[],   # ne touche pas aux tables
        )
    ]