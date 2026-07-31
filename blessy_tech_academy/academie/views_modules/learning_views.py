# ================================================
# VIEWS_MODULES/LEARNING_VIEWS.PY — Vues pédagogiques
# (formations, modules, leçons, quiz, examens, orientation, simulateur)
# ================================================

import hashlib
import json
import random
from datetime import timedelta

import filetype
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import transaction
from django.db.models import Count, Q
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_POST
from django.contrib.admin.views.decorators import staff_member_required 

from ..models import (
    AccesFormationDebloque,
    Article,
    Certificat,
    ChoixExamen,
    Competence,
    CompetenceValidee,          # ← ajouté
    Ecole,
    Examen,
    Formation,
    Lecon,
    Module,
    Parcours,
    ProgressionLecon,
    Quiz,
    Question,
    QuestionExamen,
    Reaction,
    Reponse,
    ResultatQuiz,
    Sujet,
    SoumissionProjet,
    TentativeExamen,
    WorkflowFormation,
)
from ..services.ia_service import (
    attribuer_badges,
    generer_parcours_oriente,
    generer_programme_complet,
)
from ..xp_utils import ajouter_xp
from .. import notifications
from ..decorators import exiger_acces_formation
# ================================================
# Vues : Formations
# ================================================

def formations(request):
    """Page catalogue formations — paginée, avec cache invalidable par version."""
    version_cache = cache.get('formations_cache_version', 1)
    page_num = request.GET.get('page', 1)
    cache_key = f"formations_page_{page_num}_v{version_cache}"

    donnees_cache = cache.get(cache_key)
    if donnees_cache is not None:
        return render(request, 'academie/formations.html', donnees_cache)

    ecoles_list = Ecole.objects.prefetch_related('formations__modules').all()
    paginator = Paginator(ecoles_list, 6)  # 6 écoles par page
    try:
        ecoles = paginator.page(page_num)
    except PageNotAnInteger:
        ecoles = paginator.page(1)
    except EmptyPage:
        ecoles = paginator.page(paginator.num_pages)

    parcours_list = Parcours.objects.prefetch_related('formations').filter(actif=True)

    contexte = {
        'ecoles': ecoles,
        'page_obj': ecoles,             # pour les contrôles de pagination dans le template
        'parcours_list': parcours_list,
    }
    cache.set(cache_key, contexte, 600)  # 10 minutes
    return render(request, 'academie/formations.html', contexte)


def detail_formation(request, formation_id):
    formation = Formation.objects.prefetch_related("modules__lecons").get(
        id=formation_id, actif=True
    )
    pourcentage_progression = 0
    acces_autorise = formation.gratuit
    deja_inscrit = False

    if request.user.is_authenticated:
        pourcentage_progression = formation.progression_pour(request.user)
        acces_autorise = verifier_acces_formation(request.user, formation)
        deja_inscrit = acces_autorise

    prix_final, promo_active = _prix_avec_promotion(formation)
    nb_modules = formation.modules.count()
    nb_lecons = sum(m.lecons.count() for m in formation.modules.all())
    duree_totale_minutes = sum(
        lecon.duree_minutes for m in formation.modules.all() for lecon in m.lecons.all()
    )

    formations_similaires = (
        Formation.objects.filter(ecole=formation.ecole, actif=True).exclude(id=formation.id)[:3]
        if formation.ecole
        else []
    )

    if formation.debouches:
        formation.debouches_liste = [
            d.strip() for d in formation.debouches.replace(".", ",").split(",") if d.strip()
        ]
    else:
        formation.debouches_liste = []
    # Pré-calcul accessibilité séquentielle pour le template
    # Évite de recalculer est_accessible_pour() N fois dans le template Django
    if request.user.is_authenticated and formation.sequentiel_obligatoire:
        for module in formation.modules.all():
            for lecon in module.lecons.all():
                accessible, _ = lecon.est_accessible_pour(request.user)
                lecon.accessible = accessible
    else:
        for module in formation.modules.all():
            for lecon in module.lecons.all():
                lecon.accessible = True

    return render(
        request,
        "academie/detail_formation.html",
        {
            "formation": formation,
            "pourcentage_progression": pourcentage_progression,
            "acces_autorise": acces_autorise,
            "deja_inscrit": deja_inscrit,
            "prix_final": prix_final,
            "promo_active": promo_active,
            "nb_modules": nb_modules,
            "nb_lecons": nb_lecons,
            "duree_totale_heures": round(duree_totale_minutes / 60, 1),
            "formations_similaires": formations_similaires,
            "debouches_liste": formation.debouches_liste,
        },
    )

