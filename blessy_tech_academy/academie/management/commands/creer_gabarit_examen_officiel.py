# ================================================
# CREER_GABARIT_EXAMEN_OFFICIEL.PY — Composition exacte demandée
# 20 Internet + 15 IA + 15 Bureautique = 50 questions, 90 min, 60 points
# ================================================

from django.core.management.base import BaseCommand
from academie.models_banque import ModuleBanque, GabaritExamen, CompositionGabarit


class Command(BaseCommand):
    help = "Crée le gabarit d'examen officiel BTA"

    def handle(self, *args, **options):
        # 1. Créer ou récupérer le gabarit
        gabarit, cree = GabaritExamen.objects.get_or_create(
            nom='Examen de Certification Officiel BTA',
            defaults={'duree_minutes': 90, 'seuil_reussite': 70}
        )

        if not cree:
            self.stdout.write(self.style.WARNING("⚠️ Le gabarit existe déjà, mise à jour de la composition si nécessaire."))

        # 2. Composition : (code_module, nombre_questions, points_par_question)
        composition = [
            ('INT', 20, 1.2),   # Internet
            ('IA', 15, 1.2),    # Intelligence Artificielle
            ('BUR', 15, 1.2),   # Bureautique
        ]

        for code, nb, points in composition:
            try:
                module = ModuleBanque.objects.get(code=code)
                comp, created = CompositionGabarit.objects.get_or_create(
                    gabarit=gabarit,
                    module=module,
                    defaults={
                        'nombre_questions': nb,
                        'points_par_question': points
                    }
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f"✅ Ajouté : {nb} questions de {code} ({points} pts/qs)"))
                else:
                    self.stdout.write(self.style.WARNING(f"⚠️ La ligne {code} existe déjà, inchangée."))
            except ModuleBanque.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"❌ Module {code} introuvable. Vérifiez la taxonomie."))

        # 3. Résumé final
        total_q = gabarit.nombre_questions_total()
        total_pts = gabarit.points_total()
        self.stdout.write(self.style.SUCCESS(
            f"✅ Gabarit final : {total_q} questions, {total_pts} points, "
            f"{gabarit.duree_minutes} min, seuil {gabarit.seuil_reussite}%"
        ))