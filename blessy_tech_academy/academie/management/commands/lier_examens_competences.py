# ================================================
# LIER_EXAMENS_COMPETENCES.PY — Backfill intelligent
# Tente de matcher automatiquement les compétences existantes avec 
# le texte libre competences_evaluees déjà saisi
# Usage : python manage.py lier_examens_competences
# ================================================

from django.core.management.base import BaseCommand
from academie.models import Examen, Competence


class Command(BaseCommand):
    help = "Lie automatiquement Examen.competences_evaluees (texte) aux vraies Competence (FK)"

    def handle(self, *args, **options):
        liaisons_creees = 0

        for examen in Examen.objects.exclude(competences_evaluees=''):
            mots_cles = [m.strip() for m in examen.competences_evaluees.replace('\n', ',').split(',') if m.strip()]

            for mot_cle in mots_cles:
                competence = Competence.objects.filter(nom__icontains=mot_cle).first()
                if competence and not examen.competences_liees.filter(id=competence.id).exists():
                    examen.competences_liees.add(competence)
                    liaisons_creees += 1

        self.stdout.write(self.style.SUCCESS(f"✅ {liaisons_creees} liaison(s) Examen↔Compétence créée(s)"))
        self.stdout.write("⚠️ Vérifie manuellement dans l'admin — le matching est heuristique, pas garanti à 100%.")