def detail_formation_slug(request, formation_slug):
    formation = Formation.objects.filter(slug=formation_slug, actif=True).first()
    if not formation:
        from django.http import Http404
        raise Http404("Formation introuvable")
    return detail_formation(request, formation.id)


# ================================================
# Vues : Leçons et progression
# ================================================

@login_required(login_url="/connexion/")
@exiger_acces_formation(lambda lecon_id: Lecon.objects.get(id=lecon_id).module.formation)
def lire_lecon(request, lecon_id):
    lecon = get_object_or_404(Lecon.objects.select_related("module__formation__ecole"), id=lecon_id)

    # --- Vérification séquentielle P0 #3 ---
    accessible, raison_blocage = lecon.est_accessible_pour(request.user)
    if not accessible:
        messages.warning(request, f"🔒 {raison_blocage}")
        return redirect('detail_formation', formation_id=lecon.module.formation.id)
    # ------------------------------------

    contenu_html = lecon.contenu if lecon.contenu else ""

    lecons_module = list(lecon.module.lecons.all())
    index_actuel = lecons_module.index(lecon)
    lecon_precedente = lecons_module[index_actuel - 1] if index_actuel > 0 else None
    lecon_suivante = (
        lecons_module[index_actuel + 1] if index_actuel < len(lecons_module) - 1 else None
    )
    progression = ProgressionLecon.objects.filter(utilisateur=request.user, lecon=lecon).first()
    lecon_terminee = progression.terminee if progression else False
    formation = lecon.module.formation
    pourcentage_formation = formation.progression_pour(request.user)
    tous_modules = formation.modules.prefetch_related("lecons").all()

    return render(
        request,
        "academie/lire_lecon.html",
        {
            "lecon": lecon,
            "contenu_html": contenu_html,
            "lecon_precedente": lecon_precedente,
            "lecon_suivante": lecon_suivante,
            "lecon_terminee": lecon_terminee,
            "pourcentage_formation": pourcentage_formation,
            "tous_modules": tous_modules,
            "formation": formation,
        },
    )

@login_required(login_url="/connexion/")
@exiger_acces_formation(lambda lecon_id: Lecon.objects.get(id=lecon_id).module.formation)
def marquer_lecon_terminee(request, lecon_id):
    if request.method == "POST":
        try:
            lecon = Lecon.objects.get(id=lecon_id)
            progression, cree = ProgressionLecon.objects.get_or_create(
                utilisateur=request.user,
                lecon=lecon,
            )

            progression.terminee = not progression.terminee
            progression.date_completion = timezone.now() if progression.terminee else None
            progression.save()

            # ===== ENREGISTREMENT DU STREAK =====
            from ..models import StreakEtudiant
            streak, _ = StreakEtudiant.objects.get_or_create(utilisateur=request.user)
            streak.enregistrer_activite_jour()

            if progression.terminee:
                ajouter_xp(request.user, "lecon_terminee")
                formation = lecon.module.formation
                pourcentage = formation.progression_pour(request.user)
                if pourcentage == 100:
                    notifications.notifier_formation_completee(request.user, formation.nom)
                    # --- Validation des compétences liées à la formation complétée ---
                    CompetenceValidee.valider_pour_formation_completee(request.user, formation)

            formation = lecon.module.formation
            nouveau_pourcentage = formation.progression_pour(request.user)

            return JsonResponse(
                {
                    "succes": True,
                    "terminee": progression.terminee,
                    "progression_formation": nouveau_pourcentage,
                }
            )

        except Lecon.DoesNotExist:
            return JsonResponse({"erreur": "Leçon introuvable"}, status=404)
        except Exception as e:
            return JsonResponse({"erreur": str(e)}, status=500)

    return JsonResponse({"erreur": "Méthode non autorisée"}, status=405)

# ================================================
# Vues Quiz (complément)
# ================================================

def liste_quiz(request, formation_id):
    formation = Formation.objects.get(id=formation_id)
    quiz_disponibles = Quiz.objects.filter(formation=formation, actif=True)
    return render(
        request,
        "academie/liste_quiz.html",
        {
            "formation": formation,
            "quiz_disponibles": quiz_disponibles,
        },
    )


