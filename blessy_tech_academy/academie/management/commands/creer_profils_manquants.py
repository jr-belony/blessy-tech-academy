# ================================================
# CREER_PROFILS_MANQUANTS.PY — Rattrapage profils existants
# Usage : python manage.py creer_profils_manquants
# ================================================

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from academie.models import ProfilUtilisateur


class Command(BaseCommand):
    help = "Crée les ProfilUtilisateur manquants pour les users existants"

    def handle(self, *args, **options):
        crees = 0
        for user in User.objects.all():
            profil, cree = ProfilUtilisateur.objects.get_or_create(
                utilisateur=user, defaults={"role": "admin" if user.is_staff else "etudiant"}
            )
            if cree:
                crees += 1
        self.stdout.write(self.style.SUCCESS(f"✅ {crees} profil(s) créé(s)"))
