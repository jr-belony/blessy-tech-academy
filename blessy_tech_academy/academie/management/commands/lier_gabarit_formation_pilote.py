# ================================================
# LIER_GABARIT_FORMATION_PILOTE.PY — Connecte le gabarit officiel a une formation
# Sans cette liaison, l'examen ne peut pas alimenter EligibiliteCertification
# ================================================

from django.core.management.base import BaseCommand
from academie.models_banque import GabaritExamen
from academie.models import Formation


class Command(BaseCommand):
    help = "Lie le gabarit officiel a une formation de la cohorte pilote"

    def add_arguments(self, parser):
        parser.add_argument('--formation', type=str, required=True, help="Nom exact de la formation")

    def handle(self, *args, **options):
        gabarit = GabaritExamen.objects.filter(nom='Examen de Certification Officiel BTA').first()
        formation = Formation.objects.filter(nom=options['formation']).first()

        if not gabarit or not formation:
            self.stdout.write(self.style.ERROR("Gabarit ou formation introuvable"))
            return

        gabarit.formation_liee = formation
        gabarit.save()
        self.stdout.write(self.style.SUCCESS(f"Gabarit lie a la formation : {formation.nom}"))