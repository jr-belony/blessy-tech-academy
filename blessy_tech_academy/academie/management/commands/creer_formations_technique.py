"""
Commande Django : crée les 7 formations de l'École Technique.
Usage : python manage.py creer_formations_technique
"""

from django.core.management.base import BaseCommand
from django.utils.text import slugify
from academie.models import Formation, Ecole


class Command(BaseCommand):
    help = "Crée les formations de l'École Technique"

    def handle(self, *args, **options):
        ecole = Ecole.objects.get(nom__icontains="Technique")
        self.stdout.write(self.style.SUCCESS(f"✅ École trouvée : {ecole.nom}"))

        formations_data = [
            {
                "nom": "Technicien(ne) en Maintenance Informatique — Certificat Professionnel",
                "icone": "🔧",
                "description": "Formation certifiante au diagnostic, à la réparation et à l'entretien des ordinateurs de bureau et portables.",
                "duree": 80, "duree_unite": "heures", "prix": 115.00, "niveau": "debutant",
                "public_cible": "Passionnés d'informatique, jeunes en réorientation professionnelle, futurs techniciens indépendants.",
                "methode_pedagogique": "Cours + ateliers pratiques sur matériel réel.",
                "criteres_evaluation": "Examen final pratique noté sur le diagnostic, la réparation et la documentation.",
                "debouches": "Technicien informatique en entreprise, école, institution, ou activité indépendante.",
                "competences_acquises": "Diagnostic matériel, installation de systèmes d'exploitation, maintenance préventive, documentation technique.",
                "badge_associe": "Certifié Maintenance Informatique",
                "gratuit": False, "actif": True,
            },
            {
                "nom": "Installation & Configuration Windows / Logiciels",
                "icone": "💻",
                "description": "Formation pratique à l'installation et à la configuration de Windows et des logiciels courants.",
                "duree": 20, "duree_unite": "heures", "prix": 54.00, "niveau": "debutant",
                "public_cible": "Futurs techniciens, employés IT juniors.",
                "methode_pedagogique": "Ateliers pratiques.",
                "criteres_evaluation": "Évaluation pratique par l'installation complète et fonctionnelle d'un poste.",
                "debouches": "Compétence directement utile en support technique et maintenance.",
                "competences_acquises": "Installation de systèmes d'exploitation, gestion des pilotes et mises à jour, configuration logicielle.",
                "badge_associe": "Certifié Déploiement Windows",
                "gratuit": False, "actif": True,
            },
            {
                "nom": "Diagnostic & Dépannage PC : Techniques Professionnelles",
                "icone": "🔍",
                "description": "Formation aux méthodes professionnelles de diagnostic pour identifier et résoudre rapidement les pannes.",
                "duree": 24, "duree_unite": "heures", "prix": 62.00, "niveau": "intermediaire",
                "public_cible": "Techniciens en formation, employés de support technique.",
                "methode_pedagogique": "Ateliers pratiques par études de cas.",
                "criteres_evaluation": "Examen pratique noté sur la méthode, le temps de résolution et la documentation.",
                "debouches": "Technicien de dépannage en entreprise ou en activité indépendante.",
                "competences_acquises": "Méthodologie de diagnostic, résolution de problèmes techniques.",
                "badge_associe": "Certifié Diagnostic PC",
                "gratuit": False, "actif": True,
            },
            {
                "nom": "Réseaux Informatiques : Fondamentaux & Administration (TCP/IP)",
                "icone": "🌐",
                "description": "Formation aux fondamentaux des réseaux informatiques : configuration de réseaux locaux, adressage IP et protocoles TCP/IP.",
                "duree": 40, "duree_unite": "heures", "prix": 92.00, "niveau": "intermediaire",
                "public_cible": "Techniciens en progression, futurs administrateurs systèmes.",
                "methode_pedagogique": "Cours + travaux pratiques en laboratoire réseau.",
                "criteres_evaluation": "Examen pratique noté sur la configuration et le diagnostic d'un réseau.",
                "debouches": "Technicien réseau, poste d'entrée en administration systèmes.",
                "competences_acquises": "Réseaux TCP/IP, configuration réseau, diagnostic de connectivité.",
                "badge_associe": "Certifié Réseaux TCP/IP",
                "gratuit": False, "actif": True,
            },
            {
                "nom": "Administration Systèmes Windows Server",
                "icone": "🖥️",
                "description": "Formation à l'installation, la configuration et l'administration d'un serveur Windows Server.",
                "duree": 40, "duree_unite": "heures", "prix": 115.00, "niveau": "avance",
                "public_cible": "Techniciens réseau en progression, futurs administrateurs systèmes.",
                "methode_pedagogique": "Cours + travaux pratiques en environnement serveur.",
                "criteres_evaluation": "Examen pratique noté sur la configuration, la sécurité et la documentation.",
                "debouches": "Administrateur systèmes junior en PME, école ou institution.",
                "competences_acquises": "Administration Windows Server, gestion des comptes et permissions, sécurité de base des serveurs.",
                "badge_associe": "Certifié Windows Server",
                "gratuit": False, "actif": True,
            },
            {
                "nom": "Virtualisation & Cloud Computing (VMware / Hyper-V)",
                "icone": "☁️",
                "description": "Formation à la création et gestion de machines virtuelles avec VMware et Hyper-V, et introduction au cloud computing.",
                "duree": 30, "duree_unite": "heures", "prix": 108.00, "niveau": "avance",
                "public_cible": "Administrateurs systèmes en progression, techniciens souhaitant se spécialiser.",
                "methode_pedagogique": "Cours + travaux pratiques en environnement virtualisé.",
                "criteres_evaluation": "Examen pratique noté sur la configuration de l'environnement virtualisé.",
                "debouches": "Administrateur infrastructure/cloud junior.",
                "competences_acquises": "Virtualisation (VMware, Hyper-V), culture cloud computing, gestion d'infrastructure virtualisée.",
                "badge_associe": "Certifié Virtualisation & Cloud",
                "gratuit": False, "actif": True,
            },
            {
                "nom": "Support Technique IT / Helpdesk Professionnel",
                "icone": "🎧",
                "description": "Formation aux métiers du support technique et du helpdesk : gestion des tickets et résolution de premier niveau.",
                "duree": 20, "duree_unite": "heures", "prix": 62.00, "niveau": "intermediaire",
                "public_cible": "Techniciens en fin de parcours technique, candidats à un poste de support IT.",
                "methode_pedagogique": "Cours + mises en situation.",
                "criteres_evaluation": "Évaluation par mise en situation notée sur la résolution et la communication.",
                "debouches": "Agent de support technique / helpdesk en entreprise.",
                "competences_acquises": "Gestion de tickets, communication avec utilisateurs non techniques, résolution d'incidents.",
                "badge_associe": "Certifié Helpdesk Pro",
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
            f"\n📊 Total : {Formation.objects.filter(ecole=ecole).count()} formations dans l'École Technique"
        ))