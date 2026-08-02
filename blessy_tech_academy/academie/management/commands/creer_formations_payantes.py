from django.core.management.base import BaseCommand
from django.utils.text import slugify
from academie.models import Ecole, Formation

class Command(BaseCommand):
    help = 'Crée les 3 formations payantes de l\'École des Compétences Fondamentales'

    def handle(self, *args, **options):
        self.stdout.write("🚀 Création des formations payantes...")

        ecole = Ecole.objects.get(nom="École des Compétences Fondamentales")
        self.stdout.write(f"✅ École trouvée : {ecole.nom}")

        formations_data = [
            {
                "nom": "Bureautique Professionnelle & Productivité Numérique (Word, Excel, Google Workspace)",
                "description": "Formation professionnelle visant la maîtrise de Word, Excel et Google Workspace pour produire des documents professionnels, gérer des données simples et collaborer efficacement en ligne.",
                "duree": 40,
                "duree_unite": "heures",
                "niveau": "debutant",
                "prix": 46.00,
                "gratuit": False,
                "actif": True,
                "delivre_certificat": True,
                "icone": "📊",
                "public_cible": "Employés administratifs, étudiants, demandeurs d'emploi, professionnels souhaitant consolider leurs bases.",
                "methode_pedagogique": "Cours + travaux pratiques hebdomadaires sur des documents réels.",
                "criteres_evaluation": "Quiz de fin de module, projet final, examen pratique final.",
                "debouches": "Agent administratif, assistant(e) de direction, agent de saisie.",
                "competences_acquises": "Traitement de texte professionnel, tableur et calculs de base, collaboration en ligne.",
                "badge_associe": "Certifié Bureautique Pro",
            },
            {
                "nom": "IA au Quotidien : Productivité avec ChatGPT & Copilot",
                "description": "Formation pratique à l'utilisation quotidienne de ChatGPT et Microsoft Copilot pour la rédaction, la synthèse et l'organisation du travail.",
                "duree": 24,
                "duree_unite": "heures",
                "niveau": "debutant",
                "prix": 38.00,
                "gratuit": False,
                "actif": True,
                "delivre_certificat": True,
                "icone": "🤖",
                "public_cible": "Employés de bureau, étudiants, entrepreneurs.",
                "methode_pedagogique": "Cours + travaux pratiques sur des documents réels.",
                "criteres_evaluation": "Évaluation du mini-projet selon la qualité du document final.",
                "debouches": "Gain de productivité applicable dans tout poste administratif.",
                "competences_acquises": "Prompt de base, productivité augmentée par l'IA.",
                "badge_associe": "Certifié IA Productivité",
            },
            {
                "nom": "Communication & Collaboration Numérique en Entreprise",
                "description": "Formation aux outils de communication et de collaboration professionnelle modernes (Teams, Zoom, e-mail professionnel, messagerie d'équipe).",
                "duree": 20,
                "duree_unite": "heures",
                "niveau": "debutant",
                "prix": 35.00,
                "gratuit": False,
                "actif": True,
                "delivre_certificat": True,
                "icone": "💬",
                "public_cible": "Employés d'entreprise, télétravailleurs, étudiants en stage.",
                "methode_pedagogique": "Mises en situation de réunion en ligne.",
                "criteres_evaluation": "Évaluation par mise en situation notée.",
                "debouches": "Compétence transversale attendue dans tout environnement de travail.",
                "competences_acquises": "Communication professionnelle, travail en équipe à distance.",
                "badge_associe": "Certifié Communication Pro",
            }
        ]

        for data in formations_data:
            base_slug = slugify(data["nom"])
            slug = base_slug
            counter = 1
            while Formation.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            formation, created = Formation.objects.get_or_create(
                slug=slug,
                defaults={**data, "ecole": ecole}
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f"✅ Formation créée : '{formation.nom}'"))
                self.stdout.write(f"   → Durée : {formation.duree} {formation.get_duree_unite_display()}")
                self.stdout.write(f"   → Prix : {formation.prix} USD")
                self.stdout.write(f"   → Badge : {formation.badge_associe}")
            else:
                for key, value in data.items():
                    setattr(formation, key, value)
                formation.ecole = ecole
                formation.save()
                self.stdout.write(self.style.WARNING(f"🔄 Formation mise à jour : '{formation.nom}'"))

        self.stdout.write("\n" + "="*50)
        self.stdout.write("📊 RÉCAPITULATIF DES FORMATIONS PAYANTES")
        self.stdout.write("="*50)
        for f in Formation.objects.filter(gratuit=False, actif=True, ecole=ecole).order_by('nom'):
            self.stdout.write(f"• {f.icone} {f.nom}")
            self.stdout.write(f"  → {f.duree} {f.get_duree_unite_display()} · {f.get_niveau_display()} · {f.prix} USD · Badge : {f.badge_associe}")
            self.stdout.write("")

        self.stdout.write(self.style.SUCCESS("\n✅ Terminé."))