@exiger_acces_formation(lambda quiz_id: Quiz.objects.get(id=quiz_id).formation)
@login_required(login_url="/connexion/")
def passer_quiz(request, quiz_id):
    quiz = Quiz.objects.prefetch_related("questions").get(id=quiz_id)

    if request.method == "POST":
        score = 0
        total = quiz.questions.count()

        for question in quiz.questions.all():
            reponse_utilisateur = request.POST.get(f"question_{question.id}")
            if reponse_utilisateur == question.bonne_reponse:
                score += 1

        ResultatQuiz.objects.create(
            utilisateur=request.user, quiz=quiz, score=score, total_questions=total
        )

        attribuer_badges(request.user)

        pourcentage = round((score / total) * 100) if total > 0 else 0
        if pourcentage >= 70:
            ajouter_xp(request.user, "quiz_reussi")
            notifications.creer_notification(
                request.user,
                "📝 Quiz réussi !",
                f'Tu as obtenu {score}/{total} au quiz "{quiz.titre}".',
                f"/formation/{quiz.formation.id}/quiz/",
            )

        return render(
            request,
            "academie/resultat_quiz.html",
            {
                "quiz": quiz,
                "score": score,
                "total": total,
                "pourcentage": pourcentage,
            },
        )

    return render(request, "academie/passer_quiz.html", {"quiz": quiz})



# ================================================
# Vues : Parcours et orientation
# ================================================

def parcours_professionnels(request):
    parcours_list = (
        Parcours.objects.prefetch_related("formations__modules")
        .filter(actif=True)
        .order_by("ordre")
    )
    return render(
        request,
        "academie/parcours.html",
        {
            "parcours_list": parcours_list,
        },
    )


def orientation_ia(request):
    profils = [
        ("lyceen_etudiant", "Lycéen / Étudiant", "🎓"),
        ("professionnel", "Professionnel", "💼"),
        ("entrepreneur", "Entrepreneur", "🚀"),
        ("numerique", "Déjà dans le numérique", "👨‍💻"),
    ]

    objectifs = [
        ("developpeur", "Devenir développeur", "💻"),
        ("design_creation", "Design & Création", "🎨"),
        ("marketing_business", "Marketing & Business", "📊"),
        ("maitriser_ia", "Maîtriser l'IA", "🤖"),
        ("technicien", "Technicien informatique", "🔧"),
    ]

    disponibilites = [
        ("1-2h", "1-2h par jour", "⏰"),
        ("3-4h", "3-4h par jour", "⏱"),
        ("temps_plein", "Temps plein", "🔥"),
    ]

    resultat = None
    erreur = None

    if request.method == "POST":
        profil = request.POST.get("profil", "")
        objectif = request.POST.get("objectif", "")
        disponibilite = request.POST.get("disponibilite", "")
        details = request.POST.get("details", "").strip()

        if profil and objectif and disponibilite:
            formations = Formation.objects.filter(actif=True).select_related("ecole")
            resultat = generer_parcours_oriente(
                profil, objectif, disponibilite, details, formations
            )

            if "erreur" in resultat:
                erreur = resultat["erreur"]
                resultat = None
        else:
            erreur = "Veuillez répondre aux 3 premières questions."

    return render(
        request,
        "academie/orientation.html",
        {
            "resultat": resultat,
            "erreur": erreur,
            "profils": profils,
            "objectifs": objectifs,
            "disponibilites": disponibilites,
            "post_data": request.POST if request.method == "POST" else None,
        },
    )


