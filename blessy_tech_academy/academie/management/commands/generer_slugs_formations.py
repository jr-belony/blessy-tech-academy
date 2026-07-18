# ================================================
# GENERER_SLUGS_FORMATIONS.PY — Backfill slugs zéro-casse
# Usage : python manage.py generer_slugs_formations
# ================================================

from django.core.management.base import BaseCommand
from django.utils.text import slugify
from academie.models import Formation


class Command(BaseCommand):
    help = "Génère les slugs manquants pour les formations existantes"

    def handle(self, *args, **options):
        formations_sans_slug = Formation.objects.filter(slug__isnull=True)
        compteur = 0

        for formation in formations_sans_slug:
            base_slug = slugify(formation.nom)
            slug_candidat = base_slug
            i = 1
            while Formation.objects.filter(slug=slug_candidat).exclude(pk=formation.pk).exists():
                slug_candidat = f"{base_slug}-{i}"
                i += 1
            formation.slug = slug_candidat
            formation.save(update_fields=['slug'])
            compteur += 1

        self.stdout.write(self.style.SUCCESS(f"✅ {compteur} slug(s) généré(s)"))