# ================================================
# CONFIGURER_FRAIS_PILOTE.PY — Frais de certification pour la Cohorte Pilote
# Usage : python manage.py configurer_frais_pilote
# ================================================

from django.core.management.base import BaseCommand
from academie.models import Cohorte, EligibiliteCertification


class Command(BaseCommand):
    help = "Configure les frais de certification pour les formations de la Cohorte Pilote"

    def add_arguments(self, parser):
        parser.add_argument('--montant', type=float, default=0, help="Montant en USD (0 = gratuit pour le pilote)")

    def handle(self, *args, **options):
        cohorte = Cohorte.objects.filter(nom='Cohorte Pilote 2026').first()
        if not cohorte:
            self.stdout.write(self.style.ERROR("❌ Cohorte Pilote 2026 introuvable"))
            return

        montant = options['montant']
        
        # 1. Enregistrer le montant sur la cohorte
        cohorte.frais_montant = montant
        cohorte.save()

        # 2. Mettre à jour les éligibilités existantes en fonction du montant
        if montant == 0:
            # Certificat gratuit : on marque toutes les éligibilités de la cohorte comme payées
            count = EligibiliteCertification.objects.filter(cohorte=cohorte).update(frais_paye=True)
            self.stdout.write(self.style.SUCCESS(
                f"✅ Frais configurés à 0$ – {count} éligibilité(s) marquée(s) comme frais payés (gratuit)."
            ))
        else:
            # Montant > 0 : on remet frais_paye à False pour forcer le paiement
            count = EligibiliteCertification.objects.filter(cohorte=cohorte).update(frais_paye=False)
            self.stdout.write(self.style.WARNING(
                f"⚠️ Frais configurés à {montant}$. Les {count} éligibilité(s) existante(s) doivent être payées."
            ))