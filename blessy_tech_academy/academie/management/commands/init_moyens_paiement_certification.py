# ================================================
# INIT_MOYENS_PAIEMENT_CERTIFICATION.PY — Assure MonCash/NatCash existent
# ================================================
from django.core.management.base import BaseCommand
from billing.models import MoyenPaiement

class Command(BaseCommand):
    def handle(self, *args, **options):
        for code, nom, icone in [('moncash', 'MonCash', '📱'), ('natcash', 'NatCash', '📲'), ('manuel', 'Cash', '💵')]:
            MoyenPaiement.objects.get_or_create(code=code, defaults={'nom_affiche': nom, 'icone': icone, 'actif': True})
        self.stdout.write(self.style.SUCCESS("✅ Moyens de paiement initialisés"))