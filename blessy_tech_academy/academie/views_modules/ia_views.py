# ================================================
# VIEWS_MODULES/IA_VIEWS.PY — Vues Blessy AI (API et page chat)
# ================================================

import json
import markdown as markdown_lib

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_POST
from django_ratelimit.decorators import ratelimit

from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import (
    Formation, Module, Lecon, HistoriqueConversationIA,
    Examen, QuestionExamen, ChoixExamen, Ecole, Parcours,
    ProgressionLecon, Quiz, Question,
)
from ..services.ia_service import (
    assistant_code,
    blessy_ai_repondre,
    chatbot_tuteur,
    correction_automatique,
    explication_concept,
    generateur_exercices,
    generer_contenu_formation,
    generer_contenu_lecon,
    generer_ecole_description,
    generer_programme_complet,
    generer_quiz,
    parcours_adaptatif,
    recommander_formations,
    generer_examen_complet,
    generer_parcours_professionnel_admin,
    analyser_plateforme_ia,
    initialiser_ia,
    generer_article,
    simuler_carriere as simuler_carriere_ia,
)
from ..permissions import role_required
from .. import notifications


# ================================================
# Fonction utilitaire (copiée depuis core_views pour éviter l'import circulaire)
# ================================================

def _construire_contexte_utilisateur(request):
    """Construit un contexte utilisateur pour personnaliser les réponses du chatbot."""
    contexte_utilisateur = None
    if request.user.is_authenticated:
        formations_suivies = []
        progressions = (
            ProgressionLecon.objects.filter(utilisateur=request.user, terminee=True)
            .select_related("lecon__module__formation")
            .order_by("-date_completion")[:3]
        )
        for progression in progressions:
            formation = progression.lecon.module.formation
            if formation and formation.nom not in formations_suivies:
                formations_suivies.append(formation.nom)

        contexte_utilisateur = {
            "prenom": request.user.first_name or request.user.username,
            "formations_suivies": formations_suivies,
        }
    return contexte_utilisateur


# ================================================
# Page du chat IA
# ================================================

def chat_ia(request):
    historique = request.session.get("chat_historique", [])
    return render(
        request,
        "academie/chat_ia.html",
        {
            "historique_chat": historique,
        },
    )


# ================================================
# Page de recommandations IA
# ================================================

def recommandations_ia(request):
    """Page de recommandations personnalisées."""
    recommandations = None
    interets = ""

    if request.method == "POST":
        interets = request.POST.get("interets", "").strip()
        if interets:
            formations_actives = Formation.objects.filter(actif=True)
            recommandations = recommander_formations(interets, formations_actives)

    return render(
        request,
        "academie/recommandations_ia.html",
        {
            "recommandations": recommandations,
            "interets": interets,
        },
    )


# ================================================
# API endpoints IA
# ================================================

