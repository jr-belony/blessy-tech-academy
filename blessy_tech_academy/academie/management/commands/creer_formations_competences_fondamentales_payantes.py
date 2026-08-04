"""
Commande Django : crée les 3 formations payantes de l'École des Compétences Fondamentales.
Usage : python manage.py creer_formations_fondamentales_payantes
"""

from django.core.management.base import BaseCommand
from django.utils.text import slugify
from academie.models import Formation, Ecole


class Command(BaseCommand):
    help = "Crée les 3 formations payantes de l'École des Compétences Fondamentales"

    def handle(self, *args, **options):
        ecole = Ecole.objects.get(nom__icontains="Fondamentales")
        self.stdout.write(self.style.SUCCESS(f"✅ École trouvée : {ecole.nom}"))

        formations_data = [
            {
                "nom": "Bureautique Professionnelle & Productivité Numérique (Word, Excel, Google Workspace)",
                "icone": "📎",
                "description": "Formation professionnelle à la maîtrise de Word, Excel et Google Workspace pour produire des documents professionnels et collaborer efficacement.",
                "duree": 30, "duree_unite": "heures", "prix": 46.00, "niveau": "debutant",
                "public_cible": "Employés administratifs, étudiants, demandeurs d'emploi, professionnels souhaitant consolider leurs bases.",
                "methode_pedagogique": "Cours + travaux pratiques hebdomadaires.",
                "criteres_evaluation": "Quiz de fin de module, projet final et examen pratique noté.",
                "debouches": "Agent administratif, assistant de direction, agent de saisie, tout poste de bureau.",
                "competences_acquises": "Traitement de texte professionnel, tableur et calculs de base, collaboration en ligne, productivité avec l'IA.",
                "badge_associe": "Certifié Bureautique Pro",
                "gratuit": False, "actif": True,
            },
            {
                "nom": "Communication & Collaboration Numérique en Entreprise",
                "icone": "💬",
                "description": "Formation aux outils de communication et de collaboration professionnelle modernes (Teams, Zoom, e-mail, messagerie d'équipe).",
                "duree": 14, "duree_unite": "heures", "prix": 35.00, "niveau": "debutant",
                "public_cible": "Employés d'entreprise, télétravailleurs, étudiants en stage.",
                "methode_pedagogique": "Cours + mises en situation.",
                "criteres_evaluation": "Évaluation par mise en situation notée (réunion simulée et e-mail rédigé).",
                "debouches": "Compétence transversale attendue dans tout environnement de travail moderne.",
                "competences_acquises": "Communication professionnelle écrite et orale, travail en équipe à distance, étiquette numérique.",
                "badge_associe": "Certifié Collaboration Numérique",
                "gratuit": False, "actif": True,
            },
            {
                "nom": "Cybersécurité au Quotidien : Protéger ses Données",
                "icone": "🔒",
                "description": "Formation de sensibilisation à la cybersécurité personnelle et professionnelle : hameçonnage, mots de passe, protection des données.",
                "duree": 12, "duree_unite": "heures", "prix": 38.00, "niveau": "debutant",
                "public_cible": "Grand public, employés d'entreprise, professionnels manipulant des données sensibles.",
                "methode_pedagogique": "Cours + mises en situation.",
                "criteres_evaluation": "Quiz final sur la reconnaissance des menaces et les bonnes pratiques.",
                "debouches": "Compétence transversale de protection personnelle et professionnelle.",
                "competences_acquises": "Cybersécurité de base, esprit critique face aux menaces numériques.",
                "badge_associe": "Certifié Cybersécurité Quotidien",
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
            f"\n📊 Total : {Formation.objects.filter(ecole=ecole).count()} formations dans l'École des Compétences Fondamentales"
        ))