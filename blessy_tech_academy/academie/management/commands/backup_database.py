# ================================================
# BACKUP_DATABASE.PY — Sauvegarde complète PostgreSQL (pas seulement le contenu)
# Complète export_content (qui ne couvre que Formation/Article/etc.)
# Usage : python manage.py backup_database
# ================================================

import os
import subprocess
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = "Effectue une sauvegarde complète de la base PostgreSQL via pg_dump"

    def handle(self, *args, **options):
        db_config = settings.DATABASES['default']

        nom_fichier = f"backup_bta_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"

        commande = [
            'pg_dump',
            '-h', db_config.get('HOST', 'localhost'),
            '-p', str(db_config.get('PORT', 5432)),
            '-U', db_config.get('USER', ''),
            '-d', db_config.get('NAME', ''),
            '-f', nom_fichier,
            '--no-password',
        ]

        env = os.environ.copy()
        env['PGPASSWORD'] = db_config.get('PASSWORD', '')

        try:
            resultat = subprocess.run(commande, env=env, capture_output=True, text=True, timeout=300)
            if resultat.returncode == 0:
                taille_mo = round(os.path.getsize(nom_fichier) / (1024 * 1024), 2)
                self.stdout.write(self.style.SUCCESS(f"✅ Sauvegarde réussie : {nom_fichier} ({taille_mo} Mo)"))

                # Upload automatique vers S3 si configuré (réutilise le storage existant)
                if getattr(settings, 'USE_S3_STORAGE', False):
                    self._uploader_vers_s3(nom_fichier)
            else:
                self.stdout.write(self.style.ERROR(f"❌ Échec pg_dump : {resultat.stderr}"))
        except subprocess.TimeoutExpired:
            self.stdout.write(self.style.ERROR("❌ Timeout — la sauvegarde a pris trop de temps"))
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR("❌ pg_dump introuvable — vérifie que PostgreSQL client est installé"))

    def _uploader_vers_s3(self, nom_fichier):
        try:
            import boto3
            from django.conf import settings as s

            client_s3 = boto3.client(
                's3', endpoint_url=getattr(s, 'AWS_S3_ENDPOINT_URL', None),
                aws_access_key_id=s.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=s.AWS_SECRET_ACCESS_KEY,
            )
            client_s3.upload_file(nom_fichier, s.AWS_STORAGE_BUCKET_NAME, f"backups/{nom_fichier}")
            self.stdout.write(self.style.SUCCESS(f"☁️ Sauvegarde uploadée vers S3/R2 : backups/{nom_fichier}"))
            os.remove(nom_fichier)  # nettoie le fichier local après upload
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"⚠️ Upload S3 échoué (fichier local conservé) : {e}"))