# ================================================
# EXPIRER_ENROLLMENTS.PY — Synchronise le statut réel avec la date d'expiration
# Usage : python manage.py expirer_enrollments
# À planifier quotidiennement via Railway Cron
# ================================================

from django.core.management.base import BaseCommand
from django.utils import timezone
from academie.models import Enrollment


class Command(BaseCommand):
    help = "Passe en statut 'expire' tous les Enrollment dont la date_expiration est dépassée"

    def handle(self, *args, **options):
        maintenant = timezone.now()
        nb_expires = Enrollment.objects.filter(
            statut='actif', date_expiration__isnull=False, date_expiration__lt=maintenant
        ).update(statut='expire')

        self.stdout.write(self.style.SUCCESS(f"✅ {nb_expires} enrollment(s) marqué(s) 'expire'"))