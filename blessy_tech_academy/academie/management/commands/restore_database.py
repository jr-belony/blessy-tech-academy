# ================================================
# RESTORE_DATABASE.PY — Restauration PostgreSQL depuis backup
# Usage : python manage.py restore_database backup_bta_20260720.sql
# ⚠️ DESTRUCTIF — écrase les données actuelles, confirmation requise
# ================================================

import subprocess
import os
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings


class Command(BaseCommand):
    help = "Restaure la base PostgreSQL depuis un fichier de sauvegarde"

    def add_arguments(self, parser):
        parser.add_argument('fichier', type=str, help="Chemin du fichier .sql à restaurer")
        parser.add_argument('--force', action='store_true', help="Ignore la confirmation interactive")

    def handle(self, *args, **options):
        fichier = options['fichier']

        if not os.path.exists(fichier):
            raise CommandError(f"❌ Fichier introuvable : {fichier}")

        if not options['force']:
            self.stdout.write(self.style.WARNING(
                "⚠️ ATTENTION : cette opération va ÉCRASER toutes les données actuelles."
            ))
            confirmation = input("Tape 'RESTAURER' en majuscules pour confirmer : ")
            if confirmation != 'RESTAURER':
                self.stdout.write(self.style.ERROR("❌ Annulé — confirmation incorrecte."))
                return

        db_config = settings.DATABASES['default']
        env = os.environ.copy()
        env['PGPASSWORD'] = db_config.get('PASSWORD', '')

        commande = [
            'psql',
            '-h', db_config.get('HOST', 'localhost'),
            '-p', str(db_config.get('PORT', 5432)),
            '-U', db_config.get('USER', ''),
            '-d', db_config.get('NAME', ''),
            '-f', fichier,
        ]

        try:
            resultat = subprocess.run(commande, env=env, capture_output=True, text=True, timeout=600)
            if resultat.returncode == 0:
                self.stdout.write(self.style.SUCCESS(f"✅ Restauration réussie depuis {fichier}"))
            else:
                self.stdout.write(self.style.ERROR(f"❌ Erreur restauration : {resultat.stderr}"))
        except subprocess.TimeoutExpired:
            self.stdout.write(self.style.ERROR("❌ Timeout — restauration trop longue"))