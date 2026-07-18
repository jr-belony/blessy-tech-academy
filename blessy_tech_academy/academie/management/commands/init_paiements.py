# academie/management/commands/init_paiements.py
from django.core.management.base import BaseCommand

from academie.models import MoyenPaiement


class Command(BaseCommand):
    def handle(self, *args, **options):
        moyens = [
            {
                "code": "manuel",
                "nom_affiche": "Paiement manuel (MonCash/NatCash/Virement)",
                "icone": "📱",
                "ordre": 1,
                "instructions": "Envoie ton paiement au numéro MonCash 509-XXXX-XXXX puis colle la référence ci-dessous.",
            },
        ]
        for m in moyens:
            MoyenPaiement.objects.get_or_create(code=m["code"], defaults=m)
        self.stdout.write(self.style.SUCCESS("✅ Moyens de paiement initialisés"))
