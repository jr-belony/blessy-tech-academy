"""
Commande Django : crée les compétences, examens finaux et quiz de module
pour les formations de l'École de Programmation & Développement.
Usage : python manage.py creer_competences_examens_programmation
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
    help = "Crée les compétences, examens et quiz pour l'École de Programmation & Développement"

    def get_formation(self, nom):
        try:
            return Formation.objects.get(nom__iexact=nom, ecole__nom__icontains="Programmation")
        except Formation.DoesNotExist:
            self.stdout.write(self.style.WARNING(f"  ⚠️ Formation introuvable : '{nom}'"))
            return None
        except Formation.MultipleObjectsReturned:
            return Formation.objects.filter(nom__iexact=nom, ecole__nom__icontains="Programmation").first()

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
                "xp_recompense": 100, "certificat_automatique": True,
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
        self.stdout.write("🚀 CRÉATION COMPÉTENCES, EXAMENS & QUIZ — PROGRAMMATION")
        self.stdout.write("=" * 60)

        # ---- ÉTAPE 1 : Compétences ----
        self.stdout.write("\n📌 ÉTAPE 1/3 : COMPÉTENCES")
        self.stdout.write("-" * 40)

        COMPETENCES_DATA = [
            {"nom": "HTML/CSS professionnel", "categorie": "outil", "icone": "🎨", "description": "Structuration sémantique HTML et mise en page responsive avec CSS."},
            {"nom": "JavaScript appliqué", "categorie": "outil", "icone": "📜", "description": "Manipulation du DOM, événements et logique applicative en JavaScript."},
            {"nom": "Développement React", "categorie": "outil", "icone": "⚛️", "description": "Construction de composants React, gestion d'état et déploiement."},
            {"nom": "Développement back-end Django", "categorie": "outil", "icone": "⚙️", "description": "Architecture Django, modélisation de bases de données et logique serveur."},
            {"nom": "Développement full stack Python/React", "categorie": "methode", "icone": "🚀", "description": "Architecture complète d'application web, connexion back-end/front-end et déploiement."},
            {"nom": "Programmation Python avancée", "categorie": "outil", "icone": "🐍", "description": "Structures de données avancées, POO et structuration de projets Python."},
            {"nom": "JavaScript moderne (ES6+)", "categorie": "outil", "icone": "📜", "description": "Syntaxe ES6+, promesses, programmation asynchrone et modules."},
            {"nom": "Développement mobile Flutter", "categorie": "outil", "icone": "📱", "description": "Interfaces Flutter, gestion d'état et publication sur les stores iOS/Android."},
            {"nom": "Conception d'API REST", "categorie": "methode", "icone": "🔌", "description": "Routes REST, sérialiseurs, authentification et documentation d'API."},
            {"nom": "Sécurité des API", "categorie": "methode", "icone": "🔒", "description": "Authentification, permissions et bonnes pratiques de sécurisation d'API."},
            {"nom": "Contrôle de version Git/GitHub", "categorie": "outil", "icone": "🔀", "description": "Gestion de l'historique, branches, pull requests et résolution de conflits."},
            {"nom": "Déploiement en production", "categorie": "methode", "icone": "☁️", "description": "Mise en ligne d'applications web et mobiles sur des serveurs ou stores."},
        ]

        competences_cache = {}
        for comp_data in COMPETENCES_DATA:
            comp = self.create_competence(**comp_data)
            competences_cache[comp.nom] = comp
        self.stdout.write(self.style.SUCCESS(f"   ✅ {len(competences_cache)} compétences prêtes."))

        # ---- ÉTAPE 2 : Examens finaux ----
        self.stdout.write("\n📌 ÉTAPE 2/3 : EXAMENS FINAUX")
        self.stdout.write("-" * 40)

        EXAMENS_DATA = [
            {"formation_nom": "Développeur Front-End (HTML, CSS, JavaScript, React)", "titre": "Examen Final — Développeur Front-End", "duree_minutes": 120, "seuil_reussite": 70, "competences_evaluees": "HTML/CSS, JavaScript, React, déploiement front-end.", "competences_noms": ["HTML/CSS professionnel", "JavaScript appliqué", "Développement React"]},
            {"formation_nom": "Développeur Back-End avec Django", "titre": "Examen Final — Développeur Back-End Django", "duree_minutes": 90, "seuil_reussite": 70, "competences_evaluees": "Architecture Django, bases de données, API.", "competences_noms": ["Développement back-end Django", "Conception d'API REST"]},
            {"formation_nom": "Développeur Full Stack Python (Django + React)", "titre": "Examen Final — Développeur Full Stack", "duree_minutes": 120, "seuil_reussite": 70, "competences_evaluees": "Architecture full stack, connexion back-end/front-end, déploiement.", "competences_noms": ["Développement full stack Python/React", "Déploiement en production"]},
            {"formation_nom": "Python Professionnel : de Zéro à Développeur", "titre": "Examen Final — Python Professionnel", "duree_minutes": 90, "seuil_reussite": 70, "competences_evaluees": "Structures de données, POO, projet complet.", "competences_noms": ["Programmation Python avancée"]},
            {"formation_nom": "JavaScript Moderne (ES6+)", "titre": "Examen Final — JavaScript Moderne", "duree_minutes": 60, "seuil_reussite": 70, "competences_evaluees": "ES6+, promesses, modules.", "competences_noms": ["JavaScript moderne (ES6+)"]},
            {"formation_nom": "Développeur Mobile Flutter (iOS & Android)", "titre": "Examen Final — Développeur Mobile Flutter", "duree_minutes": 90, "seuil_reussite": 70, "competences_evaluees": "Interfaces Flutter, logique applicative, publication.", "competences_noms": ["Développement mobile Flutter"]},
            {"formation_nom": "Développeur d'API REST avec Django REST Framework", "titre": "Examen Final — Développeur API REST", "duree_minutes": 60, "seuil_reussite": 70, "competences_evaluees": "Routes REST, sérialiseurs, authentification, documentation.", "competences_noms": ["Conception d'API REST", "Sécurité des API"]},
            {"formation_nom": "Git & GitHub Professionnel : Contrôle de Version", "titre": "Examen Final — Git & GitHub Professionnel", "duree_minutes": 45, "seuil_reussite": 70, "competences_evaluees": "Commandes Git, branches, pull requests, conflits.", "competences_noms": ["Contrôle de version Git/GitHub"]},
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

        # ---- ÉTAPE 3 : Quiz ----
        self.stdout.write("\n📌 ÉTAPE 3/3 : QUIZ DE MODULE")
        self.stdout.write("-" * 40)

        QUIZ_DATA = [
            {"formation_nom": "Développeur Front-End (HTML, CSS, JavaScript, React)", "quizzes": [
                {"module_titre": "HTML & CSS professionnel", "titre": "Quiz — HTML & CSS", "description": "Structure sémantique et mise en page responsive.", "limite_minutes": 20},
                {"module_titre": "JavaScript appliqué", "titre": "Quiz — JavaScript appliqué", "description": "DOM, événements et logique applicative.", "limite_minutes": 20},
                {"module_titre": "Développement avec React", "titre": "Quiz — React", "description": "Composants, props, état et déploiement.", "limite_minutes": 20},
            ]},
            {"formation_nom": "Développeur Back-End avec Django", "quizzes": [
                {"module_titre": "Structure Django", "titre": "Quiz — Structure Django", "description": "Architecture projet et modélisation de base de données.", "limite_minutes": 20},
                {"module_titre": "Logique applicative et API", "titre": "Quiz — Logique et API Django", "description": "Vues, routes et API connectable au front-end.", "limite_minutes": 20},
            ]},
            {"formation_nom": "Développeur Full Stack Python (Django + React)", "quizzes": [
                {"module_titre": "Architecture full stack", "titre": "Quiz — Architecture full stack", "description": "Conception et connexion back-end/front-end.", "limite_minutes": 20},
                {"module_titre": "Projet capstone", "titre": "Quiz — Projet capstone", "description": "Construction, déploiement et documentation.", "limite_minutes": 20},
            ]},
            {"formation_nom": "Python Professionnel : de Zéro à Développeur", "quizzes": [
                {"module_titre": "Python approfondi", "titre": "Quiz — Python approfondi", "description": "Structures de données avancées et bonnes pratiques.", "limite_minutes": 20},
                {"module_titre": "Programmation orientée objet", "titre": "Quiz — POO Python", "description": "Classes, objets, héritage et projet appliqué.", "limite_minutes": 20},
            ]},
            {"formation_nom": "JavaScript Moderne (ES6+)", "quizzes": [
                {"module_titre": "JavaScript moderne", "titre": "Quiz — JavaScript ES6+", "description": "Syntaxe, promesses et modules.", "limite_minutes": 20},
            ]},
            {"formation_nom": "Développeur Mobile Flutter (iOS & Android)", "quizzes": [
                {"module_titre": "Interfaces Flutter", "titre": "Quiz — Interfaces Flutter", "description": "Widgets et mise en page.", "limite_minutes": 20},
                {"module_titre": "Logique applicative et publication", "titre": "Quiz — Logique et publication Flutter", "description": "Gestion d'état et publication sur les stores.", "limite_minutes": 20},
            ]},
            {"formation_nom": "Développeur d'API REST avec Django REST Framework", "quizzes": [
                {"module_titre": "Concevoir et sécuriser une API", "titre": "Quiz — API REST", "description": "Routes, sérialiseurs, authentification et documentation.", "limite_minutes": 20},
            ]},
            {"formation_nom": "Git & GitHub Professionnel : Contrôle de Version", "quizzes": [
                {"module_titre": "Git & GitHub en pratique", "titre": "Quiz — Git & GitHub", "description": "Commandes Git, branches, pull requests et conflits.", "limite_minutes": 15},
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