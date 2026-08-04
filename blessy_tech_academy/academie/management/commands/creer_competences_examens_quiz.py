"""
Commande Django : crée les compétences, examens finaux et quiz de module
pour les formations des écoles Business Numérique et Logistique.
Usage : python manage.py creer_competences_examens_quiz
"""

from django.core.management.base import BaseCommand
from django.utils.text import slugify
from django.utils import timezone
from django.db import transaction
from academie.models import Formation, Competence, Examen, Quiz, Module
from datetime import timedelta


DATE_DISPONIBILITE = timezone.now()
DATE_EXPIRATION = DATE_DISPONIBILITE + timedelta(days=365 * 2)


class Command(BaseCommand):
    help = "Crée les compétences, examens finaux et quiz pour Business Numérique et Logistique"

    def get_formation(self, nom, ecole_nom):
        try:
            return Formation.objects.get(nom__iexact=nom, ecole__nom__icontains=ecole_nom)
        except Formation.DoesNotExist:
            self.stdout.write(self.style.WARNING(f"  ⚠️ Formation introuvable : '{nom}' dans '{ecole_nom}'"))
            return None
        except Formation.MultipleObjectsReturned:
            return Formation.objects.filter(nom__iexact=nom, ecole__nom__icontains=ecole_nom).first()

    def create_competence(self, nom, categorie, icone, description):
        slug = slugify(nom)
        obj, created = Competence.objects.get_or_create(
            slug=slug,
            defaults={"nom": nom, "categorie": categorie, "icone": icone, "description": description}
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"    ✅ Compétence créée : {obj.nom}"))
        else:
            self.stdout.write(f"    🔄 Compétence existante : {obj.nom}")
        return obj

    def create_examen(self, formation, titre, duree_minutes, seuil_reussite, competences_evaluees, competences_liees):
        if not formation:
            return None
        examen, created = Examen.objects.get_or_create(
            formation=formation,
            titre=titre,
            defaults={
                "duree_minutes": duree_minutes,
                "seuil_reussite": seuil_reussite,
                "tentatives_max": 2,
                "competences_evaluees": competences_evaluees,
                "type_evaluation": "EXAMEN_FINAL",
                "actif": True,
                "prerequis": "Avoir suivi tous les modules de la formation.",
                "conditions_utilisation": "Examen individuel sans documentation externe.",
                "xp_recompense": 100,
                "certificat_automatique": True,
                "date_disponibilite": DATE_DISPONIBILITE,
                "date_expiration": DATE_EXPIRATION,
            }
        )
        if created:
            examen.competences_liees.set(competences_liees)
            self.stdout.write(self.style.SUCCESS(f"    ✅ Examen créé : {examen.titre}"))
        else:
            self.stdout.write(f"    🔄 Examen existant : {examen.titre}")
        return examen

    def create_quiz(self, formation, module_titre, quiz_titre, description, limite_minutes):
        if not formation:
            return None
        module, _ = Module.objects.get_or_create(
            formation=formation,
            titre__iexact=module_titre,
            defaults={"titre": module_titre, "description": f"Module : {module_titre}", "ordre": 1}
        )
        quiz, created = Quiz.objects.get_or_create(
            formation=formation,
            module=module,
            titre=quiz_titre,
            defaults={
                "description": description,
                "actif": True,
                "limite_temps_minutes": limite_minutes,
                "tentatives_max": 3,
                "melanger_questions": True,
                "melanger_reponses": True,
                "type_evaluation": "QUIZ_MODULE",
                "date_creation": DATE_DISPONIBILITE,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"    ✅ Quiz créé : {quiz.titre} (module: {module.titre})"))
        else:
            self.stdout.write(f"    🔄 Quiz existant : {quiz.titre}")
        return quiz

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("🚀 CRÉATION DES COMPÉTENCES, EXAMENS ET QUIZ")
        self.stdout.write("Blessy Tech Academy — Catalogue 2026-2027")
        self.stdout.write("=" * 60)

        # ---- ÉTAPE 1 : Compétences ----
        self.stdout.write("\n📌 ÉTAPE 1/3 : CRÉATION DES COMPÉTENCES")
        self.stdout.write("-" * 40)

        COMPETENCES_DATA = [
            {"nom": "Stratégie marketing digital", "categorie": "methode", "icone": "📊", "description": "Élaboration d'une stratégie marketing complète."},
            {"nom": "Community management", "categorie": "methode", "icone": "💬", "description": "Animation de communauté, planification de contenu et gestion de crise."},
            {"nom": "Social media growth", "categorie": "methode", "icone": "📈", "description": "Stratégies de croissance d'audience et contenu engageant."},
            {"nom": "Facebook Ads", "categorie": "outil", "icone": "📱", "description": "Création, ciblage et optimisation de campagnes Facebook/Instagram."},
            {"nom": "Google Ads (SEA)", "categorie": "outil", "icone": "🔍", "description": "Publicité Google avec sélection de mots-clés et optimisation."},
            {"nom": "E-commerce", "categorie": "outil", "icone": "🛒", "description": "Création de boutique en ligne, paiements et livraison."},
            {"nom": "Freelancing & Personal Branding", "categorie": "methode", "icone": "💼", "description": "Positionnement freelance et prospection internationale."},
            {"nom": "Excel appliqué à la logistique", "categorie": "outil", "icone": "📊", "description": "Suivi des stocks, seuils de réapprovisionnement et tableaux de bord Excel."},
            {"nom": "Gestion de stock professionnelle", "categorie": "methode", "icone": "📦", "description": "Classification ABC, rotation des stocks, anticipation des ruptures."},
            {"nom": "Logistique et flux de marchandises", "categorie": "methode", "icone": "🚚", "description": "Transport, entreposage et distribution."},
            {"nom": "Supply chain management", "categorie": "methode", "icone": "🔗", "description": "Pilotage stratégique de la chaîne d'approvisionnement."},
            {"nom": "Odoo ERP", "categorie": "outil", "icone": "🔄", "description": "Utilisation d'Odoo pour la gestion intégrée stocks, achats et ventes."},
            {"nom": "SAP S/4HANA", "categorie": "outil", "icone": "💼", "description": "ERP de référence des grandes entreprises."},
            {"nom": "Microsoft Dynamics 365", "categorie": "outil", "icone": "☁️", "description": "ERP Microsoft pour PME en croissance."},
            {"nom": "Power BI Logistique", "categorie": "outil", "icone": "📈", "description": "Visualisation de données logistiques pour l'aide à la décision."},
            {"nom": "Gestion des achats et approvisionnement", "categorie": "methode", "icone": "🤝", "description": "Sélection fournisseurs, négociation et planification."},
            {"nom": "Warehouse management", "categorie": "methode", "icone": "🏗️", "description": "Organisation et pilotage d'entrepôt professionnel."},
        ]

        competences_cache = {}
        for comp_data in COMPETENCES_DATA:
            comp = self.create_competence(**comp_data)
            competences_cache[comp.nom] = comp
        self.stdout.write(self.style.SUCCESS(f"   ✅ {len(competences_cache)} compétences prêtes."))

        # ---- ÉTAPE 2 : Examens finaux ----
        self.stdout.write("\n📌 ÉTAPE 2/3 : CRÉATION DES EXAMENS FINAUX")
        self.stdout.write("-" * 40)

        EXAMENS_DATA = {
            "Business Numérique": [
                {"formation_nom": "Marketing Digital Professionnel — Certificat Complet", "titre": "Examen Final — Marketing Digital Professionnel", "duree_minutes": 90, "seuil_reussite": 70, "competences_evaluees": "Stratégie marketing digital, sélection de canaux, analyse de performance.", "competences_noms": ["Stratégie marketing digital"]},
                {"formation_nom": "Community Manager Professionnel", "titre": "Examen Final — Community Manager Professionnel", "duree_minutes": 60, "seuil_reussite": 70, "competences_evaluees": "Planification de contenu, animation de communauté, gestion de crise.", "competences_noms": ["Community management"]},
                {"formation_nom": "Social Media Marketing : Croissance & Engagement", "titre": "Examen Final — Social Media Marketing", "duree_minutes": 60, "seuil_reussite": 70, "competences_evaluees": "Stratégie de croissance, contenu engageant, analyse d'indicateurs.", "competences_noms": ["Social media growth"]},
                {"formation_nom": "Publicité Facebook & Instagram Ads", "titre": "Examen Final — Publicité Facebook & Instagram Ads", "duree_minutes": 60, "seuil_reussite": 70, "competences_evaluees": "Publicité Facebook/Instagram, ciblage, optimisation.", "competences_noms": ["Facebook Ads"]},
                {"formation_nom": "Google Ads Professionnel (SEA)", "titre": "Examen Final — Google Ads Professionnel", "duree_minutes": 60, "seuil_reussite": 70, "competences_evaluees": "Google Ads, mots-clés, optimisation SEA.", "competences_noms": ["Google Ads (SEA)"]},
                {"formation_nom": "E-commerce Professionnel : Créer sa Boutique en Ligne", "titre": "Examen Final — E-commerce Professionnel", "duree_minutes": 90, "seuil_reussite": 70, "competences_evaluees": "Boutique en ligne, paiements, livraison.", "competences_noms": ["E-commerce"]},
                {"formation_nom": "Freelance & Personal Branding : Vivre de son Expertise en Ligne", "titre": "Examen Final — Freelance & Personal Branding", "duree_minutes": 60, "seuil_reussite": 70, "competences_evaluees": "Freelancing, personal branding, prospection.", "competences_noms": ["Freelancing & Personal Branding"]},
            ],
            "Logistique": [
                {"formation_nom": "Excel Professionnel pour la Gestion des Stocks", "titre": "Examen Final — Excel Gestion des Stocks", "duree_minutes": 60, "seuil_reussite": 70, "competences_evaluees": "Excel logistique, suivi de stock, tableaux de bord.", "competences_noms": ["Excel appliqué à la logistique"]},
                {"formation_nom": "Gestion de Stock Professionnelle : Excel, Méthodes Modernes & ERP", "titre": "Examen Final — Gestion de Stock Professionnelle", "duree_minutes": 60, "seuil_reussite": 70, "competences_evaluees": "Méthodes modernes, classification ABC, introduction ERP.", "competences_noms": ["Gestion de stock professionnelle"]},
                {"formation_nom": "Logistique Professionnelle", "titre": "Examen Final — Logistique Professionnelle", "duree_minutes": 60, "seuil_reussite": 70, "competences_evaluees": "Logistique, flux, transport, distribution.", "competences_noms": ["Logistique et flux de marchandises"]},
                {"formation_nom": "Supply Chain Management", "titre": "Examen Final — Supply Chain Management", "duree_minutes": 90, "seuil_reussite": 70, "competences_evaluees": "Stratégie supply chain, coordination, KPI.", "competences_noms": ["Supply chain management"]},
                {"formation_nom": "Odoo ERP", "titre": "Examen Final — Odoo ERP", "duree_minutes": 90, "seuil_reussite": 70, "competences_evaluees": "Configuration Odoo, flux achat-vente, reporting.", "competences_noms": ["Odoo ERP"]},
                {"formation_nom": "SAP S/4HANA", "titre": "Examen Final — SAP S/4HANA", "duree_minutes": 90, "seuil_reussite": 70, "competences_evaluees": "Navigation SAP, processus logistiques.", "competences_noms": ["SAP S/4HANA"]},
                {"formation_nom": "Microsoft Dynamics 365 Business Central", "titre": "Examen Final — Microsoft Dynamics 365", "duree_minutes": 90, "seuil_reussite": 70, "competences_evaluees": "Dynamics 365, gestion intégrée, reporting.", "competences_noms": ["Microsoft Dynamics 365"]},
                {"formation_nom": "Power BI Logistique", "titre": "Examen Final — Power BI Logistique", "duree_minutes": 60, "seuil_reussite": 70, "competences_evaluees": "Power BI, visualisation, indicateurs.", "competences_noms": ["Power BI Logistique"]},
                {"formation_nom": "Achats & Approvisionnement", "titre": "Examen Final — Achats & Approvisionnement", "duree_minutes": 60, "seuil_reussite": 70, "competences_evaluees": "Achats, négociation, planification.", "competences_noms": ["Gestion des achats et approvisionnement"]},
                {"formation_nom": "Warehouse Management", "titre": "Examen Final — Warehouse Management", "duree_minutes": 60, "seuil_reussite": 70, "competences_evaluees": "Entrepôt, réception, expédition, KPI.", "competences_noms": ["Warehouse management"]},
            ],
        }

        total_examens = 0
        for ecole_key, examens in EXAMENS_DATA.items():
            self.stdout.write(f"\n  🏫 École : {ecole_key}")
            for ex_data in examens:
                formation = self.get_formation(ex_data["formation_nom"], ecole_key)
                if not formation:
                    continue
                competences_liees = [competences_cache[nom] for nom in ex_data["competences_noms"] if nom in competences_cache]
                self.create_examen(formation, ex_data["titre"], ex_data["duree_minutes"], ex_data["seuil_reussite"], ex_data["competences_evaluees"], competences_liees)
                total_examens += 1
        self.stdout.write(self.style.SUCCESS(f"\n   ✅ {total_examens} examens finaux créés."))

        # ---- ÉTAPE 3 : Quiz ----
        self.stdout.write("\n📌 ÉTAPE 3/3 : CRÉATION DES QUIZ DE MODULE")
        self.stdout.write("-" * 40)

        QUIZ_DATA = {
            "Business Numérique": [
                {"formation_nom": "Marketing Digital Professionnel — Certificat Complet", "quizzes": [{"module_titre": "Stratégie marketing digital", "titre": "Quiz — Stratégie marketing digital", "description": "Stratégie et sélection des canaux.", "limite_minutes": 20}, {"module_titre": "Exécution et mesure", "titre": "Quiz — Exécution et mesure", "description": "Contenu, calendrier éditorial et performance.", "limite_minutes": 20}]},
                {"formation_nom": "Community Manager Professionnel", "quizzes": [{"module_titre": "Le métier de community manager", "titre": "Quiz — Community Manager", "description": "Planification, animation et gestion de crise.", "limite_minutes": 20}]},
                {"formation_nom": "Social Media Marketing : Croissance & Engagement", "quizzes": [{"module_titre": "Croissance et engagement", "titre": "Quiz — Croissance & Engagement", "description": "Stratégies de croissance et contenu engageant.", "limite_minutes": 20}]},
                {"formation_nom": "Publicité Facebook & Instagram Ads", "quizzes": [{"module_titre": "Créer et optimiser une campagne Ads", "titre": "Quiz — Facebook & Instagram Ads", "description": "Structure, ciblage et optimisation.", "limite_minutes": 20}]},
                {"formation_nom": "Google Ads Professionnel (SEA)", "quizzes": [{"module_titre": "Créer et optimiser une campagne Google Ads", "titre": "Quiz — Google Ads", "description": "Structure, mots-clés et optimisation.", "limite_minutes": 20}]},
                {"formation_nom": "E-commerce Professionnel : Créer sa Boutique en Ligne", "quizzes": [{"module_titre": "Construction de la boutique", "titre": "Quiz — Construction boutique", "description": "Produits et configuration des paiements.", "limite_minutes": 20}, {"module_titre": "Livraison et suivi", "titre": "Quiz — Livraison et suivi", "description": "Organisation de la livraison.", "limite_minutes": 20}]},
                {"formation_nom": "Freelance & Personal Branding : Vivre de son Expertise en Ligne", "quizzes": [{"module_titre": "Se lancer en freelance", "titre": "Quiz — Freelance & Personal Branding", "description": "Profil, marque personnelle et prospection.", "limite_minutes": 20}]},
            ],
            "Logistique": [
                {"formation_nom": "Excel Professionnel pour la Gestion des Stocks", "quizzes": [{"module_titre": "Suivi de stock dans Excel", "titre": "Quiz — Suivi de stock Excel", "description": "Structure et calcul du stock disponible.", "limite_minutes": 20}, {"module_titre": "Indicateurs et tableaux de bord", "titre": "Quiz — Indicateurs et tableaux de bord", "description": "Seuils de réapprovisionnement.", "limite_minutes": 20}]},
                {"formation_nom": "Gestion de Stock Professionnelle : Excel, Méthodes Modernes & ERP", "quizzes": [{"module_titre": "Méthodes modernes de gestion de stock", "titre": "Quiz — Méthodes modernes", "description": "Classification ABC et rotation des stocks.", "limite_minutes": 20}, {"module_titre": "Vers l'ERP", "titre": "Quiz — Introduction ERP", "description": "Limites d'Excel et avantages d'un ERP.", "limite_minutes": 20}]},
                {"formation_nom": "Logistique Professionnelle", "quizzes": [{"module_titre": "Chaîne logistique et flux", "titre": "Quiz — Chaîne logistique", "description": "Cartographie et flux de marchandises.", "limite_minutes": 20}, {"module_titre": "Transport, entreposage et distribution", "titre": "Quiz — Transport et distribution", "description": "Organisation du transport.", "limite_minutes": 20}]},
                {"formation_nom": "Supply Chain Management", "quizzes": [{"module_titre": "Piloter une supply chain", "titre": "Quiz — Supply Chain", "description": "Stratégie, coordination et KPI.", "limite_minutes": 20}]},
                {"formation_nom": "Odoo ERP", "quizzes": [{"module_titre": "Configuration Odoo", "titre": "Quiz — Configuration Odoo", "description": "Modules stock, achats et ventes.", "limite_minutes": 20}, {"module_titre": "Exploitation et reporting", "titre": "Quiz — Exploitation Odoo", "description": "Flux achat-vente et rapports.", "limite_minutes": 20}]},
                {"formation_nom": "SAP S/4HANA", "quizzes": [{"module_titre": "Environnement SAP", "titre": "Quiz — Environnement SAP", "description": "Navigation et structure organisationnelle.", "limite_minutes": 20}, {"module_titre": "Processus logistiques SAP", "titre": "Quiz — Processus SAP", "description": "Gestion de stock et achats dans SAP.", "limite_minutes": 20}]},
                {"formation_nom": "Microsoft Dynamics 365 Business Central", "quizzes": [{"module_titre": "Configuration Dynamics 365", "titre": "Quiz — Configuration Dynamics", "description": "Modules stock et achats.", "limite_minutes": 20}, {"module_titre": "Exploitation et reporting", "titre": "Quiz — Exploitation Dynamics", "description": "Flux intégré et rapports.", "limite_minutes": 20}]},
                {"formation_nom": "Power BI Logistique", "quizzes": [{"module_titre": "Power BI appliqué à la logistique", "titre": "Quiz — Power BI Logistique", "description": "Connexion données, tableaux de bord.", "limite_minutes": 20}]},
                {"formation_nom": "Achats & Approvisionnement", "quizzes": [{"module_titre": "Achats et approvisionnement professionnels", "titre": "Quiz — Achats", "description": "Sélection fournisseurs, négociation.", "limite_minutes": 20}]},
                {"formation_nom": "Warehouse Management", "quizzes": [{"module_titre": "Piloter un entrepôt professionnel", "titre": "Quiz — Warehouse", "description": "Organisation, processus et KPI.", "limite_minutes": 20}]},
            ],
        }

        total_quiz = 0
        for ecole_key, formations_quiz in QUIZ_DATA.items():
            self.stdout.write(f"\n  🏫 École : {ecole_key}")
            for fq_data in formations_quiz:
                formation = self.get_formation(fq_data["formation_nom"], ecole_key)
                if not formation:
                    continue
                for q_data in fq_data["quizzes"]:
                    self.create_quiz(formation, q_data["module_titre"], q_data["titre"], q_data["description"], q_data["limite_minutes"])
                    total_quiz += 1
        self.stdout.write(self.style.SUCCESS(f"\n   ✅ {total_quiz} quiz de module créés."))

        # ---- RÉCAPITULATIF ----
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("📊 RÉCAPITULATIF FINAL")
        self.stdout.write("=" * 60)
        self.stdout.write(f"  🧠 Compétences : {Competence.objects.count()}")
        self.stdout.write(f"  📝 Examens finaux : {Examen.objects.count()}")
        self.stdout.write(f"  🧩 Quiz de module : {Quiz.objects.count()}")
        self.stdout.write(f"  📦 Modules : {Module.objects.count()}")
        self.stdout.write("=" * 60)
        self.stdout.write(self.style.SUCCESS("✅ Script terminé avec succès."))