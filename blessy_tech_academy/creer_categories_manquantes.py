import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blessy_tech_academy.settings')
import django
django.setup()

from academie.models_banque import ModuleBanque, CategorieBanque

categories_par_module = {
    'INT': [
        'Navigation Web', 'Recherche avancée', 'Opérateurs de recherche',
        'Sécurité numérique', 'Google Workspace', 'Organisation des fichiers',
        'Collaboration', 'Productivité',
    ],
    'IA': [
        'Fondamentaux', 'IA générative', 'Prompt Engineering',
        'Éthique', 'Vérification des réponses', 'Cas professionnels',
        'Automatisation',
    ],
    'BUR': [
        'Microsoft Word', 'Microsoft Excel', 'Microsoft PowerPoint',
        'Gestion des fichiers', 'Raccourcis clavier', 'Mise en page',
        'Impression', 'Productivité',
    ],
}

total_creees = 0
for code, categories in categories_par_module.items():
    module = ModuleBanque.objects.filter(code=code).first()
    if not module:
        print(f"❌ Module {code} introuvable")
        continue
    for nom in categories:
        obj, created = CategorieBanque.objects.get_or_create(
            module=module, nom=nom,
            defaults={'description': f'Catégorie {nom} pour le module {code}'}
        )
        if created:
            print(f"✅ Catégorie créée : {code} / {nom}")
            total_creees += 1
        else:
            print(f"🔄 Catégorie existante : {code} / {nom}")

print(f"\n🎉 {total_creees} catégories créées.")