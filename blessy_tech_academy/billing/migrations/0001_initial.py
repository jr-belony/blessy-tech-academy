# ================================================
# BILLING/MIGRATIONS/0001_INITIAL.PY — Migration d'état vide
# ================================================

from django.db import migrations


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        ('academie', '0008_reaction_content_type_reaction_object_id'),
        ('users', '0001_initial'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]
    operations = []  # volontairement vide