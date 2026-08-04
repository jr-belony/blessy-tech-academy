"""
Commande Django : crée les 6 formations de l'École Intelligence Artificielle.
Usage : python manage.py creer_formations_ia
"""

from django.core.management.base import BaseCommand
from django.utils.text import slugify
from academie.models import Formation, Ecole


class Command(BaseCommand):
    help = "Crée les formations de l'École Intelligence Artificielle"

    def handle(self, *args, **options):
        ecole = Ecole.objects.get(nom__icontains="Intelligence Artificielle")
        self.stdout.write(self.style.SUCCESS(f"✅ École trouvée : {ecole.nom}"))

        formations_data = [
            {
                "nom": "IA pour la Productivité Personnelle & Professionnelle",
                "icone": "🤖",
                "description": "Formation pratique à l'utilisation des principaux outils d'IA générative pour gagner du temps dans le travail quotidien.",
                "duree": 16, "duree_unite": "heures", "prix": 54.00, "niveau": "debutant",
                "public_cible": "Professionnels de tout secteur, entrepreneurs, étudiants avancés.",
                "methode_pedagogique": "Cours + travaux pratiques.",
                "criteres_evaluation": "Évaluation du mini-projet selon la qualité du livrable final.",
                "debouches": "Gain de productivité directement applicable ; porte d'entrée vers les formations IA avancées.",
                "competences_acquises": "Usage professionnel de l'IA générative, productivité augmentée.",
                "badge_associe": "Certifié IA Productivité",
                "gratuit": False, "actif": True,
            },
            {
                "nom": "Prompt Engineering Professionnel : Maîtriser les IA Génératives",
                "icone": "✍️",
                "description": "Formation à la conception de prompts efficaces et reproductibles pour obtenir des résultats fiables des IA génératives.",
                "duree": 24, "duree_unite": "heures", "prix": 92.00, "niveau": "intermediaire",
                "public_cible": "Professionnels avancés, futurs spécialistes IA, créateurs de contenu.",
                "methode_pedagogique": "Cours + ateliers pratiques.",
                "criteres_evaluation": "Examen pratique noté sur la qualité et la reproductibilité des prompts.",
                "debouches": "Prompt engineer ou référent IA en entreprise.",
                "competences_acquises": "Prompt engineering, méthodologie de conception de prompts, évaluation critique.",
                "badge_associe": "Certifié Prompt Engineer",
                "gratuit": False, "actif": True,
            },
            {
                "nom": "Automatisation Intelligente : IA + No-Code (Zapier, Make, n8n)",
                "icone": "⚡",
                "description": "Formation à l'automatisation de tâches avec des plateformes no-code combinées à l'IA.",
                "duree": 30, "duree_unite": "heures", "prix": 115.00, "niveau": "intermediaire",
                "public_cible": "Entrepreneurs, professionnels souhaitant gagner en efficacité, futurs consultants en automatisation.",
                "methode_pedagogique": "Cours + travaux pratiques.",
                "criteres_evaluation": "Examen pratique noté sur la fiabilité et la pertinence du flux d'automatisation.",
                "debouches": "Consultant en automatisation, spécialiste opérations/productivité.",
                "competences_acquises": "Automatisation no-code, intégration d'API simples, IA appliquée à l'automatisation.",
                "badge_associe": "Certifié Automatisation IA",
                "gratuit": False, "actif": True,
            },
            {
                "nom": "Intelligence Artificielle pour les Entreprises : Stratégie & Cas d'Usage",
                "icone": "🏢",
                "description": "Formation pour dirigeants et responsables : intégrer l'IA dans la stratégie d'entreprise avec ROI et conduite du changement.",
                "duree": 20, "duree_unite": "heures", "prix": 138.00, "niveau": "intermediaire",
                "public_cible": "Dirigeants, responsables d'équipe, chefs de projet, décideurs.",
                "methode_pedagogique": "Cours + étude de cas d'entreprise.",
                "criteres_evaluation": "Évaluation par présentation du plan d'intégration IA.",
                "debouches": "Référent IA en entreprise, consultant en stratégie IA.",
                "competences_acquises": "Stratégie IA en entreprise, évaluation de ROI, conduite du changement.",
                "badge_associe": "Certifié Stratégie IA Entreprise",
                "gratuit": False, "actif": True,
            },
            {
                "nom": "Développeur d'Applications IA (Python + LLM)",
                "icone": "🧠",
                "description": "Formation au développement d'applications intégrant des LLM avec Python : chatbots, assistants et outils d'analyse.",
                "duree": 60, "duree_unite": "heures", "prix": 215.00, "niveau": "avance",
                "public_cible": "Développeurs souhaitant se spécialiser en IA, diplômés en informatique.",
                "methode_pedagogique": "Cours + développement de projets.",
                "criteres_evaluation": "Examen pratique noté sur le fonctionnement, la qualité du code et la documentation.",
                "debouches": "Développeur d'applications IA, ingénieur IA junior, freelance international.",
                "competences_acquises": "Développement Python appliqué à l'IA, intégration d'API de LLM, conception d'applications IA.",
                "badge_associe": "Certifié Développeur IA",
                "gratuit": False, "actif": True,
            },
            {
                "nom": "IA Générative Avancée : LLM & Agents Autonomes",
                "icone": "🦾",
                "description": "Formation avancée à la conception d'agents IA autonomes capables d'exécuter des tâches complexes.",
                "duree": 50, "duree_unite": "heures", "prix": 231.00, "niveau": "avance",
                "public_cible": "Développeurs IA expérimentés, ingénieurs IA en spécialisation avancée.",
                "methode_pedagogique": "Cours + développement de projet avancé.",
                "criteres_evaluation": "Examen pratique noté sur l'architecture, la fiabilité et la documentation.",
                "debouches": "Architecte d'agents IA, ingénieur IA senior, spécialiste systèmes autonomes.",
                "competences_acquises": "Architecture d'agents IA, orchestration d'outils multiples, évaluation de systèmes autonomes.",
                "badge_associe": "Certifié Agents IA Avancés",
                "gratuit": False, "actif": True,
            },
        ]

        for data in formations_data:
            slug = slugify(data["nom"])
            formation, created = Formation.objects.get_or_create(
                slug=slug,
                defaults={**data, "ecole": ecole}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"✅ Formation créée : {formation.nom}"))
            else:
                for key, value in data.items():
                    setattr(formation, key, value)
                formation.ecole = ecole
                formation.save()
                self.stdout.write(f"🔄 Formation mise à jour : {formation.nom}")

        self.stdout.write(self.style.SUCCESS(
            f"\n📊 Total : {Formation.objects.filter(ecole=ecole).count()} formations dans l'École Intelligence Artificielle"
        ))