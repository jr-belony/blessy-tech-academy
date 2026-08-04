"""
Commande Django : crée les compétences, examens et quiz pour les 6 formations
de l'École des Compétences Fondamentales (3 gratuites + 3 payantes).
Usage : python manage.py creer_competences_examens_fondamentales
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
    help = "Crée les compétences, examens et quiz pour l'École des Compétences Fondamentales"

    def get_formation(self, nom):
        try:
            return Formation.objects.get(nom__iexact=nom, ecole__nom__icontains="Fondamentales")
        except Formation.DoesNotExist:
            self.stdout.write(self.style.WARNING(f"  ⚠️ Formation introuvable : '{nom}'"))
            return None
        except Formation.MultipleObjectsReturned:
            return Formation.objects.filter(nom__iexact=nom, ecole__nom__icontains="Fondamentales").first()

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
            formation=formation, titre=titre,
            defaults={
                "duree_minutes": duree_minutes, "seuil_reussite": seuil_reussite,
                "tentatives_max": 2, "competences_evaluees": competences_evaluees,
                "type_evaluation": "EXAMEN_FINAL", "actif": True,
                "prerequis": "Avoir suivi tous les modules de la formation.",
                "conditions_utilisation": "Examen individuel sans documentation externe.",
                "xp_recompense": 50, "certificat_automatique": True,
                "date_disponibilite": DATE_DISPONIBILITE, "date_expiration": DATE_EXPIRATION,
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
            formation=formation, titre__iexact=module_titre,
            defaults={"titre": module_titre, "description": f"Module : {module_titre}", "ordre": 1}
        )
        quiz, created = Quiz.objects.get_or_create(
            formation=formation, module=module, titre=quiz_titre,
            defaults={
                "description": description, "actif": True,
                "limite_temps_minutes": limite_minutes, "tentatives_max": 3,
                "melanger_questions": True, "melanger_reponses": True,
                "type_evaluation": "QUIZ_MODULE", "date_creation": DATE_DISPONIBILITE,
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
        self.stdout.write("🚀 CRÉATION COMPÉTENCES, EXAMENS & QUIZ — COMPÉTENCES FONDAMENTALES")
        self.stdout.write("=" * 60)

        # ---- ÉTAPE 1 : Compétences ----
        self.stdout.write("\n📌 ÉTAPE 1/3 : COMPÉTENCES")
        self.stdout.write("-" * 40)

        COMPETENCES_DATA = [
            {"nom": "Culture numérique générale", "categorie": "methode", "icone": "🌐", "description": "Compréhension du paysage numérique, des métiers et des compétences attendues en 2026."},
            {"nom": "Navigation web et messagerie", "categorie": "outil", "icone": "📧", "description": "Utilisation d'un navigateur web, recherche Internet et messagerie électronique."},
            {"nom": "Culture de l'intelligence artificielle", "categorie": "methode", "icone": "🤖", "description": "Compréhension du fonctionnement général des IA génératives et de leurs usages."},
            {"nom": "Création web no-code", "categorie": "outil", "icone": "🌍", "description": "Création et publication d'une page web simple avec un outil no-code."},
            {"nom": "Culture marketing digital", "categorie": "methode", "icone": "📊", "description": "Connaissance des canaux du marketing digital et des bases d'une stratégie de contenu."},
            {"nom": "Initiation à la programmation Python", "categorie": "outil", "icone": "🐍", "description": "Écriture et exécution de premiers programmes simples en Python."},
            {"nom": "Traitement de texte professionnel", "categorie": "outil", "icone": "📝", "description": "Mise en forme et structuration de documents professionnels avec Word."},
            {"nom": "Tableur et calculs de base", "categorie": "outil", "icone": "📈", "description": "Construction de tableaux avec formules et fonctions de base dans Excel."},
            {"nom": "Collaboration en ligne", "categorie": "methode", "icone": "👥", "description": "Partage et co-édition de documents via Google Workspace."},
            {"nom": "Communication professionnelle numérique", "categorie": "methode", "icone": "💬", "description": "Utilisation des outils de visioconférence, rédaction d'e-mails professionnels et messagerie d'équipe."},
            {"nom": "Cybersécurité de base", "categorie": "methode", "icone": "🔒", "description": "Reconnaissance des menaces courantes, gestion sécurisée des mots de passe et protection des données."},
        ]

        competences_cache = {}
        for comp_data in COMPETENCES_DATA:
            comp = self.create_competence(**comp_data)
            competences_cache[comp.nom] = comp
        self.stdout.write(self.style.SUCCESS(f"   ✅ {len(competences_cache)} compétences prêtes."))

        # ---- ÉTAPE 2 : Examens (pour les 3 payantes uniquement) ----
        self.stdout.write("\n📌 ÉTAPE 2/3 : EXAMENS FINAUX (formations payantes)")
        self.stdout.write("-" * 40)

        EXAMENS_DATA = [
            {"formation_nom": "Bureautique Professionnelle & Productivité Numérique (Word, Excel, Google Workspace)", "titre": "Examen Final — Bureautique Professionnelle", "duree_minutes": 60, "seuil_reussite": 70, "competences_evaluees": "Word, Excel, Google Workspace, productivité IA.", "competences_noms": ["Traitement de texte professionnel", "Tableur et calculs de base", "Collaboration en ligne"]},
            {"formation_nom": "Communication & Collaboration Numérique en Entreprise", "titre": "Examen Final — Communication & Collaboration", "duree_minutes": 45, "seuil_reussite": 70, "competences_evaluees": "Visioconférence, e-mail professionnel, messagerie d'équipe.", "competences_noms": ["Communication professionnelle numérique"]},
            {"formation_nom": "Cybersécurité au Quotidien : Protéger ses Données", "titre": "Examen Final — Cybersécurité au Quotidien", "duree_minutes": 45, "seuil_reussite": 70, "competences_evaluees": "Hameçonnage, mots de passe, protection des données.", "competences_noms": ["Cybersécurité de base"]},
        ]

        total_examens = 0
        for ex_data in EXAMENS_DATA:
            formation = self.get_formation(ex_data["formation_nom"])
            if not formation:
                continue
            competences_liees = [competences_cache[nom] for nom in ex_data["competences_noms"] if nom in competences_cache]
            self.create_examen(formation, ex_data["titre"], ex_data["duree_minutes"], ex_data["seuil_reussite"], ex_data["competences_evaluees"], competences_liees)
            total_examens += 1
        self.stdout.write(self.style.SUCCESS(f"\n   ✅ {total_examens} examens finaux créés."))

        # ---- ÉTAPE 3 : Quiz (toutes formations) ----
        self.stdout.write("\n📌 ÉTAPE 3/3 : QUIZ DE MODULE")
        self.stdout.write("-" * 40)

        QUIZ_DATA = [
            {"formation_nom": "Réussir dans le Numérique 2026 : Orientation & Fondamentaux", "quizzes": [
                {"module_titre": "Comprendre et s'orienter", "titre": "Quiz — Orientation Numérique", "description": "Paysage numérique et auto-évaluation.", "limite_minutes": 15},
            ]},
            {"formation_nom": "Découverte de l'IA : Comprendre l'Intelligence Artificielle en 2026", "quizzes": [
                {"module_titre": "Comprendre l'IA", "titre": "Quiz — Comprendre l'IA", "description": "Fonctionnement, usages et risques de l'IA.", "limite_minutes": 15},
            ]},
            {"formation_nom": "Marketing Digital : les Fondamentaux 2026", "quizzes": [
                {"module_titre": "Les bases du marketing digital", "titre": "Quiz — Marketing Digital", "description": "Canaux, contenu organique vs payant.", "limite_minutes": 15},
            ]},
            {"formation_nom": "Bureautique Professionnelle & Productivité Numérique (Word, Excel, Google Workspace)", "quizzes": [
                {"module_titre": "Word professionnel", "titre": "Quiz — Word professionnel", "description": "Mise en forme et structuration de documents.", "limite_minutes": 20},
                {"module_titre": "Excel essentiel", "titre": "Quiz — Excel essentiel", "description": "Tableaux, formules et fonctions de base.", "limite_minutes": 20},
                {"module_titre": "Google Workspace & collaboration", "titre": "Quiz — Google Workspace", "description": "Docs, Sheets, Drive et Copilot.", "limite_minutes": 20},
            ]},
            {"formation_nom": "Communication & Collaboration Numérique en Entreprise", "quizzes": [
                {"module_titre": "Communiquer et collaborer", "titre": "Quiz — Communication numérique", "description": "Visioconférence, e-mails et messagerie.", "limite_minutes": 20},
            ]},
            {"formation_nom": "Cybersécurité au Quotidien : Protéger ses Données", "quizzes": [
                {"module_titre": "Se protéger au quotidien", "titre": "Quiz — Cybersécurité", "description": "Hameçonnage, mots de passe et protection des données.", "limite_minutes": 20},
            ]},
        ]

        total_quiz = 0
        for fq_data in QUIZ_DATA:
            formation = self.get_formation(fq_data["formation_nom"])
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