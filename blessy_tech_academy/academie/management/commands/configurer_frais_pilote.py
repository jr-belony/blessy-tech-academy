# ================================================
# CONFIGURER_FRAIS_PILOTE.PY — Frais de certification pour la Cohorte Pilote
# Usage : python manage.py configurer_frais_pilote
# ================================================

from django.core.management.base import BaseCommand
from academie.models import Cohorte, EligibiliteCertification


class Command(BaseCommand):
    help = "Configure les frais de certification à 1500 HTG (paiement cash) pour la Cohorte Pilote"

    def handle(self, *args, **options):
        cohorte = Cohorte.objects.filter(nom='Cohorte Pilote 2026').first()
        if not cohorte:
            self.stdout.write(self.style.ERROR("❌ Cohorte Pilote 2026 introuvable"))
            return

        # 1. Enregistrer le montant sur la cohorte (si le champ existe)
        if hasattr(cohorte, 'frais_montant'):
            cohorte.frais_montant = 1500
            cohorte.save()
            self.stdout.write(self.style.SUCCESS("✅ Montant de 1500 HTG enregistré sur la cohorte."))
        else:
            self.stdout.write(self.style.WARNING("⚠️ Le champ 'frais_montant' n'existe pas sur Cohorte. Pense à l'ajouter."))

        # 2. Réinitialiser les éligibilités : forcer frais_paye = False pour toutes
        count = EligibiliteCertification.objects.filter(cohorte=cohorte).update(frais_paye=False)
        self.stdout.write(self.style.WARNING(
            f"⚠️ {count} éligibilité(s) réinitialisée(s) : frais_paye = False. Chaque membre devra payer 1500 HTG."
        ))

        self.stdout.write(self.style.SUCCESS(
            "✅ Configuration terminée. Les frais sont fixés à 1500 HTG (cash) pour la Cohorte Pilote."
        ))
        self.stdout.write(self.style.SUCCESS(
            "🔒 Seul un superadmin ou un administrateur (staff) peut valider le paiement dans l'admin d'éligibilité."
        ))