import json
import os
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from academie.models_banque import (
    ModuleBanque, CategorieBanque, SousCategorieBanque,
    QuestionBanque,
)

class Command(BaseCommand):
    help = "Importe un lot de questions depuis un fichier JSON"

    def add_arguments(self, parser):
        parser.add_argument('fichier', type=str, help="Chemin vers le fichier JSON")

    def handle(self, *args, **options):
        chemin = options['fichier']
        if not os.path.exists(chemin):
            self.stdout.write(self.style.ERROR(f"Fichier {chemin} introuvable"))
            return

        with open(chemin, 'r', encoding='utf-8') as f:
            donnees = json.load(f)

        # Récupérer le premier superutilisateur actif (évite MultipleObjectsReturned)
        try:
            createur = User.objects.filter(is_superuser=True, is_active=True).first()
            if not createur:
                self.stdout.write(self.style.WARNING("Aucun superutilisateur actif trouvé, 'cree_par' sera null"))
        except Exception:
            createur = None
            self.stdout.write(self.style.WARNING("Erreur lors de la recherche du superutilisateur, 'cree_par' sera null"))

        # 1. Créer ou récupérer les modules
        modules_crees = {}
        for module_data in donnees.get('modules', []):
            module, _ = ModuleBanque.objects.get_or_create(
                code=module_data['code'],
                defaults={
                    'nom': module_data['nom'],
                    'icone': module_data.get('icone', '📚'),
                    'ordre': module_data.get('ordre', 0),
                    'hors_examen_principal': module_data.get('hors_examen_principal', False),
                }
            )
            modules_crees[module.code] = module

        # 2. Créer ou récupérer les catégories
        categories_crees = {}
        for cat_data in donnees.get('categories', []):
            module = modules_crees.get(cat_data['module_code'])
            if not module:
                self.stdout.write(self.style.WARNING(f"Module {cat_data['module_code']} introuvable, catégorie ignorée"))
                continue
            cat, _ = CategorieBanque.objects.get_or_create(
                module=module,
                nom=cat_data['nom'],
                defaults={'ordre': cat_data.get('ordre', 0)}
            )
            categories_crees[(module.code, cat.nom)] = cat

        # 3. Créer ou récupérer les sous-catégories
        sous_categories_crees = {}
        for sous_data in donnees.get('sous_categories', []):
            module = modules_crees.get(sous_data['module_code'])
            if not module:
                continue
            cat = categories_crees.get((sous_data['module_code'], sous_data['categorie_nom']))
            if not cat:
                self.stdout.write(self.style.WARNING(f"Catégorie {sous_data['categorie_nom']} introuvable, sous-catégorie ignorée"))
                continue
            sous_cat, _ = SousCategorieBanque.objects.get_or_create(
                categorie=cat,
                nom=sous_data['nom']
            )
            sous_categories_crees[(cat.id, sous_cat.nom)] = sous_cat

        # 4. Créer les questions
        questions_creees = 0
        for q_data in donnees.get('questions', []):
            module = modules_crees.get(q_data['module_code'])
            if not module:
                continue
            cat = categories_crees.get((q_data['module_code'], q_data['categorie_nom']))
            if not cat:
                continue
            sous_cat = None
            if 'sous_categorie_nom' in q_data:
                sous_cat = sous_categories_crees.get((cat.id, q_data['sous_categorie_nom']))

            question, cree = QuestionBanque.objects.get_or_create(
                identifiant_unique=q_data.get('identifiant_unique'),
                defaults={
                    'module': module,
                    'categorie': cat,
                    'sous_categorie': sous_cat,
                    'niveau': q_data.get('niveau', 'intermediaire'),
                    'type_question': q_data.get('type_question', 'qcm'),
                    'enonce': q_data['enonce'],
                    'reponses_possibles': q_data.get('reponses_possibles', []),
                    'explication_pedagogique': q_data.get('explication_pedagogique', ''),
                    'temps_conseille_secondes': q_data.get('temps_conseille_secondes', 90),
                    'points_base': q_data.get('points_base', 1.0),
                    'statut': 'active',
                    'cree_par': createur,
                }
            )
            if cree:
                questions_creees += 1

        self.stdout.write(self.style.SUCCESS(
            f"✅ Import terminé : {questions_creees} question(s) créées."
        ))