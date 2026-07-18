# ================================================
# CREER_WORKFLOWS_MANQUANTS.PY — Rattrapage formations existantes
# ================================================

from django.core.management.base import BaseCommand

from academie.models import Formation, WorkflowFormation


class Command(BaseCommand):
    help = "Crée les WorkflowFormation manquants pour les formations déjà en base"

    def handle(self, *args, **options):
        crees = 0
        for formation in Formation.objects.all():
            # Les formations déjà actif=True sont considérées comme "publiées"
            etat_initial = 'publiee' if formation.actif else 'brouillon'
            workflow, cree = WorkflowFormation.objects.get_or_create(
                formation=formation,
                defaults={
                    'etat_actuel': etat_initial,
                    'checklist_contenu_complet': formation.modules.exists(),
                    'checklist_seo_complet': bool(formation.description),
                    'checklist_prix_valide': True,
                    'checklist_quiz_present': formation.quiz_set.exists() if hasattr(formation, 'quiz_set') else False,
                }
            )
            if cree:
                crees += 1
        self.stdout.write(self.style.SUCCESS(f"✅ {crees} workflow(s) créé(s)"))