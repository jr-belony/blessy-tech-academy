# ================================================
# 0067_PARTENAIREAPI_DATE_EXPIRATION_AND_MORE.PY — Recréation exacte
# ================================================
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("academie", "0066_workflowarticle"),
    ]

    operations = [
        migrations.AddField(
            model_name="partenaireapi",
            name="date_expiration",
            field=models.DateTimeField(blank=True, help_text="Date d'expiration de la clé API", null=True),
        ),
        migrations.AddField(
            model_name="partenaireapi",
            name="limite_requetes_heure",
            field=models.IntegerField(default=100, help_text="Nombre max de requêtes par heure"),
        ),
    ]