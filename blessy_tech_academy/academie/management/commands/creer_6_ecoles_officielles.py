# ================================================
# CREER_6_ECOLES_OFFICIELLES.PY — Seed architecture académique officielle
# Usage : python manage.py creer_6_ecoles_officielles
# Idempotent (get_or_create) — safe à relancer plusieurs fois
# ================================================

from django.core.management.base import BaseCommand
from academie.models import Ecole, Academie


class Command(BaseCommand):
    help = "Crée les 6 écoles officielles de Blessy Tech Academy avec marquage des écoles phares"

    def handle(self, *args, **options):
        academie_defaut = Academie.objects.filter(est_academie_par_defaut=True).first()

        ecoles_data = [
            {
                'nom': 'École des Compétences Fondamentales', 'icone': '📘', 'ordre': 1,
                'description_courte': "Les bases indispensables pour bien démarrer dans le numérique.",
                'est_ecole_phare': False,
            },
            {
                'nom': 'École Technique', 'icone': '🔧', 'ordre': 2,
                'description_courte': "Maintenance, réseaux et support informatique professionnel.",
                'est_ecole_phare': False,
            },
            {
                'nom': 'École Intelligence Artificielle', 'icone': '🤖', 'ordre': 3,
                'description_courte': "Maîtrise les outils IA qui transforment déjà le marché du travail.",
                'est_ecole_phare': True,
            },
            {
                'nom': 'École de Programmation & Développement', 'icone': '💻', 'ordre': 4,
                'description_courte': "Deviens développeur — Python, Web, applications réelles.",
                'est_ecole_phare': True,
            },
            {
                'nom': 'École de Logistique, Supply Chain & ERP', 'icone': '📦', 'ordre': 5,
                'description_courte': "Gestion de stock, chaîne logistique et outils ERP professionnels.",
                'est_ecole_phare': True,
            },
            {
                'nom': 'École Business Numérique', 'icone': '📊', 'ordre': 6,
                'description_courte': "Marketing digital, entrepreneuriat et outils business modernes.",
                'est_ecole_phare': False,
            },
        ]

        creees, mises_a_jour = 0, 0
        for data in ecoles_data:
            ecole, cree = Ecole.objects.get_or_create(
                nom=data['nom'],
                defaults={**data, 'academie': academie_defaut}
            )
            if cree:
                creees += 1
            else:
                # Met à jour les champs même si l'école existe déjà (idempotent)
                for champ, valeur in data.items():
                    setattr(ecole, champ, valeur)
                if academie_defaut and not ecole.academie:
                    ecole.academie = academie_defaut
                ecole.save()
                mises_a_jour += 1

        self.stdout.write(self.style.SUCCESS(
            f"✅ {creees} école(s) créée(s), {mises_a_jour} mise(s) à jour\n"
            f"⭐ Écoles phares : IA, Programmation & Développement, Logistique/ERP"
        ))