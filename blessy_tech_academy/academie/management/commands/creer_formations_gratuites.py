from django.core.management.base import BaseCommand
from django.utils.text import slugify
from academie.models import Ecole, Formation

class Command(BaseCommand):
    help = 'Crée les 3 formations gratuites du catalogue officiel 2026-2027 (durées optimisées)'

    def handle(self, *args, **options):
        self.stdout.write("🚀 Création des formations gratuites...")

        # ---------- 1. Récupérer ou créer l'école ----------
        ecole_nom = "École des Compétences Fondamentales"
        ecole, created = Ecole.objects.get_or_create(
            nom=ecole_nom,
            defaults={
                'icone': '🧠',
                'description': 'Le socle numérique et professionnel commun.',
                'ordre': 1,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"✅ École '{ecole_nom}' créée."))
        else:
            self.stdout.write(f"✅ École '{ecole_nom}' trouvée.")

        # ---------- 2. Définir les 3 formations ----------
        formations_data = [
            {
                "nom": "Réussir dans le Numérique 2026 : Orientation & Fondamentaux",
                "description": "Atelier d'orientation structuré autour des compétences numériques attendues en 2026. Aide à situer son niveau et à choisir une trajectoire de formation cohérente.",
                "duree": 8,
                "duree_unite": "heures",
                "niveau": "debutant",
                "prix": 0,
                "gratuit": True,
                "actif": True,
                "delivre_certificat": False,
                "icone": "🧭",
                "public_cible": "Toute personne en réflexion sur son orientation numérique.",
                "methode_pedagogique": "Atelier collectif interactif avec exercices d'auto-évaluation.",
                "criteres_evaluation": "Validation par la remise du plan de formation personnel.",
                "debouches": "Orientation éclairée vers une formation ou un parcours BTA.",
                "competences_acquises": "Culture numérique générale, auto-évaluation, orientation.",
            },
            {
                "nom": "Découverte de l'IA : Comprendre l'Intelligence Artificielle en 2026",
                "description": "Introduction conceptuelle à l'intelligence artificielle contemporaine : fonctionnement des IA génératives, cas d'usage, impact sur le travail.",
                "duree": 8,
                "duree_unite": "heures",
                "niveau": "debutant",
                "prix": 0,
                "gratuit": True,
                "actif": True,
                "delivre_certificat": False,
                "icone": "🤖",
                "public_cible": "Grand public curieux, professionnels non-techniques, enseignants.",
                "methode_pedagogique": "Atelier avec démonstrations et manipulation guidée de ChatGPT.",
                "criteres_evaluation": "Quiz oral collectif de synthèse.",
                "debouches": "Base de culture IA pour IA au Quotidien et parcours IA.",
                "competences_acquises": "Culture IA, esprit critique face aux contenus générés.",
            },
            {
                "nom": "Marketing Digital : les Fondamentaux 2026",
                "description": "Introduction aux fondamentaux du marketing digital : réseaux sociaux, publicité en ligne, création de contenu.",
                "duree": 10,
                "duree_unite": "heures",
                "niveau": "debutant",
                "prix": 0,
                "gratuit": True,
                "actif": True,
                "delivre_certificat": False,
                "icone": "📢",
                "public_cible": "Petits entrepreneurs, futurs freelances, curieux du marketing.",
                "methode_pedagogique": "Atelier collectif avec exercices pratiques et esquisse de stratégie.",
                "criteres_evaluation": "Présentation orale de la stratégie esquissée.",
                "debouches": "Porte d'entrée vers Marketing Digital Professionnel.",
                "competences_acquises": "Culture marketing digital, communication en ligne.",
            },
        ]

        # ---------- 3. Créer ou mettre à jour chaque formation ----------
        for data in formations_data:
            # Générer un slug unique
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
                self.stdout.write(self.style.SUCCESS(
                    f"✅ Formation '{formation.nom}' créée."
                ))
                self.stdout.write(f"   → Durée : {formation.duree} {formation.get_duree_unite_display()}")
            else:
                # Mise à jour des champs (si la formation existe déjà avec un autre slug)
                for key, value in data.items():
                    setattr(formation, key, value)
                formation.ecole = ecole
                formation.save()
                self.stdout.write(self.style.WARNING(
                    f"🔄 Formation '{formation.nom}' mise à jour."
                ))
                self.stdout.write(f"   → Nouvelle durée : {formation.duree} {formation.get_duree_unite_display()}")

        # ---------- 4. Récapitulatif ----------
        self.stdout.write("\n" + "="*50)
        self.stdout.write("📊 RÉCAPITULATIF DES FORMATIONS GRATUITES")
        self.stdout.write("="*50)
        formations = Formation.objects.filter(gratuit=True, actif=True).order_by('nom')
        for f in formations:
            self.stdout.write(
                f"• {f.icone} {f.nom}\n"
                f"  → {f.duree} {f.get_duree_unite_display()} · {f.get_niveau_display()} · "
                f"{f.ecole.nom if f.ecole else 'Sans école'}"
            )
        self.stdout.write("\n✅ Terminé.")