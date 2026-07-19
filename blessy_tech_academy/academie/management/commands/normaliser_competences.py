# ================================================
# NORMALISER_COMPETENCES.PY — Extraction automatique depuis TextField existants
# Usage : python manage.py normaliser_competences
# Parse Formation.debouches (texte libre) et crée des Competence structurées
# ================================================

from django.core.management.base import BaseCommand
from academie.models import Formation, Competence


class Command(BaseCommand):
    help = "Extrait et normalise les compétences depuis les champs texte existants"

    def handle(self, *args, **options):
        competences_creees = 0
        liaisons_creees = 0

        for formation in Formation.objects.exclude(debouches=''):
            # Découpe le texte libre par virgules — heuristique simple mais efficace
            elements = [e.strip() for e in formation.debouches.replace('\n', ',').split(',') if e.strip()]

            for element in elements[:8]:  # limite raisonnable par formation
                if len(element) < 3 or len(element) > 100:
                    continue

                competence, cree = Competence.objects.get_or_create(
                    nom=element,
                    defaults={'categorie': 'technique', 'icone': '⚡'}
                )
                if cree:
                    competences_creees += 1

                if not competence.formations.filter(id=formation.id).exists():
                    competence.formations.add(formation)
                    liaisons_creees += 1

        self.stdout.write(self.style.SUCCESS(
            f"✅ {competences_creees} compétence(s) créée(s), {liaisons_creees} liaison(s) établie(s)"
        ))