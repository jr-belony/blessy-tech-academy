"""
Commande Django : crée les 8 formations de l'École de Programmation & Développement.
Usage : python manage.py creer_formations_programmation
"""

from django.core.management.base import BaseCommand
from django.utils.text import slugify
from academie.models import Formation, Ecole


class Command(BaseCommand):
    help = "Crée les formations de l'École de Programmation & Développement"

    def handle(self, *args, **options):
        ecole = Ecole.objects.get(nom__icontains="Programmation")
        self.stdout.write(self.style.SUCCESS(f"✅ École trouvée : {ecole.nom}"))

        formations_data = [
            {
                "nom": "Développeur Front-End (HTML, CSS, JavaScript, React)",
                "icone": "🎨",
                "description": "Formation professionnelle au développement web front-end avec HTML, CSS, JavaScript et React.",
                "duree": 80, "duree_unite": "heures", "prix": 154.00, "niveau": "debutant",
                "public_cible": "Débutants motivés, étudiants en informatique, futurs développeurs front-end ou full stack.",
                "methode_pedagogique": "Cours + développement de projets.",
                "criteres_evaluation": "Examen pratique noté sur la fonctionnalité, la qualité du code et le déploiement.",
                "debouches": "Développeur front-end junior, poste d'entrée vers le développement full stack.",
                "competences_acquises": "HTML/CSS professionnel, JavaScript appliqué, développement React.",
                "badge_associe": "Certifié Front-End Pro",
                "gratuit": False, "actif": True,
            },
            {
                "nom": "Développeur Back-End avec Django",
                "icone": "⚙️",
                "description": "Formation au développement back-end avec Django (Python) : logique serveur, bases de données et création d'API.",
                "duree": 70, "duree_unite": "heures", "prix": 169.00, "niveau": "intermediaire",
                "public_cible": "Développeurs en formation, futurs développeurs full stack.",
                "methode_pedagogique": "Cours + développement de projets.",
                "criteres_evaluation": "Examen pratique noté sur la structure, la sécurité et le fonctionnement.",
                "debouches": "Développeur back-end junior, poste d'entrée vers le développement full stack ou API.",
                "competences_acquises": "Développement back-end Python/Django, modélisation de bases de données, sécurité applicative.",
                "badge_associe": "Certifié Back-End Django Pro",
                "gratuit": False, "actif": True,
            },
            {
                "nom": "Développeur Full Stack Python (Django + React)",
                "icone": "🚀",
                "description": "Formation complète combinant back-end Django et front-end React pour devenir développeur full stack.",
                "duree": 140, "duree_unite": "heures", "prix": 269.00, "niveau": "avance",
                "public_cible": "Développeurs ayant les bases front-end et back-end, futurs freelances internationaux.",
                "methode_pedagogique": "Cours + développement de projet capstone.",
                "criteres_evaluation": "Soutenance et examen pratique notés sur l'architecture, le fonctionnement et le déploiement.",
                "debouches": "Développeur full stack junior à confirmé, en entreprise ou en freelance international.",
                "competences_acquises": "Développement full stack Python/React, architecture d'application web, déploiement en production.",
                "badge_associe": "Certifié Full Stack Pro",
                "gratuit": False, "actif": True,
            },
            {
                "nom": "Python Professionnel : de Zéro à Développeur",
                "icone": "🐍",
                "description": "Formation approfondie au langage Python, de la syntaxe de base à la programmation orientée objet.",
                "duree": 60, "duree_unite": "heures", "prix": 123.00, "niveau": "debutant",
                "public_cible": "Débutants motivés, futurs développeurs back-end ou spécialistes IA.",
                "methode_pedagogique": "Cours + développement de projets.",
                "criteres_evaluation": "Examen pratique noté sur la structure, la lisibilité et le fonctionnement du projet.",
                "debouches": "Porte d'entrée vers le développement back-end, mobile ou l'IA appliquée.",
                "competences_acquises": "Programmation Python avancée, programmation orientée objet, structuration de projets.",
                "badge_associe": "Certifié Python Pro",
                "gratuit": False, "actif": True,
            },
            {
                "nom": "JavaScript Moderne (ES6+)",
                "icone": "📜",
                "description": "Formation à JavaScript moderne (ES6+) : fonctions fléchées, promesses, modules et bonnes pratiques.",
                "duree": 30, "duree_unite": "heures", "prix": 77.00, "niveau": "debutant",
                "public_cible": "Futurs développeurs front-end, développeurs autodidactes souhaitant se structurer.",
                "methode_pedagogique": "Cours + exercices pratiques.",
                "criteres_evaluation": "Évaluation du mini-projet selon la qualité, la lisibilité et le fonctionnement du code.",
                "debouches": "Compétence indispensable pour tout poste de développement web front-end ou full stack.",
                "competences_acquises": "JavaScript moderne (ES6+), programmation asynchrone, modularité du code.",
                "badge_associe": "Certifié JavaScript Pro",
                "gratuit": False, "actif": True,
            },
            {
                "nom": "Développeur Mobile Flutter (iOS & Android)",
                "icone": "📱",
                "description": "Formation au développement d'applications mobiles multiplateformes avec Flutter (iOS et Android).",
                "duree": 70, "duree_unite": "heures", "prix": 185.00, "niveau": "intermediaire",
                "public_cible": "Développeurs souhaitant se spécialiser en mobile, entrepreneurs.",
                "methode_pedagogique": "Cours + développement de projets.",
                "criteres_evaluation": "Examen pratique noté sur le fonctionnement, l'interface et la qualité du code.",
                "debouches": "Développeur mobile junior, en entreprise ou en freelance international.",
                "competences_acquises": "Développement mobile Flutter, conception d'interfaces mobiles, publication sur les stores.",
                "badge_associe": "Certifié Flutter Pro",
                "gratuit": False, "actif": True,
            },
            {
                "nom": "Développeur d'API REST avec Django REST Framework",
                "icone": "🔌",
                "description": "Formation à la conception et sécurisation d'API REST professionnelles avec Django REST Framework.",
                "duree": 30, "duree_unite": "heures", "prix": 108.00, "niveau": "avance",
                "public_cible": "Développeurs back-end en progression, futurs développeurs full stack.",
                "methode_pedagogique": "Cours + développement de projet.",
                "criteres_evaluation": "Examen pratique noté sur la structure, la sécurité et la documentation de l'API.",
                "debouches": "Développeur back-end/API, poste d'entrée vers l'architecture logicielle.",
                "competences_acquises": "Conception d'API REST, sécurité des API, documentation technique.",
                "badge_associe": "Certifié API REST Pro",
                "gratuit": False, "actif": True,
            },
            {
                "nom": "Git & GitHub Professionnel : Contrôle de Version",
                "icone": "🔀",
                "description": "Formation à la maîtrise de Git et GitHub pour gérer les versions de code et collaborer en équipe.",
                "duree": 12, "duree_unite": "heures", "prix": 38.00, "niveau": "debutant",
                "public_cible": "Tout développeur débutant, quel que soit le langage visé.",
                "methode_pedagogique": "Cours + exercices pratiques.",
                "criteres_evaluation": "Évaluation par la réalisation d'une pull request avec résolution d'un conflit simulé.",
                "debouches": "Compétence transversale obligatoire pour tout poste de développement.",
                "competences_acquises": "Contrôle de version avec Git, collaboration via GitHub, résolution de conflits.",
                "badge_associe": "Certifié Git Pro",
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
            f"\n📊 Total : {Formation.objects.filter(ecole=ecole).count()} formations dans l'École de Programmation & Développement"
        ))