def simuler_carriere(request):
    METIERS_BTA = {
        "developpeur_web": {
            "titre": "Développeur Web Full Stack",
            "emoji": "💻",
            "description": "Tu crées des sites et applications web de A à Z — du design à la base de données.",
            "competences": ["HTML/CSS", "JavaScript", "Python", "Django", "PostgreSQL", "Git"],
            "technologies": ["VS Code", "GitHub", "Figma", "Postman", "Docker"],
            "metiers_accessibles": [
                "Développeur Front-end",
                "Développeur Back-end",
                "Full Stack Developer",
                "CTO Startup",
                "Freelance",
                "Consultant Web",
            ],
            "salaire_haiti": "800-2500",
            "salaire_international": "3000-8000",
            "duree_formation": "10 mois",
            "parcours_bta": "Développeur Web Python",
            "secteurs": ["Startups Tech", "Agences Web", "ONG", "Banques", "Télétravail"],
            "perspectives": "Évolution vers Lead Developer, Architecte logiciel, CTO ou fondateur de startup.",
            "demande": "Le développement web est l'une des compétences les plus recherchées au monde avec +25% de croissance annuelle.",
            "freelance": "Excellent — plateforme Upwork, Fiverr, Toptal. Revenus freelance dès le 6e mois.",
            "competences_futur": ["IA générative", "Web3", "Cloud Computing", "DevOps"],
        },
        "expert_ia": {
            "titre": "Expert en Intelligence Artificielle",
            "emoji": "🤖",
            "description": "Tu maîtrises les outils IA les plus puissants et tu les appliques dans des contextes professionnels concrets.",
            "competences": [
                "Prompt Engineering",
                "ChatGPT",
                "Claude",
                "Gemini",
                "Python IA",
                "Data Analysis",
            ],
            "technologies": ["OpenAI API", "LangChain", "Hugging Face", "Google Colab"],
            "metiers_accessibles": [
                "Prompt Engineer",
                "AI Product Manager",
                "Data Analyst",
                "Consultant IA",
                "Formateur IA",
            ],
            "salaire_haiti": "1500-4000",
            "salaire_international": "4000-12000",
            "duree_formation": "6 mois",
            "parcours_bta": "Spécialiste IA et Productivité",
            "secteurs": ["Finance", "Santé", "Éducation", "Marketing", "Consulting", "Remote"],
            "perspectives": "Secteur en explosion — les experts IA sont parmi les professionnels les mieux payés au monde.",
            "demande": "La demande en expertise IA croît de +40% par an. Les entreprises cherchent désespérément ces profils.",
            "freelance": "Excellent — services de consultation IA très demandés. Tarifs: 50-200 USD/heure.",
            "competences_futur": ["AGI", "IA multimodale", "IA embarquée", "Éthique IA"],
        },
        "technicien_informatique": {
            "titre": "Technicien Informatique",
            "emoji": "🖥️",
            "description": "Tu répares, configures et maintiens les équipements informatiques et réseaux des entreprises.",
            "competences": [
                "Hardware",
                "Windows Server",
                "Réseaux",
                "Dépannage",
                "Sécurité de base",
            ],
            "technologies": ["Active Directory", "VMware", "Cisco", "TeamViewer", "SCCM"],
            "metiers_accessibles": [
                "Technicien IT",
                "Support N1/N2",
                "Admin Réseau Junior",
                "Technicien Télécoms",
            ],
            "salaire_haiti": "600-1800",
            "salaire_international": "2500-5000",
            "duree_formation": "9 mois",
            "parcours_bta": "Technicien Informatique Professionnel",
            "secteurs": ["PME", "Hôtels", "Banques", "Hôpitaux", "Écoles", "ONG"],
            "perspectives": "Évolution vers Admin Systèmes, Ingénieur Réseau, Cybersécurité.",
            "demande": "Besoin constant dans toutes les organisations. Pénurie de techniciens qualifiés en Haïti.",
            "freelance": "Possible — maintenance informatique à domicile, support IT aux PME.",
            "competences_futur": ["Cloud hybride", "IoT", "Cybersécurité", "IA pour IT"],
        },
        "designer_graphique": {
            "titre": "Designer Graphique & Content Creator",
            "emoji": "🎨",
            "description": "Tu crées des identités visuelles, des contenus pour les réseaux sociaux et du matériel marketing professionnel.",
            "competences": [
                "Canva Pro",
                "Adobe Express",
                "Photoshop",
                "Illustrator",
                "Branding",
                "Vidéo",
            ],
            "technologies": ["Adobe Suite", "Figma", "CapCut", "DaVinci Resolve", "Midjourney"],
            "metiers_accessibles": [
                "Graphiste Freelance",
                "Community Manager",
                "Social Media Manager",
                "Brand Designer",
            ],
            "salaire_haiti": "500-1500",
            "salaire_international": "2000-6000",
            "duree_formation": "5 mois",
            "parcours_bta": "Entrepreneur Numérique",
            "secteurs": ["Agences", "Marques", "Médias", "E-commerce", "Politique", "ONG"],
            "perspectives": "Évolution vers Directeur Artistique, UX Designer, Brand Manager.",
            "demande": "Explosion du contenu numérique — chaque entreprise a besoin de contenu quotidien.",
            "freelance": "Excellent — fiverr, 99designs, réseaux sociaux. Revenus très rapides.",
            "competences_futur": ["Design IA", "Motion Design", "AR/VR Design", "3D"],
        },
        "marketeur_digital": {
            "titre": "Marketeur Digital & Growth Hacker",
            "emoji": "📊",
            "description": "Tu développes la présence en ligne des entreprises, gères les publicités et augmentes leurs revenus.",
            "competences": [
                "Meta Ads",
                "Google Ads",
                "SEO",
                "Email Marketing",
                "Analytics",
                "Copywriting",
            ],
            "technologies": [
                "Google Analytics",
                "Facebook Business",
                "HubSpot",
                "Mailchimp",
                "Semrush",
            ],
            "metiers_accessibles": [
                "Traffic Manager",
                "Community Manager",
                "Growth Hacker",
                "CMO Startup",
            ],
            "salaire_haiti": "700-2000",
            "salaire_international": "2500-7000",
            "duree_formation": "8 mois",
            "parcours_bta": "Entrepreneur Numérique",
            "secteurs": ["E-commerce", "Startups", "Agences", "Médias", "Mode", "Tourisme"],
            "perspectives": "Évolution vers CMO, Growth Lead, fondateur d'agence digitale.",
            "demande": "Le marketing digital est indispensable pour toutes les entreprises modernes.",
            "freelance": "Excellent — gestion des réseaux sociaux et publicités pour les PME locales.",
            "competences_futur": ["Marketing IA", "Automatisation", "Créateurs de contenu IA"],
        },
        "cybersecurite": {
            "titre": "Spécialiste en Cybersécurité",
            "emoji": "🔐",
            "description": "Tu protèges les systèmes informatiques contre les cyberattaques et sécurises les données sensibles.",
            "competences": ["Sécurité réseau", "Pentest", "SIEM", "Cryptographie", "Forensique"],
            "technologies": ["Wireshark", "Metasploit", "Nmap", "Kali Linux", "Splunk"],
            "metiers_accessibles": [
                "Analyste SOC",
                "Pentester",
                "RSSI Junior",
                "Consultant Sécurité",
            ],
            "salaire_haiti": "1000-3000",
            "salaire_international": "4000-12000",
            "duree_formation": "8 mois",
            "parcours_bta": "Technicien Informatique Professionnel",
            "secteurs": ["Banques", "Gouvernement", "Défense", "Santé", "Remote"],
            "perspectives": "L'un des métiers les mieux payés du numérique avec pénurie mondiale de talents.",
            "demande": "+35% de croissance annuelle. Les cyberattaques coûtent des milliards aux organisations.",
            "freelance": "Possible — audits de sécurité, tests de pénétration pour les PME.",
            "competences_futur": ["IA en cybersécurité", "Zero Trust", "Cloud Security"],
        },
    }

    profils = [
        ("lyceen_etudiant", "Lycéen / Étudiant", "🎓"),
        ("professionnel", "Professionnel en reconversion", "💼"),
        ("entrepreneur", "Entrepreneur", "🚀"),
        ("sans_emploi", "En recherche d'emploi", "🔍"),
    ]

    interets = [
        ("creer", "Créer des choses (sites, apps, designs)", "🎨"),
        ("analyser", "Analyser et comprendre les données", "📊"),
        ("reparer", "Réparer et configurer des systèmes", "🔧"),
        ("vendre", "Vendre et convaincre", "📢"),
        ("proteger", "Sécuriser et protéger", "🔐"),
        ("automatiser", "Automatiser avec l'IA", "🤖"),
    ]

    objectifs = [
        ("entreprise", "Travailler en entreprise", "🏢"),
        ("freelance", "Travailler en freelance", "💻"),
        ("remote", "Travailler à distance (remote)", "🌍"),
        ("startup", "Créer mon entreprise", "🚀"),
    ]

    niveaux = [
        ("debutant", "Débutant complet", "🌱"),
        ("quelques_bases", "J'ai quelques bases", "📖"),
        ("intermediaire", "Niveau intermédiaire", "⚡"),
    ]

    resultat = None
    metier_data = None
    erreur = None
    form_data = {}

    if request.method == "POST":
        profil = request.POST.get("profil", "")
        interet = request.POST.get("interet", "")
        objectif = request.POST.get("objectif", "")
        niveau = request.POST.get("niveau", "")
        details = request.POST.get("details", "").strip()
        form_data = request.POST

        if profil and interet and objectif and niveau:
            formations = Formation.objects.filter(actif=True).select_related("ecole")

            from ..services.ia_service import generer_parcours_oriente

            resultat_ia = generer_parcours_oriente(
                profil=profil,
                objectif=f"interet:{interet}, objectif:{objectif}",
                disponibilite=niveau,
                details=details,
                formations_disponibles=formations,
            )

            mapping_metier = {
                "creer": "developpeur_web",
                "analyser": "expert_ia",
                "reparer": "technicien_informatique",
                "vendre": "marketeur_digital",
                "proteger": "cybersecurite",
                "automatiser": "expert_ia",
            }

            metier_key = mapping_metier.get(interet, "developpeur_web")

            if objectif == "freelance":
                if interet == "creer":
                    metier_key = "designer_graphique"

            metier_data = METIERS_BTA.get(metier_key, METIERS_BTA["developpeur_web"])

            if "erreur" in resultat_ia:
                erreur = resultat_ia.get("erreur")
            else:
                resultat = resultat_ia

        else:
            erreur = "Réponds à toutes les questions pour obtenir ta recommandation."

    return render(
        request,
        "academie/simulateur.html",
        {
            "profils": profils,
            "interets": interets,
            "objectifs": objectifs,
            "niveaux": niveaux,
            "resultat": resultat,
            "metier_data": metier_data,
            "erreur": erreur,
            "form_data": form_data,
        },
    )


