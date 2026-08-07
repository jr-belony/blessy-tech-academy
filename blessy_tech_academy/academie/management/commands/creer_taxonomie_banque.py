# ================================================
# CREER_TAXONOMIE_BANQUE.PY — Structure taxonomique uniquement
# Usage : python manage.py creer_taxonomie_banque
# Crée les Modules + Catégories (structure), PAS les 900 questions
# ================================================

from django.core.management.base import BaseCommand
from academie.models_banque import ModuleBanque, CategorieBanque


class Command(BaseCommand):
    help = "Crée la taxonomie officielle (Modules + Catégories) de la Banque de Questions"

    def handle(self, *args, **options):
        taxonomie = {
            'INT': {
                'nom': 'Internet, Recherche et Productivité', 'icone': '🌐', 'ordre': 1,
                'categories': ['Navigation Web', 'Recherche avancée', 'Opérateurs de recherche', 'Sécurité numérique', 'Productivité', 'Google Workspace', 'Organisation des fichiers', 'Collaboration'],
            },
            'IA': {
                'nom': 'Intelligence Artificielle', 'icone': '🤖', 'ordre': 2,
                'categories': ['Fondamentaux', 'IA générative', 'Prompt Engineering', 'Éthique', 'Vérification des réponses', 'Cas professionnels', 'Automatisation'],
            },
            'BUR': {
                'nom': 'Bureautique Professionnelle', 'icone': '📊', 'ordre': 3,
                'categories': ['Microsoft Word', 'Microsoft Excel', 'Microsoft PowerPoint', 'Gestion des fichiers', 'Productivité', 'Raccourcis clavier', 'Mise en page', 'Impression'],
            },
            'STK': {
                'nom': 'Gestion de Stock avec Excel', 'icone': '📦', 'ordre': 4,
                'categories': ['Suivi des stocks', 'Formules Excel avancées', 'Tableaux croisés dynamiques', 'Alertes et seuils'],
                'hors_examen_principal': True,
            },
        }

        for code, data in taxonomie.items():
            module, _ = ModuleBanque.objects.get_or_create(
                code=code,
                defaults={
                    'nom': data['nom'],
                    'icone': data['icone'],
                    'ordre': data['ordre'],
                    'hors_examen_principal': data.get('hors_examen_principal', False)
                }
            )
            for i, nom_cat in enumerate(data['categories']):
                CategorieBanque.objects.get_or_create(
                    module=module,
                    nom=nom_cat,
                    defaults={'ordre': i}
                )

        self.stdout.write(self.style.SUCCESS("✅ Taxonomie créée : 4 modules, catégories associées"))