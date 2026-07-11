"""
Commande d'import intelligent du contenu pédagogique BTA.
Usage :
    python manage.py import_content bta_export_20260701.json
    python manage.py import_content bta_export.json --dry-run
"""

import json
import time
from django.core.management.base import BaseCommand, CommandError
from django.core import serializers
from django.db import transaction

class Command(BaseCommand):
    help = "Importe le contenu pédagogique BTA sans créer de doublons"

    def add_arguments(self, parser):
        parser.add_argument('fichier', type=str, help="Chemin du fichier JSON à importer")
        parser.add_argument(
            '--dry-run', action='store_true',
            help="Simule l'import sans rien écrire en base"
        )

    def handle(self, *args, **options):
        debut = time.time()
        fichier = options['fichier']
        dry_run = options['dry_run']

        try:
            with open(fichier, 'r', encoding='utf-8') as f:
                contenu_json = f.read()
        except FileNotFoundError:
            raise CommandError(f"❌ Fichier introuvable : {fichier}")

        rapport = {'crees': 0, 'mis_a_jour': 0, 'erreurs': 0, 'details_erreurs': []}

        objets = list(serializers.deserialize('json', contenu_json))

        self.stdout.write(f"\n📦 {len(objets)} objet(s) trouvé(s) dans le fichier.\n")

        if dry_run:
            self.stdout.write(self.style.WARNING("🔍 MODE SIMULATION — Rien ne sera écrit en base.\n"))

        try:
            with transaction.atomic():
                for deserialized_obj in objets:
                    try:
                        model = deserialized_obj.object.__class__
                        pk = deserialized_obj.object.pk

                        existe_deja = model.objects.filter(pk=pk).exists()

                        if not dry_run:
                            deserialized_obj.save()

                        if existe_deja:
                            rapport['mis_a_jour'] += 1
                        else:
                            rapport['crees'] += 1

                    except Exception as e:
                        rapport['erreurs'] += 1
                        rapport['details_erreurs'].append(str(e))

                if dry_run:
                    # Annule la transaction en mode simulation
                    raise Exception("DRY_RUN_ROLLBACK")

        except Exception as e:
            if str(e) != "DRY_RUN_ROLLBACK":
                raise CommandError(f"❌ Erreur critique — rollback complet : {e}")

        duree = round(time.time() - debut, 2)

        self.stdout.write(self.style.SUCCESS(f"\n✅ Import terminé en {duree}s\n"))
        self.stdout.write("📊 Rapport de synchronisation :")
        self.stdout.write(f"   ✨ Créés       : {rapport['crees']}")
        self.stdout.write(f"   🔄 Mis à jour  : {rapport['mis_a_jour']}")
        self.stdout.write(f"   ⚠️  Erreurs     : {rapport['erreurs']}")

        if rapport['details_erreurs']:
            self.stdout.write(self.style.ERROR("\nDétail des erreurs :"))
            for err in rapport['details_erreurs'][:10]:
                self.stdout.write(f"   • {err}")

        return rapport