# ================================================
# Vues : Examens
# ================================================

@login_required
@exiger_acces_formation(lambda examen_id: Examen.objects.get(id=examen_id).formation)
def preparation_examen(request, examen_id):
    examen = get_object_or_404(Examen, id=examen_id, actif=True)

    erreurs = []

    if examen.date_disponibilite and timezone.now() < examen.date_disponibilite:
        erreurs.append(
            f"L'examen sera disponible le {examen.date_disponibilite.strftime('%d/%m/%Y à %H:%M')}"
        )

    if examen.date_expiration and timezone.now() > examen.date_expiration:
        erreurs.append("Cet examen n'est plus disponible.")

    tentatives_count = TentativeExamen.objects.filter(
        utilisateur=request.user, examen=examen
    ).count()
    tentatives_restantes = examen.tentatives_max - tentatives_count
    if tentatives_restantes <= 0:
        erreurs.append("Vous avez atteint le nombre maximum de tentatives.")

    competences = [c.strip() for c in examen.competences_evaluees.split("\n") if c.strip()]
    prerequis = [p.strip() for p in examen.prerequis_examen.split("\n") if p.strip()]
    conditions = (
        [c.strip() for c in examen.conditions_utilisation.split("\n") if c.strip()]
        if examen.conditions_utilisation
        else []
    )

    checklist = [
        ("Connexion Internet stable", "wifi"),
        ("Batterie suffisante ou secteur branché", "battery"),
        ("Navigateur compatible (Chrome, Firefox, Edge)", "browser"),
        ("Être dans un endroit calme, sans distraction", "quiet"),
    ]

    return render(
        request,
        "academie/preparation_examen.html",
        {
            "examen": examen,
            "erreurs": erreurs,
            "tentatives_restantes": tentatives_restantes,
            "competences": competences,
            "prerequis": prerequis,
            "conditions": conditions,
            "checklist": checklist,
        },
    )


