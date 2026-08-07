# ================================================
# LANCER_TEST_PILOTE_BANQUE.PY — Active le gabarit officiel en mode test pilote
# Usage : python manage.py lancer_test_pilote_banque
# ================================================

from django.core.management.base import BaseCommand
from academie.models_banque import GabaritExamen
from academie.models import Cohorte


class Command(BaseCommand):
    help = "Active le gabarit d'examen officiel en mode test avec la Cohorte Pilote"

    def handle(self, *args, **options):
        cohorte = Cohorte.objects.filter(nom='Cohorte Pilote 2026').first()
        if not cohorte:
            self.stdout.write(self.style.ERROR("❌ Cohorte Pilote 2026 introuvable"))
            return

        gabarit = GabaritExamen.objects.filter(nom='Examen de Certification Officiel BTA').first()
        if not gabarit:
            self.stdout.write(self.style.ERROR("❌ Gabarit officiel introuvable — lance d'abord creer_gabarit_examen_officiel"))
            return

        gabarit.cohorte_pilote = cohorte
        gabarit.phase_test = True
        gabarit.save()

        self.stdout.write(self.style.SUCCESS(
            f"✅ Gabarit '{gabarit.nom}' activé en mode TEST pour '{cohorte.nom}' "
            f"({cohorte.nb_inscrits()} participant(s))\n"
            f"⚠️ Chaque membre peut maintenant passer l'examen via /examen-banque/{gabarit.id}/demarrer/"
        ))