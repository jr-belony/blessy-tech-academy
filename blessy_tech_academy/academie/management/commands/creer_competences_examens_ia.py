"""
Commande Django : crée les compétences, examens finaux et quiz de module
pour les formations de l'École Intelligence Artificielle.
Usage : python manage.py creer_competences_examens_ia
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
    help = "Crée les compétences, examens et quiz pour l'École Intelligence Artificielle"

    def get_formation(self, nom):
        try:
            return Formation.objects.get(nom__iexact=nom, ecole__nom__icontains="Intelligence Artificielle")
        except Formation.DoesNotExist:
            self.stdout.write(self.style.WARNING(f"  ⚠️ Formation introuvable : '{nom}'"))
            return None
        except Formation.MultipleObjectsReturned:
            return Formation.objects.filter(nom__iexact=nom, ecole__nom__icontains="Intelligence Artificielle").first()

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
        self.stdout.write("🚀 CRÉATION COMPÉTENCES, EXAMENS & QUIZ — INTELLIGENCE ARTIFICIELLE")
        self.stdout.write("=" * 60)

        # ---- ÉTAPE 1 : Compétences ----
        self.stdout.write("\n📌 ÉTAPE 1/3 : COMPÉTENCES")
        self.stdout.write("-" * 40)

        COMPETENCES_DATA = [
            {"nom": "Usage professionnel de l'IA générative", "categorie": "methode", "icone": "🤖", "description": "Utilisation quotidienne des outils d'IA générative pour la productivité."},
            {"nom": "Prompt engineering", "categorie": "methode", "icone": "✍️", "description": "Conception méthodique de prompts fiables et reproductibles."},
            {"nom": "Automatisation no-code", "categorie": "outil", "icone": "⚡", "description": "Connexion d'outils et automatisation de processus avec Zapier, Make et n8n."},
            {"nom": "Intégration IA dans les flux automatisés", "categorie": "methode", "icone": "🔗", "description": "Ajout d'étapes IA dans des flux d'automatisation no-code."},
            {"nom": "Stratégie IA en entreprise", "categorie": "methode", "icone": "🏢", "description": "Identification de cas d'usage IA, évaluation de ROI et conduite du changement."},
            {"nom": "Développement d'applications IA avec Python", "categorie": "outil", "icone": "🧠", "description": "Intégration d'API de LLM dans des applications Python : chatbots et outils d'analyse."},
            {"nom": "Architecture d'agents IA autonomes", "categorie": "methode", "icone": "🦾", "description": "Conception de systèmes IA multi-outils et multi-étapes autonomes."},
            {"nom": "Orchestration d'outils IA", "categorie": "methode", "icone": "🎯", "description": "Chaînage de plusieurs outils et décisions dans un agent autonome."},
            {"nom": "Évaluation de systèmes IA autonomes", "categorie": "methode", "icone": "📋", "description": "Mesure de la fiabilité, limites et risques des agents IA."},
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
            {"formation_nom": "IA pour la Productivité Personnelle & Professionnelle", "titre": "Examen Final — IA Productivité", "duree_minutes": 45, "seuil_reussite": 70, "competences_evaluees": "Usage IA générative, productivité augmentée.", "competences_noms": ["Usage professionnel de l'IA générative"]},
            {"formation_nom": "Prompt Engineering Professionnel : Maîtriser les IA Génératives", "titre": "Examen Final — Prompt Engineering", "duree_minutes": 60, "seuil_reussite": 70, "competences_evaluees": "Conception de prompts, reproductibilité, adaptation multi-modèles.", "competences_noms": ["Prompt engineering"]},
            {"formation_nom": "Automatisation Intelligente : IA + No-Code (Zapier, Make, n8n)", "titre": "Examen Final — Automatisation Intelligente", "duree_minutes": 60, "seuil_reussite": 70, "competences_evaluees": "Automatisation no-code, intégration IA.", "competences_noms": ["Automatisation no-code", "Intégration IA dans les flux automatisés"]},
            {"formation_nom": "Intelligence Artificielle pour les Entreprises : Stratégie & Cas d'Usage", "titre": "Examen Final — Stratégie IA Entreprise", "duree_minutes": 60, "seuil_reussite": 70, "competences_evaluees": "Cas d'usage IA, ROI, conduite du changement.", "competences_noms": ["Stratégie IA en entreprise"]},
            {"formation_nom": "Développeur d'Applications IA (Python + LLM)", "titre": "Examen Final — Développeur Applications IA", "duree_minutes": 90, "seuil_reussite": 70, "competences_evaluees": "API LLM, chatbot, outil d'analyse, déploiement.", "competences_noms": ["Développement d'applications IA avec Python"]},
            {"formation_nom": "IA Générative Avancée : LLM & Agents Autonomes", "titre": "Examen Final — Agents IA Autonomes", "duree_minutes": 90, "seuil_reussite": 70, "competences_evaluees": "Architecture d'agents, orchestration, fiabilité.", "competences_noms": ["Architecture d'agents IA autonomes", "Orchestration d'outils IA", "Évaluation de systèmes IA autonomes"]},
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
            {"formation_nom": "IA pour la Productivité Personnelle & Professionnelle", "quizzes": [
                {"module_titre": "Bases de l'IA générative appliquée", "titre": "Quiz — Bases IA générative", "description": "Panorama des outils et rédaction assistée.", "limite_minutes": 20},
                {"module_titre": "Productivité et priorisation", "titre": "Quiz — Productivité IA", "description": "Synthèse de documents et priorisation des tâches.", "limite_minutes": 20},
            ]},
            {"formation_nom": "Prompt Engineering Professionnel : Maîtriser les IA Génératives", "quizzes": [
                {"module_titre": "Méthodologie du prompt professionnel", "titre": "Quiz — Méthodologie du prompt", "description": "Structure, contexte, rôle, format et contraintes.", "limite_minutes": 20},
                {"module_titre": "Prompts appliqués et bibliothèque personnelle", "titre": "Quiz — Bibliothèque de prompts", "description": "Adaptation multi-modèles et prompts réutilisables.", "limite_minutes": 20},
            ]},
            {"formation_nom": "Automatisation Intelligente : IA + No-Code (Zapier, Make, n8n)", "quizzes": [
                {"module_titre": "Bases de l'automatisation no-code", "titre": "Quiz — Bases automatisation", "description": "Déclencheurs, actions et connexion d'outils.", "limite_minutes": 20},
                {"module_titre": "Automatisation intelligente avec l'IA", "titre": "Quiz — Automatisation IA", "description": "Intégration IA et diagnostic de flux.", "limite_minutes": 20},
            ]},
            {"formation_nom": "Intelligence Artificielle pour les Entreprises : Stratégie & Cas d'Usage", "quizzes": [
                {"module_titre": "Stratégie IA en entreprise", "titre": "Quiz — Stratégie IA", "description": "Cas d'usage, ROI et conduite du changement.", "limite_minutes": 20},
            ]},
            {"formation_nom": "Développeur d'Applications IA (Python + LLM)", "quizzes": [
                {"module_titre": "Intégration de LLM en Python", "titre": "Quiz — API LLM Python", "description": "Appels d'API, gestion des réponses et erreurs.", "limite_minutes": 20},
                {"module_titre": "Construction d'applications IA", "titre": "Quiz — Applications IA", "description": "Chatbot fonctionnel et outil d'analyse.", "limite_minutes": 20},
            ]},
            {"formation_nom": "IA Générative Avancée : LLM & Agents Autonomes", "quizzes": [
                {"module_titre": "Architecture des agents autonomes", "titre": "Quiz — Architecture agents", "description": "Principes de conception et orchestration.", "limite_minutes": 20},
                {"module_titre": "Fiabilité et limites des agents IA", "titre": "Quiz — Fiabilité agents IA", "description": "Évaluation, risques et garde-fous.", "limite_minutes": 20},
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