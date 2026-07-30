# ================================================
# PURGER_DONNEES_ANCIENNES.PY — Purge périodique (audit: croissance illimitée)
# Usage : python manage.py purger_donnees_anciennes
# À planifier via Railway Cron (hebdomadaire)
# ================================================

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from users.models import HistoriqueConversationIA, NotificationPushEnvoyee, LogAudit
from academie.models import LogRequetePartenaire


class Command(BaseCommand):
    help = "Purge les données historiques anciennes pour limiter la croissance des tables"

    def handle(self, *args, **options):
        maintenant = timezone.now()

        # Historique IA : conserve 90 jours (permet personnalisation raisonnable)
        seuil_ia = maintenant - timedelta(days=90)
        nb_ia, _ = HistoriqueConversationIA.objects.filter(date_creation__lt=seuil_ia).delete()

        # Notifications push envoyées : conserve 60 jours (juste pour debug)
        seuil_push = maintenant - timedelta(days=60)
        nb_push, _ = NotificationPushEnvoyee.objects.filter(date_envoi__lt=seuil_push).delete()

        # Logs de requêtes partenaires : conserve 30 jours (rate limiting n'a pas besoin de plus)
        seuil_logs_api = maintenant - timedelta(days=30)
        nb_logs_api, _ = LogRequetePartenaire.objects.filter(date_creation__lt=seuil_logs_api).delete()

        # LogAudit : conserve 1 an (traçabilité légale/comptable plus longue)
        seuil_audit = maintenant - timedelta(days=365)
        nb_audit, _ = LogAudit.objects.filter(date_creation__lt=seuil_audit).delete()

        self.stdout.write(self.style.SUCCESS(
            f"✅ Purge terminée :\n"
            f"   • Historique IA : {nb_ia} entrée(s) supprimée(s)\n"
            f"   • Notifications push : {nb_push} entrée(s) supprimée(s)\n"
            f"   • Logs API partenaires : {nb_logs_api} entrée(s) supprimée(s)\n"
            f"   • Logs d'audit : {nb_audit} entrée(s) supprimée(s)"
        ))