@login_required
@exiger_acces_formation(lambda examen_id: Examen.objects.get(id=examen_id).formation)
def passer_examen(request, examen_id):
    examen = get_object_or_404(Examen, id=examen_id, actif=True)

    questions = list(examen.questions.prefetch_related("choix").all())
    random.shuffle(questions)

    for question in questions:
        choix_list = list(question.choix.all())
        random.shuffle(choix_list)
        question.choix_melanges = choix_list

    return render(
        request,
        "academie/examen.html",
        {
            "examen": examen,
            "questions": questions,
            "duree_secondes": examen.duree_minutes * 60,
        },
    )


@login_required
@exiger_acces_formation(lambda examen_id: Examen.objects.get(id=examen_id).formation)
def soumettre_examen(request, examen_id):
    if request.method != "POST":
        return redirect("passer_examen", examen_id=examen_id)

    examen = get_object_or_404(Examen, id=examen_id, actif=True)

    tentative = TentativeExamen.objects.create(
        utilisateur=request.user,
        examen=examen,
    )

    evenements = request.POST.get("evenements_suspects", "[]")
    try:
        tentative.evenements_suspects = json.loads(evenements)
    except Exception:
        pass

    temps_utilise = request.POST.get("temps_utilise", 0)
    tentative.temps_utilise_secondes = int(temps_utilise) if temps_utilise else 0

    total_points = 0
    points_obtenus = 0
    bonnes = 0
    mauvaises = 0
    repondues = 0

    for question in examen.questions.all():
        total_points += question.points
        reponse_key = f"question_{question.id}"

        if question.type_question == "qcm":
            choix_id = request.POST.get(reponse_key)
            if choix_id:
                repondues += 1
                choix = get_object_or_404(ChoixExamen, id=choix_id)
                if choix.est_correct:
                    points_obtenus += question.points
                    bonnes += 1
                else:
                    mauvaises += 1
        elif question.type_question in ["vrai_faux", "texte"]:
            valeur = request.POST.get(reponse_key)
            if valeur:
                repondues += 1

    score = round((points_obtenus / total_points) * 100, 1) if total_points > 0 else 0
    tentative.score = score
    tentative.reussi = score >= examen.seuil_reussite
    tentative.questions_repondues = repondues
    tentative.bonnes_reponses = bonnes
    tentative.mauvaises_reponses = mauvaises
    tentative.date_fin = timezone.now()
    tentative.save()
    # --- NOUVEAU : validation automatique des compétences liées à l'examen ---
    if tentative.reussi:
        from ..xp_utils import ajouter_xp
        ajouter_xp(request.user, examen.xp_recompense or 50)
        # Enregistrement des compétences validées par la réussite de l'examen
        from ..models import CompetenceValidee
        competences_validees = CompetenceValidee.valider_pour_examen(
            request.user, examen, tentative
        )
        for comp_validee in competences_validees:
            notifications.creer_notification(
                request.user,
                "🏆 Nouvelle compétence validée !",
                f"Tu maîtrises maintenant {comp_validee.competence.nom} ({comp_validee.get_niveau_display()}).",
                "/mon-profil-competences/"
            )

        if examen.certificat_auto:
            Certificat.objects.get_or_create(
                utilisateur=request.user,
                formation=examen.formation,
            )

    if score < 70:
        contexte_feedback = f"L'étudiant a obtenu {score}% à l'examen {examen.titre}. Donne un conseil bref et motivant en 2 phrases."
    else:
        contexte_feedback = f"L'étudiant a réussi l'examen {examen.titre} avec {score}%. Félicite-le brièvement en 2 phrases."

    try:
        from ..services.ia_service import initialiser_ia
        client = initialiser_ia()
        response = client.models.generate_content(
            model="gemini-2.5-flash", contents=contexte_feedback
        )
        feedback_ia = response.text
    except Exception:
        feedback_ia = (
            "Continue à pratiquer régulièrement — chaque tentative te rapproche de la maîtrise !"
        )

    return render(
        request,
        "academie/resultat_examen.html",
        {
            "examen": examen,
            "tentative": tentative,
            "score": score,
            "reussi": tentative.reussi,
            "feedback_ia": feedback_ia,
        },
    )

