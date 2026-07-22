# ================================================
# USERS/MIGRATIONS/0001_INITIAL.PY — Migration d'état SANS toucher aux tables
# Cette migration ne fait RIEN à la base de données réelle.
# Elle informe seulement Django que ces modèles "appartiennent" 
# maintenant conceptuellement à l'app users (mais Meta.app_label='academie' 
# les garde sur les mêmes tables physiques academie_*)
# ================================================

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('academie', '0001_initial'),  # ⚠️ adapte au nom réel de ta première migration academie
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        # Volontairement VIDE — grâce à app_label='academie' + db_table explicite 
        # dans users/models.py, aucune opération de migration réelle n'est nécessaire.
        # Django "sait" déjà que ces tables existent via l'app academie.
    ]