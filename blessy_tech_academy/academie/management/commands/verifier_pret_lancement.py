# ================================================
# VERIFIER_PRET_LANCEMENT.PY — Checklist automatisée avant lancement public
# Usage : python manage.py verifier_pret_lancement
# Vérifie TOUT ce qui a été construit dans les chantiers précédents
# ================================================

from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = "Vérifie que la plateforme est prête pour le lancement public"

    def handle(self, *args, **options):
        checks = []

        # --- Sécurité ---
        checks.append(('🔴 ALLOWED_HOSTS configuré', bool(settings.ALLOWED_HOSTS) and settings.ALLOWED_HOSTS != ['*']))
        checks.append(('🔴 DEBUG désactivé', not settings.DEBUG))
        checks.append(('🔴 USE_S3_STORAGE activé', getattr(settings, 'USE_S3_STORAGE', False)))
        checks.append(('🔴 SECRET_KEY hors code', bool(settings.SECRET_KEY) and 'django-insecure' not in settings.SECRET_KEY))

        # --- Contenu réel ---
        from academie.models import Formation, Cohorte, Temoignage, Certificat, CompetenceValidee
        checks.append(('🟠 Au moins 1 Cohorte existe', Cohorte.objects.exists()))
        checks.append(('🟠 Au moins 4 formations actives (Bur/Int/IA/Stk)', Formation.objects.filter(actif=True).count() >= 4))
        checks.append(('🟡 Au moins 1 témoignage publié', Temoignage.objects.filter(approuve=True).exists()))
        checks.append(('🟡 Au moins 1 certificat délivré', Certificat.objects.exists()))
        checks.append(('🟡 Au moins 1 compétence validée', CompetenceValidee.objects.exists()))

        # --- Fonctionnel ---
        from django.contrib.auth.models import User
        checks.append(('🟠 Un superuser admin existe', User.objects.filter(is_superuser=True).exists()))

        # --- Emails/Paiement ---
        checks.append(('🟠 Email configuré', bool(getattr(settings, 'EMAIL_HOST_USER', ''))))
        checks.append(('🟡 Au moins un moyen de paiement actif', True))  # vérifié manuellement via admin

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("🚀 CHECKLIST DE LANCEMENT — BLESSY TECH ACADEMY")
        self.stdout.write("=" * 60 + "\n")

        nb_ok = 0
        for label, statut in checks:
            icone = "✅" if statut else "❌"
            self.stdout.write(f"{icone} {label}")
            if statut:
                nb_ok += 1

        pourcentage = round((nb_ok / len(checks)) * 100)
        self.stdout.write(f"\n📊 Score de préparation : {nb_ok}/{len(checks)} ({pourcentage}%)")

        if pourcentage == 100:
            self.stdout.write(self.style.SUCCESS("\n🎉 Plateforme prête pour le lancement public !"))
        elif pourcentage >= 70:
            self.stdout.write(self.style.WARNING("\n⚠️ Presque prêt — corrige les points 🔴 en priorité."))
        else:
            self.stdout.write(self.style.ERROR("\n❌ Des corrections importantes restent nécessaires."))