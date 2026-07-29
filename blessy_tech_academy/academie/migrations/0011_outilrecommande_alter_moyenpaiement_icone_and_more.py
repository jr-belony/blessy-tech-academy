from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('academie', '0010_fix_fields'),
    ]

    operations = [
        # Migration volontairement vide.
        # Les modifications de champs (icone, icone_produit_snapshot) 
        # ont déjà été traitées dans 0010_fix_fields.
        # Les CreateModel ci-dessous ne sont pas nécessaires 
        # car ces tables existent déjà.
    ]