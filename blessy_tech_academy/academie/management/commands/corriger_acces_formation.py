# ================================================
# CORRIGER_ACCES_FORMATION.PY — Nettoyage AVANT d'appliquer la nouvelle contrainte
# Usage : python manage.py corriger_acces_formation
# ================================================

from django.core.management.base import BaseCommand
from billing.models import AccesFormationDebloque


class Command(BaseCommand):
    help = "Dédoublonne AccesFormationDebloque avant application de la nouvelle contrainte unique"

    def handle(self, *args, **options):
        vus = set()
        supprimes = 0

        for acces in AccesFormationDebloque.objects.filter(formation__isnull=False).order_by('date_deblocage'):
            cle = (acces.utilisateur_id, acces.formation_id)
            if cle in vus:
                acces.delete()
                supprimes += 1
            else:
                vus.add(cle)

        self.stdout.write(self.style.SUCCESS(f"✅ {supprimes} doublon(s) supprimé(s)"))