@login_required
@ratelimit(key="user_or_ip", rate="20/m", block=True)
def api_chat_ia(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            question = data.get("question", "").strip()

            if not question:
                return JsonResponse({"erreur": "Question vide"}, status=400)

            if len(question) > 500:
                return JsonResponse(
                    {"erreur": "Question trop longue (max 500 caractères)"}, status=400
                )

            formations_actives = Formation.objects.filter(actif=True)[:5]
            historique = request.session.get("chat_historique", [])
            contexte_utilisateur = _construire_contexte_utilisateur(request)

            reponse = blessy_ai_repondre(
                question,
                formations_actives,
                historique=historique,
                contexte_utilisateur=contexte_utilisateur,
            )

            historique.append({"role": "user", "content": question})
            historique.append({"role": "assistant", "content": reponse})
            request.session["chat_historique"] = historique[-12:]
            request.session.modified = True

            try:
                reponse_html = markdown_lib.markdown(reponse)
            except Exception:
                reponse_html = reponse

            return JsonResponse({"reponse": reponse_html})

        except Exception as e:
            return JsonResponse({"erreur": str(e)}, status=500)

    return JsonResponse({"erreur": "Méthode non autorisée"}, status=405)


@require_POST
def api_assistant_code(request):
    try:
        data = json.loads(request.body)
        code = data.get("code", "")
        langage = data.get("langage", "python")
        question = data.get("question", "")

        if not code:
            return JsonResponse({"erreur": 'Le champ "code" est requis.'}, status=400)

        reponse = assistant_code(code=code, langage=langage, question=question)
        return JsonResponse({"reponse": reponse, "fonction": "assistant_code"})
    except json.JSONDecodeError:
        return JsonResponse({"erreur": "JSON invalide"}, status=400)
    except Exception as e:
        return JsonResponse({"erreur": str(e)}, status=500)


@require_POST
def api_generateur_exercices(request):
    try:
        data = json.loads(request.body)
        sujet = data.get("sujet", "")
        niveau = data.get("niveau", "debutant")
        format_ex = data.get("format_exercice", "code")

        if not sujet:
            return JsonResponse({"erreur": 'Le champ "sujet" est requis.'}, status=400)

        reponse = generateur_exercices(sujet=sujet, niveau=niveau, format_exercice=format_ex)
        return JsonResponse({"reponse": reponse, "fonction": "generateur_exercices"})
    except json.JSONDecodeError:
        return JsonResponse({"erreur": "JSON invalide"}, status=400)
    except Exception as e:
        return JsonResponse({"erreur": str(e)}, status=500)


@require_POST
def api_explication_concept(request):
    try:
        data = json.loads(request.body)
        question = data.get("question", "")
        niveau_eleve = data.get("niveau_eleve", "debutant")

        if not question:
            return JsonResponse({"erreur": 'Le champ "question" est requis.'}, status=400)

        reponse = explication_concept(question=question, niveau_eleve=niveau_eleve)
        return JsonResponse({"reponse": reponse, "fonction": "explication_concept"})
    except json.JSONDecodeError:
        return JsonResponse({"erreur": "JSON invalide"}, status=400)
    except Exception as e:
        return JsonResponse({"erreur": str(e)}, status=500)


@require_POST
def api_correction_automatique(request):
    try:
        data = json.loads(request.body)
        enonce = data.get("enonce", "")
        reponse_eleve = data.get("reponse_eleve", "")
        bareme = data.get("bareme", "")

        if not enonce or not reponse_eleve:
            return JsonResponse(
                {"erreur": 'Les champs "enonce" et "reponse_eleve" sont requis.'}, status=400
            )

        reponse = correction_automatique(enonce=enonce, reponse_eleve=reponse_eleve, bareme=bareme)
        return JsonResponse({"reponse": reponse, "fonction": "correction_automatique"})
    except json.JSONDecodeError:
        return JsonResponse({"erreur": "JSON invalide"}, status=400)
    except Exception as e:
        return JsonResponse({"erreur": str(e)}, status=500)


@require_POST
def api_parcours_adaptatif(request):
    try:
        data = json.loads(request.body)
        profil_scores = data.get("profil_scores", {})
        parcours_actuel = data.get("parcours_actuel", "")
        objectif = data.get("objectif", "")

        if not profil_scores:
            return JsonResponse({"erreur": 'Le champ "profil_scores" est requis.'}, status=400)

        reponse = parcours_adaptatif(
            profil_scores=profil_scores, parcours_actuel=parcours_actuel, objectif=objectif
        )
        return JsonResponse({"reponse": reponse, "fonction": "parcours_adaptatif"})
    except json.JSONDecodeError:
        return JsonResponse({"erreur": "JSON invalide"}, status=400)
    except Exception as e:
        return JsonResponse({"erreur": str(e)}, status=500)


@require_POST
def api_chatbot_tuteur(request):
    try:
        data = json.loads(request.body)
        message = data.get("message", "")
        historique = data.get("historique", [])
        niveau_eleve = data.get("niveau_eleve", "debutant")

        if not message:
            return JsonResponse({"erreur": 'Le champ "message" est requis.'}, status=400)

        reponse = chatbot_tuteur(message=message, historique=historique, niveau_eleve=niveau_eleve)
        return JsonResponse({"reponse": reponse, "fonction": "chatbot_tuteur"})
    except json.JSONDecodeError:
        return JsonResponse({"erreur": "JSON invalide"}, status=400)
    except Exception as e:
        return JsonResponse({"erreur": str(e)}, status=500)


@login_required
@role_required("resp_academique", "admin", "super_admin")
def api_generer_formation(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            nom = data.get("nom", "").strip()
            ecole = data.get("ecole", "").strip()
            if not nom:
                return JsonResponse({"erreur": "Nom de formation requis"}, status=400)

            contenu = generer_contenu_formation(nom, ecole)
            return JsonResponse(contenu)

        except Exception as e:
            return JsonResponse({"erreur": str(e)}, status=500)

    return JsonResponse({"erreur": "Méthode non autorisée"}, status=405)


@login_required
@role_required("resp_academique", "examinateur", "admin", "super_admin")
def api_generer_quiz(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            sujet = data.get("sujet", "").strip()
            nombre = int(data.get("nombre", 5))

            if not sujet:
                return JsonResponse({"erreur": "Sujet requis"}, status=400)

            questions = generer_quiz(sujet, nombre)

            if not questions:
                return JsonResponse({"erreur": "Génération échouée"}, status=500)

            return JsonResponse({"questions": questions})

        except Exception as e:
            return JsonResponse({"erreur": str(e)}, status=500)

    return JsonResponse({"erreur": "Méthode non autorisée"}, status=405)


@login_required
@role_required('resp_academique', 'admin', 'super_admin')
def api_generer_quiz_module(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            module_id = data.get('module_id')
            nombre = int(data.get('nombre', 5))
            module = Module.objects.select_related('formation').get(id=module_id)
            questions = generer_quiz(module.titre, nombre)

            if not questions:
                return JsonResponse({'erreur': 'Génération échouée'}, status=500)

            quiz = Quiz.objects.create(
                formation=module.formation,
                module=module,
                titre=f"Quiz — {module.titre}",
                actif=True,
            )

            for i, q_data in enumerate(questions, start=1):
                Question.objects.create(
                    quiz=quiz,
                    texte=q_data.get('texte', ''),
                    choix_a=q_data.get('choix_a', ''),
                    choix_b=q_data.get('choix_b', ''),
                    choix_c=q_data.get('choix_c', ''),
                    choix_d=q_data.get('choix_d', ''),
                    bonne_reponse=q_data.get('bonne_reponse', 'a'),
                    explication=q_data.get('explication', ''),
                    ordre=i,
                )

            return JsonResponse({'succes': True, 'quiz_id': quiz.id, 'nombre_questions': len(questions)})

        except Exception as e:
            return JsonResponse({'erreur': str(e)}, status=500)

    return JsonResponse({'erreur': 'Méthode non autorisée'}, status=405)


@login_required
@role_required("resp_academique", "admin", "super_admin")
def api_generer_programme(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            formation_id = data.get("formation_id")

            if not formation_id:
                return JsonResponse({"erreur": "ID de formation requis"}, status=400)

            formation = Formation.objects.get(id=formation_id)

            programme = generer_programme_complet(
                formation.nom, formation.description, formation.niveau
            )

            if not programme:
                return JsonResponse({"erreur": "Génération échouée"}, status=500)

            for index_module, module_data in enumerate(programme, start=1):
                module = Module.objects.create(
                    formation=formation,
                    titre=module_data.get("titre", f"Module {index_module}"),
                    description=module_data.get("description", ""),
                    ordre=index_module,
                )

                for index_lecon, lecon_data in enumerate(module_data.get("lecons", []), start=1):
                    Lecon.objects.create(
                        module=module,
                        titre=lecon_data.get("titre", f"Leçon {index_lecon}"),
                        resume=lecon_data.get("resume", ""),
                        duree_minutes=lecon_data.get("duree_minutes", 15),
                        ordre=index_lecon,
                    )

            return JsonResponse(
                {
                    "succes": True,
                    "nombre_modules": len(programme),
                    "message": f"{len(programme)} modules créés avec succès !",
                }
            )

        except Formation.DoesNotExist:
            return JsonResponse({"erreur": "Formation introuvable"}, status=404)
        except Exception as e:
            return JsonResponse({"erreur": str(e)}, status=500)

    return JsonResponse({"erreur": "Méthode non autorisée"}, status=405)


@login_required
@role_required("formateur", "resp_academique", "admin", "super_admin")
def api_generer_contenu_lecon(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            lecon_id = data.get("lecon_id")

            if not lecon_id:
                return JsonResponse({"erreur": "ID de leçon requis"}, status=400)

            lecon = Lecon.objects.select_related("module__formation").get(id=lecon_id)
            contenu = generer_contenu_lecon(
                titre_lecon=lecon.titre,
                resume_lecon=lecon.resume,
                contexte_formation=lecon.module.formation.nom,
                contexte_module=lecon.module.titre,
            )

            lecon.contenu = contenu
            lecon.save()

            return JsonResponse(
                {
                    "succes": True,
                    "contenu": contenu,
                }
            )

        except Lecon.DoesNotExist:
            return JsonResponse({"erreur": "Leçon introuvable"}, status=404)
        except Exception as e:
            return JsonResponse({"erreur": str(e)}, status=500)

    return JsonResponse({"erreur": "Méthode non autorisée"}, status=405)


@login_required
@role_required("resp_academique", "admin", "super_admin")
def api_generer_contenu_module(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            module_id = data.get("module_id")

            if not module_id:
                return JsonResponse({"erreur": "ID de module requis"}, status=400)

            module = (
                Module.objects.select_related("formation")
                .prefetch_related("lecons")
                .get(id=module_id)
            )

            lecons = module.lecons.all()
            nombre_traitees = 0

            for lecon in lecons:
                contenu = generer_contenu_lecon(
                    titre_lecon=lecon.titre,
                    resume_lecon=lecon.resume,
                    contexte_formation=module.formation.nom,
                    contexte_module=module.titre,
                )
                lecon.contenu = contenu
                lecon.save()
                nombre_traitees += 1

            return JsonResponse(
                {
                    "succes": True,
                    "nombre_lecons": nombre_traitees,
                    "message": f"{nombre_traitees} leçons mises à jour avec succès !",
                }
            )

        except Module.DoesNotExist:
            return JsonResponse({"erreur": "Module introuvable"}, status=404)
        except Exception as e:
            return JsonResponse({"erreur": str(e)}, status=500)

    return JsonResponse({"erreur": "Méthode non autorisée"}, status=405)


@staff_member_required
@ratelimit(key='user', rate='15/h', method='POST', block=True)
def api_generer_examen(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            formation_id = data.get('formation_id')
            niveau = data.get('niveau', 'intermediaire')
            nombre_questions = int(data.get('nombre_questions', 10))

            formation = Formation.objects.get(id=formation_id)

            resultat = generer_examen_complet(formation.nom, niveau, nombre_questions)

            if 'erreur' in resultat:
                return JsonResponse({'erreur': resultat['erreur']}, status=500)

            examen = Examen.objects.create(
                formation=formation,
                titre=resultat.get('titre', f"Examen — {formation.nom}"),
                duree_minutes=resultat.get('duree_minutes', 45),
                seuil_reussite=resultat.get('seuil_reussite', 70),
                competences_evaluees=resultat.get('competences_evaluees', ''),
            )

            for i, q_data in enumerate(resultat.get('questions', []), start=1):
                question = QuestionExamen.objects.create(
                    examen=examen,
                    texte=q_data.get('texte', ''),
                    type_question='qcm',
                    ordre=i,
                    points=q_data.get('points', 10),
                )
                for choix_data in q_data.get('choix', []):
                    ChoixExamen.objects.create(
                        question=question,
                        texte=choix_data.get('texte', ''),
                        est_correct=choix_data.get('correct', False),
                    )

            return JsonResponse({
                'succes': True,
                'examen_id': examen.id,
                'nombre_questions': len(resultat.get('questions', [])),
            })

        except Exception as e:
            return JsonResponse({'erreur': str(e)}, status=500)

    return JsonResponse({'erreur': 'Méthode non autorisée'}, status=405)


@require_POST
@login_required
def api_generer_ecole(request):
    try:
        data = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse(
            {
                "success": False,
                "error": "Données JSON invalides."
            },
            status=400,
        )

    nom_ecole = str(data.get("nom", "")).strip()
    domaine = str(data.get("domaine", "")).strip()

    if not nom_ecole:
        return JsonResponse(
            {
                "success": False,
                "error": "Le nom de l'école est obligatoire."
            },
            status=400,
        )

    try:
        contenu = generer_ecole_description(
            nom_ecole=nom_ecole,
            domaine=domaine,
        )
        return JsonResponse(
            {
                "success": True,
                "nom": nom_ecole,
                "domaine": domaine,
                "contenu": contenu,
            }
        )
    except Exception as e:
        return JsonResponse(
            {
                "success": False,
                "error": str(e),
            },
            status=500,
        )


@staff_member_required
@ratelimit(key='user', rate='15/h', method='POST', block=True)
def api_generer_parcours_admin(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            titre_metier = data.get('titre_metier', '')
            niveau = data.get('niveau', 'intermediaire')

            resultat = generer_parcours_professionnel_admin(titre_metier, niveau)

            if 'erreur' in resultat:
                return JsonResponse({'erreur': resultat['erreur']}, status=500)

            parcours = Parcours.objects.create(
                titre=resultat.get('titre', titre_metier),
                icone=resultat.get('icone', '🚀'),
                description=resultat.get('description', ''),
                duree_mois=resultat.get('duree_mois_totale', 12),
                prix=resultat.get('prix_suggere', 300),
                actif=False,
            )

            formations_liees = 0
            for nom_suggere in resultat.get('formations_recommandees', []):
                formation_trouvee = Formation.objects.filter(nom__icontains=nom_suggere.split()[0]).first()
                if formation_trouvee:
                    parcours.formations.add(formation_trouvee)
                    formations_liees += 1

            return JsonResponse({
                'succes': True,
                'parcours_id': parcours.id,
                'formations_liees': formations_liees,
                'formations_suggerees_total': len(resultat.get('formations_recommandees', [])),
            })

        except Exception as e:
            return JsonResponse({'erreur': str(e)}, status=500)

    return JsonResponse({'erreur': 'Méthode non autorisée'}, status=405)


@login_required(login_url='/connexion/')
def api_historique_ia(request):
    historique = HistoriqueConversationIA.objects.filter(
        utilisateur=request.user
    ).order_by('-date_creation')[:20]
    data = [{'role': h.role, 'contenu': h.contenu} for h in reversed(historique)]
    return JsonResponse({'historique': data})


# ================================================
# API IA supplémentaires
# ================================================

@login_required
@role_required("marketing", "resp_academique", "admin", "super_admin")
def api_generer_article(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            titre = data.get("titre", "").strip()
            tags = data.get("tags", "").strip()

            if not titre:
                return JsonResponse({"erreur": "Titre requis"}, status=400)

            resultat = generer_article(titre, tags)
            return JsonResponse(resultat)
        except Exception as e:
            return JsonResponse({"erreur": str(e)}, status=500)
    return JsonResponse({"erreur": "Méthode non autorisée"}, status=405)


@require_POST
def api_simuler_carriere(request):
    try:
        data = json.loads(request.body)
        metier = data.get("metier", "").strip()
        if not metier:
            return JsonResponse({"erreur": 'Le champ "metier" est requis.'}, status=400)
        reponse = simuler_carriere_ia(metier=metier)
        return JsonResponse({"reponse": reponse, "metier": metier})
    except json.JSONDecodeError:
        return JsonResponse({"erreur": "JSON invalide"}, status=400)
    except Exception as e:
        return JsonResponse({"erreur": str(e)}, status=500)