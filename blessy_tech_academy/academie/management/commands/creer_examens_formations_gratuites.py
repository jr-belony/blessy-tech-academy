"""
Commande Django : crée un examen final pour les 3 formations gratuites
de l'École des Compétences Fondamentales.
Usage : python manage.py creer_examens_formations_gratuites
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from academie.models import Formation, Examen, Competence
from datetime import timedelta

DATE_DISPONIBILITE = timezone.now()
DATE_EXPIRATION = DATE_DISPONIBILITE + timedelta(days=365 * 2)

class Command(BaseCommand):
    help = "Crée des examens finaux pour les formations gratuites"

    def get_formation(self, nom):
        try:
            return Formation.objects.get(nom__iexact=nom, ecole__nom__icontains="Fondamentales")
        except Formation.DoesNotExist:
            self.stdout.write(self.style.WARNING(f"  ⚠️ Formation introuvable : '{nom}'"))
            return None

    def get_competences(self, noms):
        competences = []
        for nom in noms:
            try:
                comp = Competence.objects.get(nom__iexact=nom)
                competences.append(comp)
            except Competence.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"  ⚠️ Compétence introuvable : '{nom}'"))
        return competences

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("📝 CRÉATION DES EXAMENS POUR FORMATIONS GRATUITES")
        self.stdout.write("=" * 60)

        examens_data = [
            {
                "formation_nom": "Réussir dans le Numérique 2026 : Orientation & Fondamentaux",
                "titre": "Examen Final — Orientation & Fondamentaux Numériques",
                "duree_minutes": 45,
                "seuil_reussite": 70,
                "competences_evaluees": "Compréhension du paysage numérique, culture IA, initiation Python, compétences fondamentales.",
                "competences_noms": [
                    "Culture numérique générale",
                    "Culture de l'intelligence artificielle",
                    "Initiation à la programmation Python"
                ]
            },
            {
                "formation_nom": "Découverte de l'IA : Comprendre l'Intelligence Artificielle en 2026",
                "titre": "Examen Final — Découverte de l'IA",
                "duree_minutes": 45,
                "seuil_reussite": 70,
                "competences_evaluees": "Compréhension du fonctionnement des IA génératives, usages et risques.",
                "competences_noms": [
                    "Culture de l'intelligence artificielle"
                ]
            },
            {
                "formation_nom": "Marketing Digital : les Fondamentaux 2026",
                "titre": "Examen Final — Marketing Digital Fondamental",
                "duree_minutes": 45,
                "seuil_reussite": 70,
                "competences_evaluees": "Connaissance des canaux du marketing digital, stratégie de contenu organique.",
                "competences_noms": [
                    "Culture marketing digital"
                ]
            }
        ]

        total_examens = 0
        for data in examens_data:
            formation = self.get_formation(data["formation_nom"])
            if not formation:
                continue

            competences_liees = self.get_competences(data["competences_noms"])

            examen, created = Examen.objects.get_or_create(
                formation=formation,
                titre=data["titre"],
                defaults={
                    "duree_minutes": data["duree_minutes"],
                    "seuil_reussite": data["seuil_reussite"],
                    "tentatives_max": 2,
                    "competences_evaluees": data["competences_evaluees"],
                    "type_evaluation": "EXAMEN_FINAL",
                    "actif": True,
                    "prerequis": "Avoir suivi tous les modules de la formation.",
                    "conditions_utilisation": "Examen individuel sans documentation externe.",
                    "xp_recompense": 25,
                    "certificat_automatique": True,
                    "date_disponibilite": DATE_DISPONIBILITE,
                    "date_expiration": DATE_EXPIRATION,
                }
            )
            if created:
                examen.competences_liees.set(competences_liees)
                self.stdout.write(self.style.SUCCESS(f"✅ Examen créé : {examen.titre}"))
                total_examens += 1
            else:
                self.stdout.write(f"🔄 Examen existant : {examen.titre}")

        self.stdout.write(self.style.SUCCESS(f"\n✅ {total_examens} examens créés pour les formations gratuites."))