# ================================================
# Vues : Réactions génériques (sujets/réponses)
# ================================================

@require_POST
@login_required(login_url="/connexion/")
def toggle_reaction_generique(request, type_cible, objet_id):
    MODELES = {
        "sujet": Sujet,
        "reponse": Reponse,
    }

    modele = MODELES.get(type_cible)

    if modele is None:
        return JsonResponse(
            {"success": False, "message": "Type de contenu invalide."},
            status=400,
        )

    objet = get_object_or_404(modele, pk=objet_id)

    content_type = ContentType.objects.get_for_model(modele)

    reaction = Reaction.objects.filter(
        utilisateur=request.user,
        content_type=content_type,
        object_id=objet.pk,
    ).first()

    if reaction:
        reaction.delete()
        aime = False
    else:
        Reaction.objects.create(
            utilisateur=request.user,
            content_type=content_type,
            object_id=objet.pk,
        )
        aime = True

    nb_likes = Reaction.objects.filter(
        content_type=content_type,
        object_id=objet.pk,
    ).count()

    return JsonResponse(
        {
            "success": True,
            "aime": aime,
            "nb_likes": nb_likes,
            "type": type_cible,
            "objet_id": objet.pk,
        }
    )


# ================================================
# Fonction utilitaire (interne)
# ================================================

