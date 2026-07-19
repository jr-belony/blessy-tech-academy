# ================================================
# MIGRER_MEDIA_VERS_S3.PY — Migration ponctuelle des fichiers existants
# Usage : python manage.py migrer_media_vers_s3
# À exécuter UNE SEULE FOIS après activation de USE_S3_STORAGE
# ================================================

import os
from django.core.management.base import BaseCommand
from django.core.files import File
from academie.models import ProjetEtudiant, Formation, Academie, Invoice


class Command(BaseCommand):
    help = "Migre les fichiers média existants du disque local vers S3/R2"

    def handle(self, *args, **options):
        migres = 0

        for modele, champ in [(ProjetEtudiant, 'image'), (Academie, 'logo'), (Invoice, 'fichier_pdf')]:
            for obj in modele.objects.exclude(**{f'{champ}': ''}):
                fichier = getattr(obj, champ)
                if fichier and hasattr(fichier, 'path'):
                    try:
                        chemin_local = fichier.path
                        if os.path.exists(chemin_local):
                            with open(chemin_local, 'rb') as f:
                                nom = os.path.basename(chemin_local)
                                fichier.save(nom, File(f), save=True)
                                migres += 1
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f"⚠️ Impossible de migrer {obj} : {e}"))

        self.stdout.write(self.style.SUCCESS(f"✅ {migres} fichier(s) migré(s) vers le stockage distant"))