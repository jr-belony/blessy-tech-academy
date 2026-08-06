# ================================================
# 0066_WORKFLOWARTICLE.PY — Recréation exacte (django_migrations 
# l'a déjà marquée appliquée, ce fichier réconcilie le disque)
# ================================================
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("academie", "0065_partenaireapi_scopes"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="WorkflowArticle",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("etat_actuel", models.CharField(
                    choices=[
                        ("brouillon", "📝 Brouillon"),
                        ("en_revision", "🔍 En révision"),
                        ("valide", "✅ Validé"),
                        ("publie", "🌐 Publié"),
                        ("archive", "📦 Archivé"),
                    ],
                    default="brouillon", max_length=20,
                )),
                ("checklist_seo_complet", models.BooleanField(default=False)),
                ("checklist_image_presente", models.BooleanField(default=False)),
                ("commentaire_revision", models.TextField(blank=True)),
                ("date_creation", models.DateTimeField(auto_now_add=True)),
                ("date_derniere_transition", models.DateTimeField(auto_now=True)),
                ("article", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="workflow", to="academie.article")),
                ("demande_par", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="workflows_articles_demandes", to=settings.AUTH_USER_MODEL)),
                ("valide_par", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="workflows_articles_valides", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "Workflow article",
                "verbose_name_plural": "Workflows articles",
                "db_table": "academie_workflowarticle",
            },
        ),
    ]