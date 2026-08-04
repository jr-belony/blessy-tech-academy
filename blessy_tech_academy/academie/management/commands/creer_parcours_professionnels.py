"""
Commande Django : crée les 4 parcours professionnels signature
et y associe les formations correspondantes.
Prix = somme des formations - remise parcours (10-15%) + bonus exclusifs.
Usage : python manage.py creer_parcours_professionnels
"""

from django.core.management.base import BaseCommand
from django.utils.text import slugify
from academie.models import Parcours, Formation, Ecole
from decimal import Decimal


class Command(BaseCommand):
    help = "Crée les 4 parcours professionnels signature de Blessy Tech Academy"

    def get_formations(self, noms):
        """Récupère une liste de formations par leurs noms exacts."""
        formations = []
        for nom in noms:
            try:
                f = Formation.objects.get(nom__iexact=nom)
                formations.append(f)
            except Formation.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"  ⚠️ Formation introuvable : '{nom}'"))
            except Formation.MultipleObjectsReturned:
                f = Formation.objects.filter(nom__iexact=nom).first()
                formations.append(f)
                self.stdout.write(self.style.WARNING(f"  ⚠️ Plusieurs formations pour '{nom}', première prise."))
        return formations

    def calculer_prix_parcours(self, formations, remise_pct):
        """Calcule le prix du parcours : somme - remise%."""
        somme = sum(f.prix for f in formations)
        remise = somme * Decimal(remise_pct) / Decimal(100)
        prix_final = somme - remise
        return somme, remise, prix_final

    def handle(self, *args, **options):
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("🚀 CRÉATION DES 4 PARCOURS PROFESSIONNELS SIGNATURE")
        self.stdout.write("Blessy Tech Academy — 2026-2027")
        self.stdout.write("=" * 60)

        # ============================================================
        # PARCOURS 1 : Expert en Intelligence Artificielle
        # ============================================================
        self.stdout.write("\n📌 PARCOURS 1/4 : EXPERT EN IA & PRODUCTIVITÉ NUMÉRIQUE")
        self.stdout.write("-" * 40)

        formations_ia = self.get_formations([
            "IA pour la Productivité Personnelle & Professionnelle",
            "Prompt Engineering Professionnel : Maîtriser les IA Génératives",
            "Automatisation Intelligente : IA + No-Code (Zapier, Make, n8n)",
            "Intelligence Artificielle pour les Entreprises : Stratégie & Cas d'Usage",
            "Python Professionnel : de Zéro à Développeur",
            "Développeur d'Applications IA (Python + LLM)",
            "IA Générative Avancée : LLM & Agents Autonomes",
        ])

        somme_ia, remise_ia, prix_ia = self.calculer_prix_parcours(formations_ia, 15)
        self.stdout.write(f"  💰 Prix séparé : {somme_ia} USD | Remise 15% : -{remise_ia:.2f} USD | Prix final : {prix_ia:.2f} USD")

        parcours_ia, created = Parcours.objects.get_or_create(
            slug="expert-ia-productivite-numerique",
            defaults={
                "titre": "Expert en Intelligence Artificielle & Productivité Numérique",
                "icone": "🤖",
                "description": "Le parcours signature de Blessy Tech Academy pour devenir un professionnel de l'IA appliquée, de l'usage quotidien au développement d'agents autonomes.",
                "duree": 260,
                "duree_unite": "heures",
                "prix": prix_ia,
                "metiers_vises": "Spécialiste IA en entreprise, prompt engineer, consultant en automatisation, développeur d'applications IA, architecte d'agents IA.",
                "projets_inclus": "7 projets : du livrable professionnel assisté par IA à l'agent autonome déployé.",
                "certifications_incluses": "Certificat de Parcours BTA — Expert en Intelligence Artificielle & Productivité Numérique",
                "actif": True,
                "ordre": 1,
            }
        )
        parcours_ia.formations.set(formations_ia)
        if created:
            self.stdout.write(self.style.SUCCESS(f"  ✅ Parcours créé : {parcours_ia.titre}"))
        else:
            self.stdout.write(f"  🔄 Parcours mis à jour : {parcours_ia.titre}")
        self.stdout.write(f"  → {parcours_ia.formations.count()} formations associées")

        # ============================================================
        # PARCOURS 2 : Développeur Python Full-Stack
        # ============================================================
        self.stdout.write("\n📌 PARCOURS 2/4 : DÉVELOPPEUR PYTHON FULL-STACK")
        self.stdout.write("-" * 40)

        formations_dev = self.get_formations([
            "Git & GitHub Professionnel : Contrôle de Version",
            "Python Professionnel : de Zéro à Développeur",
            "JavaScript Moderne (ES6+)",
            "Développeur Front-End (HTML, CSS, JavaScript, React)",
            "Développeur Back-End avec Django",
            "Développeur d'API REST avec Django REST Framework",
            "Développeur Full Stack Python (Django + React)",
        ])

        somme_dev, remise_dev, prix_dev = self.calculer_prix_parcours(formations_dev, 15)
        self.stdout.write(f"  💰 Prix séparé : {somme_dev} USD | Remise 15% : -{remise_dev:.2f} USD | Prix final : {prix_dev:.2f} USD")

        parcours_dev, created = Parcours.objects.get_or_create(
            slug="developpeur-python-full-stack",
            defaults={
                "titre": "Développeur Python Full-Stack & Applications Web",
                "icone": "💻",
                "description": "Le parcours signature de Blessy Tech Academy pour devenir développeur full stack, du contrôle de version à l'application déployée en production.",
                "duree": 422,
                "duree_unite": "heures",
                "prix": prix_dev,
                "metiers_vises": "Développeur front-end, back-end ou full stack, développeur Python, freelance international.",
                "projets_inclus": "7 projets dont une application full stack déployée en production (projet capstone).",
                "certifications_incluses": "Certificat de Parcours BTA — Développeur Python Full-Stack & Applications Web",
                "actif": True,
                "ordre": 2,
            }
        )
        parcours_dev.formations.set(formations_dev)
        if created:
            self.stdout.write(self.style.SUCCESS(f"  ✅ Parcours créé : {parcours_dev.titre}"))
        else:
            self.stdout.write(f"  🔄 Parcours mis à jour : {parcours_dev.titre}")
        self.stdout.write(f"  → {parcours_dev.formations.count()} formations associées")

        # ============================================================
        # PARCOURS 3 : Logistique, Supply Chain & ERP
        # ============================================================
        self.stdout.write("\n📌 PARCOURS 3/4 : LOGISTIQUE, SUPPLY CHAIN & ERP")
        self.stdout.write("-" * 40)

        formations_log = self.get_formations([
            "Excel Professionnel pour la Gestion des Stocks",
            "Gestion de Stock Professionnelle : Excel, Méthodes Modernes & ERP",
            "Logistique Professionnelle",
            "Supply Chain Management",
            "Odoo ERP",
            "Achats & Approvisionnement",
            "Warehouse Management",
        ])

        somme_log, remise_log, prix_log = self.calculer_prix_parcours(formations_log, 12)
        self.stdout.write(f"  💰 Prix séparé : {somme_log} USD | Remise 12% : -{remise_log:.2f} USD | Prix final : {prix_log:.2f} USD")

        parcours_log, created = Parcours.objects.get_or_create(
            slug="logistique-supply-chain-erp",
            defaults={
                "titre": "Professionnel en Logistique, Supply Chain & ERP",
                "icone": "🚚",
                "description": "Le parcours signature de Blessy Tech Academy pour piloter une chaîne d'approvisionnement complète, d'Excel aux logiciels ERP professionnels.",
                "duree": 223,
                "duree_unite": "heures",
                "prix": prix_log,
                "metiers_vises": "Gestionnaire de stock, agent logistique, responsable supply chain, consultant Odoo, responsable achats, responsable d'entrepôt.",
                "projets_inclus": "7 projets : du fichier de gestion de stock au plan complet d'organisation d'entrepôt.",
                "certifications_incluses": "Certificat de Parcours BTA — Professionnel en Logistique, Supply Chain & ERP",
                "actif": True,
                "ordre": 3,
            }
        )
        parcours_log.formations.set(formations_log)
        if created:
            self.stdout.write(self.style.SUCCESS(f"  ✅ Parcours créé : {parcours_log.titre}"))
        else:
            self.stdout.write(f"  🔄 Parcours mis à jour : {parcours_log.titre}")
        self.stdout.write(f"  → {parcours_log.formations.count()} formations associées")

        # ============================================================
        # PARCOURS 4 : Transformation Digitale & Business Numérique
        # ============================================================
        self.stdout.write("\n📌 PARCOURS 4/4 : TRANSFORMATION DIGITALE & BUSINESS NUMÉRIQUE")
        self.stdout.write("-" * 40)

        formations_biz = self.get_formations([
            "Marketing Digital Professionnel — Certificat Complet",
            "Social Media Marketing : Croissance & Engagement",
            "Publicité Facebook & Instagram Ads",
            "Google Ads Professionnel (SEA)",
            "Intelligence Artificielle pour les Entreprises : Stratégie & Cas d'Usage",
            "E-commerce Professionnel : Créer sa Boutique en Ligne",
            "Freelance & Personal Branding : Vivre de son Expertise en Ligne",
        ])

        somme_biz, remise_biz, prix_biz = self.calculer_prix_parcours(formations_biz, 12)
        self.stdout.write(f"  💰 Prix séparé : {somme_biz} USD | Remise 12% : -{remise_biz:.2f} USD | Prix final : {prix_biz:.2f} USD")

        parcours_biz, created = Parcours.objects.get_or_create(
            slug="transformation-digitale-business-numerique",
            defaults={
                "titre": "Transformation Digitale & Business Numérique",
                "icone": "🚀",
                "description": "Le parcours transversal de Blessy Tech Academy pour piloter la présence digitale complète d'une entreprise, du marketing à l'intelligence artificielle.",
                "duree": 194,
                "duree_unite": "heures",
                "prix": prix_biz,
                "metiers_vises": "Marketeur digital, responsable transformation digitale, responsable e-commerce, consultant en stratégie digitale, freelance.",
                "projets_inclus": "7 projets : de la stratégie marketing complète au profil freelance et boutique en ligne.",
                "certifications_incluses": "Certificat de Parcours BTA — Transformation Digitale & Business Numérique",
                "actif": True,
                "ordre": 4,
            }
        )
        parcours_biz.formations.set(formations_biz)
        if created:
            self.stdout.write(self.style.SUCCESS(f"  ✅ Parcours créé : {parcours_biz.titre}"))
        else:
            self.stdout.write(f"  🔄 Parcours mis à jour : {parcours_biz.titre}")
        self.stdout.write(f"  → {parcours_biz.formations.count()} formations associées")

        # ============================================================
        # RÉCAPITULATIF
        # ============================================================
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("📊 RÉCAPITULATIF DES PARCOURS")
        self.stdout.write("=" * 60)
        for p in Parcours.objects.filter(actif=True).order_by('ordre'):
            self.stdout.write(f"  {p.icone} {p.titre}")
            self.stdout.write(f"     → {p.duree}h · {p.prix:.2f} USD · {p.formations.count()} formations")
        self.stdout.write("=" * 60)
        self.stdout.write(self.style.SUCCESS("✅ 4 parcours professionnels créés avec succès."))