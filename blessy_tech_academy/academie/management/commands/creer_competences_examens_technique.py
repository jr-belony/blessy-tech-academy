"""
Commande Django : crée les compétences, examens finaux et quiz de module
pour les formations de l'École Technique.
Usage : python manage.py creer_competences_examens_technique
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
    help = "Crée les compétences, examens et quiz pour l'École Technique"

    def get_formation(self, nom):
        try:
            return Formation.objects.get(nom__iexact=nom, ecole__nom__icontains="Technique")
        except Formation.DoesNotExist:
            self.stdout.write(self.style.WARNING(f"  ⚠️ Formation introuvable : '{nom}'"))
            return None
        except Formation.MultipleObjectsReturned:
            return Formation.objects.filter(nom__iexact=nom, ecole__nom__icontains="Technique").first()

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
        self.stdout.write("🚀 CRÉATION COMPÉTENCES, EXAMENS & QUIZ — ÉCOLE TECHNIQUE")
        self.stdout.write("=" * 60)

        # ---- ÉTAPE 1 : Compétences ----
        self.stdout.write("\n📌 ÉTAPE 1/3 : COMPÉTENCES")
        self.stdout.write("-" * 40)

        COMPETENCES_DATA = [
            {"nom": "Diagnostic matériel PC", "categorie": "methode", "icone": "🔍", "description": "Méthodologie de diagnostic des pannes matérielles sur ordinateurs de bureau et portables."},
            {"nom": "Installation de systèmes d'exploitation", "categorie": "outil", "icone": "💻", "description": "Installation et configuration de Windows sur différents types de matériel."},
            {"nom": "Maintenance préventive", "categorie": "methode", "icone": "🔧", "description": "Entretien préventif du matériel informatique et bonnes pratiques."},
            {"nom": "Gestion des pilotes et mises à jour", "categorie": "outil", "icone": "⬆️", "description": "Résolution de problèmes de pilotes et gestion des mises à jour Windows."},
            {"nom": "Réseaux TCP/IP", "categorie": "methode", "icone": "🌐", "description": "Adressage IP, sous-réseaux, configuration et diagnostic de réseaux locaux."},
            {"nom": "Administration Windows Server", "categorie": "outil", "icone": "🖥️", "description": "Installation, configuration et gestion de Windows Server : comptes, permissions et partages."},
            {"nom": "Virtualisation (VMware/Hyper-V)", "categorie": "outil", "icone": "☁️", "description": "Création et gestion de machines virtuelles avec VMware et Hyper-V."},
            {"nom": "Cloud computing", "categorie": "methode", "icone": "☁️", "description": "Modèles de service cloud (IaaS, PaaS, SaaS) et cas d'usage en entreprise."},
            {"nom": "Gestion de tickets helpdesk", "categorie": "methode", "icone": "🎧", "description": "Traitement de tickets, priorisation et communication avec utilisateurs."},
            {"nom": "Documentation technique", "categorie": "methode", "icone": "📋", "description": "Rédaction de fiches d'intervention et documentation de dépannage."},
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
            {"formation_nom": "Technicien(ne) en Maintenance Informatique — Certificat Professionnel", "titre": "Examen Final — Maintenance Informatique", "duree_minutes": 120, "seuil_reussite": 70, "competences_evaluees": "Diagnostic matériel, installation OS, maintenance préventive, documentation.", "competences_noms": ["Diagnostic matériel PC", "Installation de systèmes d'exploitation", "Maintenance préventive", "Documentation technique"]},
            {"formation_nom": "Installation & Configuration Windows / Logiciels", "titre": "Examen Final — Installation Windows", "duree_minutes": 60, "seuil_reussite": 70, "competences_evaluees": "Installation Windows, pilotes, mises à jour, logiciels.", "competences_noms": ["Installation de systèmes d'exploitation", "Gestion des pilotes et mises à jour"]},
            {"formation_nom": "Diagnostic & Dépannage PC : Techniques Professionnelles", "titre": "Examen Final — Diagnostic & Dépannage PC", "duree_minutes": 60, "seuil_reussite": 70, "competences_evaluees": "Méthodologie de diagnostic, résolution de pannes.", "competences_noms": ["Diagnostic matériel PC", "Documentation technique"]},
            {"formation_nom": "Réseaux Informatiques : Fondamentaux & Administration (TCP/IP)", "titre": "Examen Final — Réseaux TCP/IP", "duree_minutes": 90, "seuil_reussite": 70, "competences_evaluees": "Adressage IP, sous-réseaux, configuration et diagnostic réseau.", "competences_noms": ["Réseaux TCP/IP"]},
            {"formation_nom": "Administration Systèmes Windows Server", "titre": "Examen Final — Windows Server", "duree_minutes": 90, "seuil_reussite": 70, "competences_evaluees": "Installation, comptes, permissions, partages sécurisés.", "competences_noms": ["Administration Windows Server"]},
            {"formation_nom": "Virtualisation & Cloud Computing (VMware / Hyper-V)", "titre": "Examen Final — Virtualisation & Cloud", "duree_minutes": 60, "seuil_reussite": 70, "competences_evaluees": "Machines virtuelles, modèles cloud, cas d'usage.", "competences_noms": ["Virtualisation (VMware/Hyper-V)", "Cloud computing"]},
            {"formation_nom": "Support Technique IT / Helpdesk Professionnel", "titre": "Examen Final — Support Technique Helpdesk", "duree_minutes": 45, "seuil_reussite": 70, "competences_evaluees": "Gestion de tickets, communication, résolution d'incidents.", "competences_noms": ["Gestion de tickets helpdesk", "Documentation technique"]},
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
            {"formation_nom": "Technicien(ne) en Maintenance Informatique — Certificat Professionnel", "quizzes": [
                {"module_titre": "Matériel et assemblage", "titre": "Quiz — Matériel et assemblage", "description": "Composants, compatibilité et assemblage.", "limite_minutes": 20},
                {"module_titre": "Systèmes et logiciels", "titre": "Quiz — Systèmes et logiciels", "description": "Installation OS et logiciels courants.", "limite_minutes": 20},
                {"module_titre": "Diagnostic et maintenance", "titre": "Quiz — Diagnostic et maintenance", "description": "Méthodologie de diagnostic et maintenance préventive.", "limite_minutes": 20},
            ]},
            {"formation_nom": "Installation & Configuration Windows / Logiciels", "quizzes": [
                {"module_titre": "Déployer un poste Windows", "titre": "Quiz — Déploiement Windows", "description": "Installation, pilotes, mises à jour et logiciels.", "limite_minutes": 20},
            ]},
            {"formation_nom": "Diagnostic & Dépannage PC : Techniques Professionnelles", "quizzes": [
                {"module_titre": "Diagnostiquer et dépanner", "titre": "Quiz — Diagnostic et dépannage", "description": "Méthodologie, pannes matérielles et logicielles.", "limite_minutes": 20},
            ]},
            {"formation_nom": "Réseaux Informatiques : Fondamentaux & Administration (TCP/IP)", "quizzes": [
                {"module_titre": "Fondamentaux TCP/IP", "titre": "Quiz — Fondamentaux TCP/IP", "description": "Modèle TCP/IP, adressage et sous-réseaux.", "limite_minutes": 20},
                {"module_titre": "Configuration et diagnostic réseau", "titre": "Quiz — Configuration réseau", "description": "Réseau local et diagnostic de connectivité.", "limite_minutes": 20},
            ]},
            {"formation_nom": "Administration Systèmes Windows Server", "quizzes": [
                {"module_titre": "Installation et configuration", "titre": "Quiz — Installation Windows Server", "description": "Installation et configuration initiale.", "limite_minutes": 20},
                {"module_titre": "Comptes, permissions et partages", "titre": "Quiz — Comptes et permissions", "description": "Utilisateurs, groupes et partages sécurisés.", "limite_minutes": 20},
            ]},
            {"formation_nom": "Virtualisation & Cloud Computing (VMware / Hyper-V)", "quizzes": [
                {"module_titre": "Virtualisation", "titre": "Quiz — Virtualisation", "description": "Création et gestion de machines virtuelles.", "limite_minutes": 20},
                {"module_titre": "Cloud computing", "titre": "Quiz — Cloud computing", "description": "IaaS, PaaS, SaaS et cas d'usage.", "limite_minutes": 20},
            ]},
            {"formation_nom": "Support Technique IT / Helpdesk Professionnel", "quizzes": [
                {"module_titre": "Le métier du support technique", "titre": "Quiz — Support technique", "description": "Tickets, priorisation et communication.", "limite_minutes": 20},
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