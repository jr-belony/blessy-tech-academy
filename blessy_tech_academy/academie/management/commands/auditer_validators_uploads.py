# ================================================
# AUDITER_VALIDATORS_UPLOADS.PY — Diagnostic couverture validation
# Usage : python manage.py auditer_validators_uploads
# Liste TOUS les champs FileField/ImageField du projet et signale 
# ceux qui n'ont AUCUN validator appliqué (risque sécurité)
# ================================================

from django.core.management.base import BaseCommand
from django.apps import apps
from django.db.models import FileField, ImageField


class Command(BaseCommand):
    help = "Audite tous les champs FileField/ImageField pour vérifier la présence de validators"

    def handle(self, *args, **options):
        problemes = []
        ok = []

        for model in apps.get_app_config('academie').get_models():
            for field in model._meta.get_fields():
                if isinstance(field, (FileField, ImageField)):
                    if not field.validators:
                        problemes.append(f"{model.__name__}.{field.name}")
                    else:
                        ok.append(f"{model.__name__}.{field.name} ({len(field.validators)} validator(s))")

        self.stdout.write(self.style.SUCCESS(f"\n✅ Champs SÉCURISÉS ({len(ok)}) :"))
        for item in ok:
            self.stdout.write(f"   • {item}")

        if problemes:
            self.stdout.write(self.style.ERROR(f"\n❌ Champs SANS validator ({len(problemes)}) — À CORRECTIF :"))
            for item in problemes:
                self.stdout.write(f"   • {item}")
        else:
            self.stdout.write(self.style.SUCCESS("\n🎉 Tous les champs fichiers sont protégés !"))