def _prix_avec_promotion(formation):
    from ..models import Promotion
    from decimal import Decimal
    prix_original = Decimal(str(formation.prix))
    for promo in Promotion.objects.filter(actif=True):
        if promo.s_applique_a(formation):
            reduction = prix_original * (Decimal(promo.pourcentage_reduction) / 100)
            return prix_original - reduction, promo
    return prix_original, None


def verifier_acces_formation(user, formation):
    if formation.gratuit:
        return True
    if not user.is_authenticated:
        return False
    return AccesFormationDebloque.objects.filter(utilisateur=user, formation=formation).exists()


# ================================================
# Notes personnelles sur leçon
# ================================================

import json
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from ..models import NoteLecon

@login_required(login_url='/connexion/')
def api_note_lecon(request, lecon_id):
    """
    GET  : récupère la note existante pour l'utilisateur et la leçon
    POST : sauvegarde ou met à jour la note
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            note, _ = NoteLecon.objects.update_or_create(
                utilisateur=request.user,
                lecon_id=lecon_id,
                defaults={'contenu': data.get('contenu', '')}
            )
            return JsonResponse({'succes': True})
        except json.JSONDecodeError:
            return JsonResponse({'erreur': 'Données JSON invalides'}, status=400)
        except Exception as e:
            return JsonResponse({'erreur': str(e)}, status=500)

    note = NoteLecon.objects.filter(utilisateur=request.user, lecon_id=lecon_id).first()
    return JsonResponse({'contenu': note.contenu if note else ''})


# ================================================
# VIEWS.PY — Soumission de projet pratique (étudiant) + évaluation (formateur)
# ================================================

@login_required(login_url='/connexion/')
def soumettre_projet(request, formation_id):
    """Étudiant soumet un livrable pratique pour évaluation."""
    formation = get_object_or_404(Formation, id=formation_id)

    if not verifier_acces_formation(request.user, formation):
        messages.error(request, "🔒 Accès non autorisé.")
        return redirect('detail_formation', formation_id=formation_id)

    if request.method == 'POST':
        SoumissionProjet.objects.create(
            utilisateur=request.user, formation=formation,
            titre=request.POST.get('titre', ''), description=request.POST.get('description', ''),
            lien_livrable=request.POST.get('lien_livrable', ''),
            fichier_livrable=request.FILES.get('fichier_livrable'),
        )
        messages.success(request, "✅ Projet soumis ! Un formateur va l'évaluer sous peu.")
        return redirect('detail_formation', formation_id=formation_id)

    return render(request, 'academie/soumettre_projet.html', {'formation': formation})


@login_required(login_url='/connexion/')
@staff_member_required   # ou un décorateur personnalisé si disponible
def evaluer_soumissions(request):
    """Vue formateur — liste des soumissions à évaluer."""
    soumissions = SoumissionProjet.objects.filter(statut='en_attente').select_related('utilisateur', 'formation')
    return render(request, 'academie/evaluer_soumissions.html', {'soumissions': soumissions})


@login_required(login_url='/connexion/')
@staff_member_required
def valider_soumission(request, soumission_id):
    """Traite l'évaluation d'une soumission par le formateur."""
    if request.method == 'POST':
        soumission = get_object_or_404(SoumissionProjet, id=soumission_id)
        action = request.POST.get('action')
        note = request.POST.get('note')
        feedback = request.POST.get('feedback', '')

        if action == 'valider':
            competence_ids = request.POST.getlist('competences')
            soumission.competences_a_valider.set(competence_ids)
            soumission.valider(request.user, note=int(note) if note else None, feedback=feedback)
            messages.success(request, "✅ Soumission validée — compétences attribuées.")
        elif action == 'a_revoir':
            soumission.statut = 'a_revoir'
            soumission.feedback_formateur = feedback
            soumission.evalue_par = request.user
            soumission.date_evaluation = timezone.now()
            soumission.save()
            messages.info(request, "🔄 Retour envoyé à l'étudiant.")
        elif action == 'refuser':
            soumission.statut = 'refusee'
            soumission.feedback_formateur = feedback
            soumission.evalue_par = request.user
            soumission.date_evaluation = timezone.now()
            soumission.save()

    return redirect('evaluer_soumissions')