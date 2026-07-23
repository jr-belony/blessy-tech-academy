# ================================================
# academie/management/commands/renouveler_abonnements.py
# À exécuter quotidiennement via cron/Railway Scheduler
# ================================================

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from academie.models import Subscription


class Command(BaseCommand):
    help = "Vérifie et renouvelle les abonnements arrivant à échéance"

    def handle(self, *args, **options):
        maintenant = timezone.now()
        a_renouveler = Subscription.objects.filter(
            statut="actif",
            renouvellement_auto=True,
            date_prochain_renouvellement__lte=maintenant,
        )

        for abo in a_renouveler:
            try:
                from .payment_gateways import stripe_gateway

                succes = stripe_gateway.charger_renouvellement(abo)

                if succes:
                    duree = timedelta(days=30 if abo.plan.periodicite == "mensuel" else 365)
                    abo.date_prochain_renouvellement = maintenant + duree
                    abo.save()
                    self.stdout.write(self.style.SUCCESS(f"✅ Renouvelé : {abo}"))
                else:
                    abo.statut = "en_echec"
                    abo.save()
                    self.stdout.write(self.style.WARNING(f"⚠️ Échec paiement : {abo}"))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Erreur {abo} : {e}"))

        # Expire les abonnements en échec depuis plus de 5 jours (grâce period)
        Subscription.objects.filter(
            statut="en_echec", date_prochain_renouvellement__lt=maintenant - timedelta(days=5)
        ).update(statut="expire")
