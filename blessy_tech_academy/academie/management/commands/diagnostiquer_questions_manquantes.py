# ================================================
# DIAGNOSTIQUER_QUESTIONS_MANQUANTES.PY — Sans urgence, zero emoji (zero crash encodage)
# Usage : python manage.py diagnostiquer_questions_manquantes
# ================================================

from django.core.management.base import BaseCommand
from academie.models_banque import ModuleBanque, CategorieBanque, QuestionBanque

from academie.management.commands.seed_questions_batch1 import QUESTIONS_INTERNET as B1_INT, QUESTIONS_IA as B1_IA, QUESTIONS_BUREAUTIQUE as B1_BUR
from academie.management.commands.seed_questions_batch2 import QUESTIONS_INTERNET as B2_INT, QUESTIONS_IA as B2_IA, QUESTIONS_BUREAUTIQUE as B2_BUR
from academie.management.commands.seed_questions_batch3 import QUESTIONS_INTERNET as B3_INT, QUESTIONS_IA as B3_IA, QUESTIONS_BUREAUTIQUE as B3_BUR
from academie.management.commands.seed_questions_batch4 import QUESTIONS_INTERNET as B4_INT, QUESTIONS_IA as B4_IA, QUESTIONS_BUREAUTIQUE as B4_BUR
from academie.management.commands.seed_questions_batch5 import QUESTIONS_INTERNET as B5_INT, QUESTIONS_IA as B5_IA, QUESTIONS_BUREAUTIQUE as B5_BUR


class Command(BaseCommand):
    help = "Diagnostic sans emoji (evite crash encodage) - liste les questions du code absentes en base"

    def handle(self, *args, **options):
        tout = {
            'INT': B1_INT + B2_INT + B3_INT + B4_INT + B5_INT,
            'IA': B1_IA + B2_IA + B3_IA + B4_IA + B5_IA,
            'BUR': B1_BUR + B2_BUR + B3_BUR + B4_BUR + B5_BUR,
        }

        for code, questions in tout.items():
            module = ModuleBanque.objects.filter(code=code).first()
            for q in questions:
                categorie = CategorieBanque.objects.filter(module=module, nom=q['categorie']).first()
                if not categorie:
                    self.stdout.write(f"CATEGORIE MANQUANTE: [{code}] '{q['categorie']}'")
                    continue
                if not QuestionBanque.objects.filter(module=module, categorie=categorie, enonce=q['enonce']).exists():
                    self.stdout.write(f"QUESTION ABSENTE: [{code}/{q['categorie']}] {q['enonce'][:60]}")