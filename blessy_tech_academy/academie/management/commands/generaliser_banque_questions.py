# ================================================
# GENERALISER_BANQUE_QUESTIONS.PY — Sortie propre de la phase test pilote
# Usage : python manage.py generaliser_banque_questions
# À exécuter UNIQUEMENT après analyse du dashboard et correction 
# des questions signalées
# ================================================

from django.core.management.base import BaseCommand
from academie.models_banque import GabaritExamen, QuestionBanque


class Command(BaseCommand):
    help = "Désactive le mode test pilote — la banque devient officielle pour toutes les cohortes futures"

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help="Ignore les questions encore en_revision")

    def handle(self, *args, **options):
        questions_en_revision = QuestionBanque.objects.filter(statut='en_revision').count()

        if questions_en_revision > 0 and not options['force']:
            self.stdout.write(self.style.WARNING(
                f"⚠️ {questions_en_revision} question(s) encore en statut 'en_revision' — "
                f"corrige-les d'abord dans l'admin, ou relance avec --force pour ignorer."
            ))
            return

        gabarit = GabaritExamen.objects.filter(phase_test=True).first()
        if not gabarit:
            self.stdout.write(self.style.ERROR("❌ Aucun gabarit en phase test trouvé"))
            return

        gabarit.phase_test = False
        gabarit.save()

        self.stdout.write(self.style.SUCCESS(
            f"🎉 Banque de questions GÉNÉRALISÉE avec succès !\n"
            f"   Gabarit '{gabarit.nom}' est maintenant disponible pour toutes les cohortes futures.\n"
            f"   Prêt pour l'Étape 4 : extension vers 300 questions."
        ))