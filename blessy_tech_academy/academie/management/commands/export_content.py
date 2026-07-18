import json
import time

from django.core import serializers
from django.core.management.base import BaseCommand

from academie.models import Ecole, Formation, Lecon, Module


class Command(BaseCommand):
    help = "Exporte le contenu pedagogique en JSON"

    def handle(self, *args, **options):
        debut = time.time()
        data = []

        for model in [Ecole, Formation, Module, Lecon]:
            for obj in model.objects.all():
                data.append({
                    'model': model.__name__,
                    'fields': serializers.serialize('python', [obj])[0]['fields']
                })

        nom_fichier = f"bta_export_{time.strftime('%Y%m%d_%H%M%S')}.json"

        with open(nom_fichier, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        duree = round(time.time() - debut, 2)
        self.stdout.write(self.style.SUCCESS(f"Export termine en {duree}s -> {nom_fichier}"))


