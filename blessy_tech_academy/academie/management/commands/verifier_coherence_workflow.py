# ================================================
# VERIFIER_COHERENCE_WORKFLOW.PY — Détecte/corrige les divergences
# L'audit signale : "états gérés côté application seulement, pas de 
# contrainte DB" — cette commande audite et corrige les incohérences
# Usage : python manage.py verifier_coherence_workflow --corriger
# ================================================

from django.core.management.base import BaseCommand
from academie.models import Formation, WorkflowFormation


class Command(BaseCommand):
    help = "Vérifie et corrige la cohérence Formation.actif / WorkflowFormation.etat_actuel"

    def add_arguments(self, parser):
        parser.add_argument('--corriger', action='store_true', help="Applique les corrections automatiquement")

    def handle(self, *args, **options):
        incoherences = []

        for formation in Formation.objects.select_related('workflow').all():
            workflow = getattr(formation, 'workflow', None)
            if not workflow:
                continue

            devrait_etre_actif = workflow.etat_actuel == 'publiee'
            if formation.actif != devrait_etre_actif:
                incoherences.append((formation, workflow, devrait_etre_actif))

        self.stdout.write(f"🔍 {len(incoherences)} incohérence(s) détectée(s)\n")

        for formation, workflow, devrait_etre_actif in incoherences:
            self.stdout.write(
                f"   • {formation.nom} : actif={formation.actif} mais état='{workflow.etat_actuel}' "
                f"(devrait être actif={devrait_etre_actif})"
            )
            if options['corriger']:
                formation.actif = devrait_etre_actif
                formation.save(update_fields=['actif'])

        if options['corriger'] and incoherences:
            self.stdout.write(self.style.SUCCESS(f"\n✅ {len(incoherences)} formation(s) corrigée(s)"))
        elif incoherences:
            self.stdout.write(self.style.WARNING("\n⚠️ Relance avec --corriger pour appliquer les corrections"))