# ================================================
# ACADEMIE/VIEWS.PY — Version finale après extraction admin_views
# ================================================

import hashlib
import json
import os
import random
from datetime import timedelta
from decimal import Decimal
from io import StringIO

import filetype
import markdown as markdown_lib

from django.conf import settings
from django.contrib import admin, messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.paginator import Paginator
from django.db import transaction as db_transaction
from django.db.models import Avg, Count, Q, Sum, Subquery, OuterRef, IntegerField
from django.db.models.functions import TruncMonth
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils import timezone, translation
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.contenttypes.models import ContentType

from django_ratelimit.decorators import ratelimit
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from . import notifications
from .forms import ConnexionForm, InscriptionCompteForm, SujetForm

from .services.ia_service import (
    attribuer_badges,
    generer_article,
    analyser_plateforme_ia,
    assistant_backoffice_ia,
)

from .services.ia_service import simuler_carriere as simuler_carriere_ia

# ============================================================
# MODÈLES DE L'APP ACADEMIE
# ============================================================

from .models import (
    AccesFormationDebloque,
    Article,
    BadgeForum,
    Certificat,
    Coupon,
    HistoriqueConversationIA,
    Inscription,
    InteractionCRM,
    Invoice,
    LogAudit,
    MoyenPaiement,
    Order,
    OrderItem,
    OutilRecommande,
    ProjetEtudiant,
    Promotion,
    Reaction,
    Refund,
    Reponse,
    Sujet,
    Temoignage,
    Transaction,
)

# ============================================================
# MODÈLES UTILISATEURS
# ============================================================

from users.models import Enseignant

# ============================================================
# MODÈLES PÉDAGOGIQUES
# ============================================================

from .models import (
    Ecole,
    Formation,
    Module,
    Lecon,
    ProgressionLecon,
    Quiz,
    Question,
    ResultatQuiz,
    Parcours,
    Competence,
    LearningOutcome,
    WorkflowFormation,
    Examen,
    QuestionExamen,
    ChoixExamen,
    TentativeExamen,
)

from .permissions import enregistrer_log, role_required
from .xp_utils import ajouter_xp
from .services.async_tasks import executer_en_arriere_plan
from .services.email_service import _envoyer_email


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


# ============================================================
# RÉEXPORT DES VUES DEPUIS views_modules
# ============================================================
from .views_modules import *


# ================================================
# Dashboard IA (resp_academique, direction, admin)
# ================================================
@login_required
@role_required("resp_academique", "direction", "admin", "super_admin")
def vue_dashboard_ia(request):
    from django.contrib.auth.models import User
    from django.db.models import Count, Q, Sum

    from .models import Article, Order, ResultatQuiz
    from .models import Formation, Lecon

    formations_stats = (
        Formation.objects.filter(actif=True)
        .annotate(
            nb_inscrits=Count("orderitem", filter=Q(orderitem__commande__statut="paye")),
        )
        .order_by("-nb_inscrits")[:10]
    )

    lecons_abandon = Lecon.objects.annotate(
        nb_vues=Count("progressions"),
        nb_terminees=Count("progressions", filter=Q(progressions__terminee=True)),
    ).filter(nb_vues__gt=0)

    quiz_difficiles = (
        ResultatQuiz.objects.values("quiz__titre")
        .annotate(score_moyen=Avg("score"), nb_tentatives=Count("id"))
        .order_by("score_moyen")[:5]
    )

    articles_populaires = Article.objects.filter(publie=True).order_by("-date_publication")[:5]

    contexte_donnees = f"""
Formations les plus vendues : {[(f.nom, f.nb_inscrits) for f in formations_stats[:5]]}
Quiz avec scores les plus bas (difficiles) : {list(quiz_difficiles)}
Nombre total de formations actives : {Formation.objects.filter(actif=True).count()}
Nombre d'étudiants inscrits : {User.objects.filter(is_staff=False).count()}
Chiffre d'affaires : {Order.objects.filter(statut="paye").aggregate(t=Sum("total"))["t"] or 0} $
"""

    analyse_ia = None
    if request.GET.get("lancer_analyse"):
        analyse_ia = analyser_plateforme_ia(contexte_donnees)
    if analyse_ia:
        analyse_ia = analyse_ia.replace("##", "").replace("**", "").replace("---", "")
    return render(
        request,
        "admin/dashboard_ia.html",
        {
            "title": "🧠 Dashboard IA — Intelligence Décisionnelle",
            "formations_stats": formations_stats,
            "quiz_difficiles": quiz_difficiles,
            "articles_populaires": articles_populaires,
            "analyse_ia": analyse_ia,
        },
    )


# ================================================
# Statistiques (admin uniquement)
# ================================================
@login_required
@role_required("direction", "admin", "super_admin")
def statistiques(request):
    from django.db.models import Sum

    total_etudiants = User.objects.filter(is_active=True).count()
    total_formations = Formation.objects.filter(actif=True).count()
    total_certificats = Certificat.objects.count()
    total_leads = Inscription.objects.filter(formation__gratuit=True).count()
    total_inscriptions = Inscription.objects.count()
    taux_conversion = 0
    if total_leads > 0:
        taux_conversion = round((total_inscriptions / total_leads) * 100)

    telechargements = total_leads
    comptes_crees = User.objects.count()
    inscriptions_payantes = Inscription.objects.filter(formation__gratuit=False).count()
    certificats_delivres = total_certificats
    taux_leads_comptes = (
        round((comptes_crees / telechargements) * 100) if telechargements > 0 else 0
    )
    taux_comptes_payant = (
        round((inscriptions_payantes / comptes_crees) * 100) if comptes_crees > 0 else 0
    )
    taux_payant_certif = (
        round((certificats_delivres / inscriptions_payantes) * 100)
        if inscriptions_payantes > 0
        else 0
    )

    total_revenus = (
        Inscription.objects.filter(formation__gratuit=False).aggregate(
            total=Sum("formation__prix")
        )["total"]
        or 0
    )

    debut_mois = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    certificats_mois = Certificat.objects.filter(date_emission__gte=debut_mois).count()

    quiz_generees = Quiz.objects.count()
    contenus_generes = Lecon.objects.filter(contenu__isnull=False).exclude(contenu="").count()
    formations_populaires = (
        Formation.objects.filter(actif=True)
        .annotate(nb_inscriptions=Count("inscriptions"))
        .order_by("-nb_inscriptions")[:5]
    )
    douze_mois = timezone.now() - timedelta(days=365)
    inscriptions_mensuelles = (
        Inscription.objects.filter(date_inscription__gte=douze_mois)
        .annotate(mois=TruncMonth("date_inscription"))
        .values("mois")
        .annotate(total=Count("id"))
        .order_by("mois")
    )
    mois_labels = [item["mois"].strftime("%b %Y") for item in inscriptions_mensuelles]
    mois_data = [item["total"] for item in inscriptions_mensuelles]

    total_sujets = Sujet.objects.count()
    total_reponses = Reponse.objects.count()
    # Membres actifs : utilisateurs ayant au moins un sujet ou une réponse
    membres_actifs = User.objects.filter(
        Q(id__in=Sujet.objects.values('auteur')) | Q(id__in=Reponse.objects.values('auteur'))
    ).distinct().count()

    alertes = []
    inscriptions_non_traitees = Inscription.objects.filter(traite=False).count()
    if inscriptions_non_traitees > 0:
        alertes.append(f"{inscriptions_non_traitees} inscriptions non traitées")
    formations_sans_modules = Formation.objects.filter(actif=True, modules__isnull=True).count()
    if formations_sans_modules > 0:
        alertes.append(f"{formations_sans_modules} formations sans modules")
    etudiants_inactifs = User.objects.filter(is_active=True, progressions__isnull=True).count()
    if etudiants_inactifs > 0:
        alertes.append(f"{etudiants_inactifs} étudiants inactifs")

    contexte = {
        "total_etudiants": total_etudiants,
        "total_formations": total_formations,
        "total_certificats": total_certificats,
        "total_revenus": total_revenus,
        "total_leads": total_leads,
        "total_inscriptions": total_inscriptions,
        "taux_conversion": taux_conversion,
        "formations_populaires": formations_populaires,
        "mois_labels": mois_labels,
        "mois_data": mois_data,
        "total_sujets": total_sujets,
        "total_reponses": total_reponses,
        "membres_actifs": membres_actifs,
        "alertes": alertes,
        "telechargements": telechargements,
        "comptes_crees": comptes_crees,
        "inscriptions_payantes": inscriptions_payantes,
        "certificats_delivres": certificats_delivres,
        "taux_leads_comptes": taux_leads_comptes,
        "taux_comptes_payant": taux_comptes_payant,
        "taux_payant_certif": taux_payant_certif,
        "certificats_mois": certificats_mois,
        "quiz_generees": quiz_generees,
        "contenus_generes": contenus_generes,
    }
    return render(request, "academie/statistiques.html", contexte)


    
# ================================================
# Certificats PDF
# ================================================
@login_required(login_url="/connexion/")
def telecharger_certificat(request, formation_id):
    import base64
    from io import BytesIO

    import qrcode

    from .models import Certificat

    formation = Formation.objects.prefetch_related("modules__lecons").get(
        id=formation_id, actif=True
    )

    pourcentage = formation.progression_pour(request.user)

    if pourcentage < 100:
        messages.error(
            request,
            f"❌ Tu dois compléter 100% de la formation pour obtenir le certificat "
            f"(progression actuelle : {pourcentage}%).",
        )
        return redirect("detail_formation", formation_id=formation_id)

    chaine = f"{request.user.id}-{formation.id}-{request.user.date_joined}"
    numero = f"BTA-{hashlib.md5(chaine.encode()).hexdigest()[:8].upper()}"

    certificat, created = Certificat.objects.get_or_create(
        utilisateur=request.user, formation=formation, defaults={"numero": numero}
    )
    if not created:
        numero = certificat.numero

    url_verification = request.build_absolute_uri(f"/certificat/{numero}/")
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(url_verification)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    qr_code_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

    contexte = {
        "prenom": request.user.first_name or request.user.username,
        "nom": request.user.last_name or "",
        "formation": formation,
        "date_emission": certificat.date_emission.strftime("%d %B %Y"),
        "numero_certificat": numero,
        "qr_code_base64": qr_code_base64,
        "url_verification": url_verification,
    }

    html_certificat = render_to_string("academie/pdf/certificat.html", contexte, request=request)

    try:
        from weasyprint import HTML
        pdf = HTML(string=html_certificat, base_url=request.build_absolute_uri("/")).write_pdf()
        nom_fichier = f"certificat-{formation.nom.replace(' ', '-').lower()}-BTA.pdf"
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{nom_fichier}"'
        return response
    except Exception as e:
        messages.error(request, f"❌ Erreur lors de la génération du certificat : {str(e)}")
        return redirect("detail_formation", formation_id=formation_id)


# ================================================
# Forum — Likes et acceptation réponse (conservés)
# ================================================

@login_required(login_url="/connexion/")
def forum_liker(request, type_cible, cible_id):
    if request.method == "POST":
        try:
            if type_cible == "sujet":
                sujet = Sujet.objects.get(id=cible_id)
                reaction, cree = Reaction.objects.get_or_create(
                    utilisateur=request.user,
                    sujet=sujet,
                )
                if not cree:
                    reaction.delete()
                    liked = False
                else:
                    liked = True
                total = sujet.reactions.count()

            elif type_cible == "reponse":
                reponse = Reponse.objects.get(id=cible_id)
                reaction, cree = Reaction.objects.get_or_create(
                    utilisateur=request.user,
                    reponse=reponse,
                )
                if not cree:
                    reaction.delete()
                    liked = False
                else:
                    liked = True
                total = reponse.reactions.count()

            else:
                return JsonResponse({"erreur": "Type invalide"}, status=400)

            return JsonResponse(
                {
                    "succes": True,
                    "liked": liked,
                    "total": total,
                }
            )

        except Exception as e:
            return JsonResponse({"erreur": str(e)}, status=500)

    return JsonResponse({"erreur": "Méthode non autorisée"}, status=405)


@login_required(login_url="/connexion/")
def forum_accepter_reponse(request, reponse_id):
    if request.method == "POST":
        reponse = Reponse.objects.select_related("sujet").get(id=reponse_id)

        if request.user != reponse.sujet.auteur:
            messages.error(request, "❌ Seul l'auteur du sujet peut accepter une réponse.")
            return redirect("forum_detail", sujet_id=reponse.sujet.id)

        Reponse.objects.filter(sujet=reponse.sujet).update(acceptee=False)
        reponse.acceptee = True
        reponse.save()
        reponse.sujet.resolu = True
        reponse.sujet.save()
        attribuer_badges(reponse.auteur)
        ajouter_xp(reponse.auteur, "reponse_acceptee")

        notifications.creer_notification(
            reponse.auteur,
            "✅ Réponse acceptée",
            f'Ta réponse sur "{reponse.sujet.titre}" a été acceptée comme solution.',
            f"/forum/{reponse.sujet.id}/",
        )
        messages.success(request, "✅ Réponse marquée comme solution !")
        return redirect("forum_detail", sujet_id=reponse.sujet.id)

    return redirect("forum_liste")


# ================================================
# Espace Recrutement / Portfolio
# ================================================
def espace_recrutement(request):
    from django.contrib.auth.models import User
    from django.db.models import Count, Q

    from .models import BadgeForum, ProjetEtudiant
    from .models import Formation

    etudiants_qs = (
        User.objects.annotate(
            nb_formations=Count(
                "progressions__lecon__module__formation",
                filter=Q(progressions__terminee=True),
                distinct=True,
            ),
            nb_quiz=Count("resultats_quiz", distinct=True),
            nb_projets=Count("projets", distinct=True),
            nb_badges=Count("badges_forum", distinct=True),
        )
        .filter(Q(nb_formations__gt=0) | Q(nb_projets__gt=0))
        .order_by("-nb_badges", "-nb_formations")[:20]
    )

    etudiants_data = []
    for user in etudiants_qs:
        formations_completees = []
        for formation in Formation.objects.filter(actif=True):
            if formation.progression_pour(user) == 100:
                formations_completees.append(formation)

        projets = ProjetEtudiant.objects.filter(auteur=user).order_by("-date_creation")[:3]
        badges = BadgeForum.objects.filter(utilisateur=user)

        etudiants_data.append(
            {
                "user": user,
                "certifications": formations_completees,
                "badges": badges,
                "projets": projets,
                "nb_formations": user.nb_formations,
                "nb_quiz": user.nb_quiz,
                "nb_projets": user.nb_projets,
                "nb_badges": user.nb_badges,
            }
        )

    return render(
        request,
        "academie/recrutement.html",
        {
            "etudiants_data": etudiants_data,
        },
    )


@login_required(login_url="/connexion/")
def mon_portfolio(request):
    if request.method == "POST":
        titre = request.POST.get("titre", "").strip()
        description = request.POST.get("description", "").strip()
        technologies = request.POST.get("technologies", "").strip()
        lien = request.POST.get("lien", "").strip()
        image = request.FILES.get("image")
        formation_liee_id = request.POST.get("formation_liee") or None

        if titre and description:
            if image:
                kind = filetype.guess(image)
                if kind is None or kind.mime not in ["image/jpeg", "image/png", "image/gif"]:
                    messages.error(request, "❌ Format d'image non autorisé. Utilisez JPEG, PNG ou GIF.")
                    return redirect("mon_portfolio")

            ProjetEtudiant.objects.create(
                auteur=request.user,
                titre=titre,
                description=description,
                technologies=technologies,
                lien=lien if lien else None,
                image=image,
                formation_liee_id=formation_liee_id,
            )

            messages.success(request, "✅ Projet ajouté avec succès !")
            return redirect("mon_portfolio")
        else:
            messages.error(request, "❌ Titre et description sont obligatoires.")

    projets = ProjetEtudiant.objects.filter(auteur=request.user)
    formations_disponibles = Formation.objects.filter(actif=True)

    return render(
        request,
        "academie/portfolio.html",
        {
            "projets": projets,
            "formations_disponibles": formations_disponibles,
        },
    )


def verifier_certificat(request, numero):
    from .models import Certificat

    certificat = None
    try:
        certificat = Certificat.objects.select_related("utilisateur", "formation").get(
            numero=numero
        )
    except Exception:
        pass

    return render(request, "academie/verifier_certificat.html", {"certificat": certificat})


@login_required(login_url="/connexion/")
def notifications_liste(request):
    from .models import Notification

    notifs = Notification.objects.filter(utilisateur=request.user).order_by("-date_creation")[:30]
    ids_non_lues = [n.id for n in notifs if not n.lue]
    if ids_non_lues:
        Notification.objects.filter(id__in=ids_non_lues).update(lue=True)
    return render(request, "academie/notifications.html", {"notifications": notifs})


def classement(request):
    from .models import ProfilUtilisateur

    profils = (
        ProfilUtilisateur.objects.select_related("utilisateur")
        .filter(xp__gt=0)
        .order_by("-xp", "-streak")[:50]
    )

    return render(
        request,
        "academie/classement.html",
        {
            "profils": profils,
        },
    )


def set_lang_fr(request):
    translation.activate("fr")
    response = redirect(request.META.get("HTTP_REFERER", "/"))
    response.set_cookie(settings.LANGUAGE_COOKIE_NAME, "fr")
    return response


def set_lang_ht(request):
    translation.activate("ht")
    response = redirect(request.META.get("HTTP_REFERER", "/"))
    response.set_cookie(settings.LANGUAGE_COOKIE_NAME, "ht")
    return response


# ================================================
# Page Ressources
# ================================================
def ressources(request):
    categorie = request.GET.get("categorie", "")

    articles = Article.objects.filter(publie=True)
    if hasattr(request, "academie_courante") and request.academie_courante:
        articles = articles.filter(Q(academie=request.academie_courante) | Q(academie__isnull=True))
    if categorie:
        articles = articles.filter(categorie=categorie)

    articles_vedette = Article.objects.filter(publie=True, en_vedette=True)[:3]
    outils = OutilRecommande.objects.all()
    temoignages = Temoignage.objects.filter(approuve=True)

    return render(
        request,
        "academie/ressources.html",
        {
            "articles": articles,
            "articles_vedette": articles_vedette,
            "outils": outils,
            "temoignages": temoignages,
            "categorie_active": categorie,
            "categories": Article.CATEGORIES,
            "categories_outils": OutilRecommande.CATEGORIES,
        },
    )


def detail_article(request, slug):
    article = Article.objects.get(slug=slug, publie=True)

    articles_lies = Article.objects.filter(publie=True, categorie=article.categorie).exclude(
        id=article.id
    )[:3]

    return render(
        request,
        "academie/detail_article.html",
        {
            "article": article,
            "articles_lies": articles_lies,
        },
    )


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


# ================================================
# API — Assistant Back Office
# ================================================
@extend_schema(
    tags=["Back Office"],
    description="Assistant IA pour les administrateurs – réponse en HTML",
    request=inline_serializer(
        name="AssistantBackOfficeRequest", fields={"question": serializers.CharField()}
    ),
    responses={
        200: inline_serializer(
            name="AssistantBackOfficeResponse", fields={"reponse": serializers.CharField()}
        )
    },
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
@login_required
@role_required(
    "formateur",
    "resp_academique",
    "marketing",
    "support",
    "finance",
    "direction",
    "admin",
    "super_admin",
)
def api_assistant_backoffice(request):
    question = request.data.get("question", "").strip()
    if not question:
        return Response({"erreur": "Question vide"}, status=400)

    contexte = (
        f"Rôle: {request.user.profil.get_role_display()}, Utilisateur: {request.user.username}"
    )

    reponse_brute = assistant_backoffice_ia(question, contexte)

    try:
        reponse_html = markdown_lib.markdown(reponse_brute)
    except Exception:
        reponse_html = reponse_brute

    return Response({"reponse": reponse_html})


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


# Sitemap et robots
def sitemap_xml(request):
    articles = Article.objects.filter(publie=True)
    formations = Formation.objects.filter(actif=True, slug__isnull=False)
    return render(request, 'academie/sitemap.xml', {
        'articles': articles,
        'formations': formations,
    }, content_type='application/xml')


def robots_txt(request):
    contenu = "User-agent: *\nAllow: /\nSitemap: " + request.build_absolute_uri("/sitemap.xml")
    return HttpResponse(contenu, content_type="text/plain")


# ================================================
# Fonction utilitaire de promotion (conservée pour detail_formation)
# ================================================
def _prix_avec_promotion(formation):
    prix_original = Decimal(str(formation.prix))
    for promo in Promotion.objects.filter(actif=True):
        if promo.s_applique_a(formation):
            reduction = prix_original * (Decimal(promo.pourcentage_reduction) / 100)
            return prix_original - reduction, promo
    return prix_original, None


# ================================================
# Dashboard Business
# ================================================
@login_required
@role_required("finance", "direction", "admin", "super_admin")
def vue_dashboard_business(request):
    import json
    from datetime import timedelta

    total_inscriptions = Inscription.objects.count()
    inscriptions_non_traitees = Inscription.objects.filter(traite=False).count()

    ca_total = Order.objects.filter(statut="paye").aggregate(total=Sum("total"))["total"] or 0

    labels_jours, valeurs_jours = [], []
    for i in range(29, -1, -1):
        jour = timezone.now().date() - timedelta(days=i)
        montant_jour = (
            Order.objects.filter(statut="paye", date_paiement__date=jour).aggregate(
                total=Sum("total")
            )["total"]
            or 0
        )
        labels_jours.append(jour.strftime("%d/%m"))
        valeurs_jours.append(float(montant_jour))

    formations_populaires = Formation.objects.annotate(
        nb_ventes=Count("orderitem", filter=Q(orderitem__commande__statut="paye"))
    ).order_by("-nb_ventes")[:8]

    repartition_moyens = (
        Transaction.objects.filter(statut="reussie")
        .values("moyen_paiement__nom_affiche")
        .annotate(total=Count("id"))
    )

    coupons_utilises = Coupon.objects.filter(utilisations_actuelles__gt=0).count()
    remboursements_total = (
        Refund.objects.filter(statut="approuve").aggregate(total=Sum("montant"))["total"] or 0
    )

    return render(
        request,
        "admin/dashboard_business.html",
        {
            "title": "💼 Dashboard Business",
            "site_header": admin.site.site_header,
            "ca_total": ca_total,
            "total_inscriptions": total_inscriptions,
            "inscriptions_non_traitees": inscriptions_non_traitees,
            "formations_populaires": formations_populaires,
            "coupons_utilises": coupons_utilises,
            "remboursements_total": remboursements_total,
            "chart_labels_json": json.dumps(labels_jours),
            "chart_valeurs_json": json.dumps(valeurs_jours),
            "chart_moyens_labels": json.dumps(
                [m["moyen_paiement__nom_affiche"] or "N/A" for m in repartition_moyens]
            ),
            "chart_moyens_valeurs": json.dumps([m["total"] for m in repartition_moyens]),
        },
    )


# ================================================
# Dashboard Enseignant
# ================================================
@login_required
@role_required("formateur", "resp_academique", "admin", "super_admin")
def dashboard_enseignant(request):
    try:
        enseignant = request.user.profil.enseignant
    except (AttributeError, Enseignant.DoesNotExist):
        messages.error(request, "❌ Aucun profil enseignant associé à ce compte.")
        return redirect("dashboard")

    formations = enseignant.formations_attribuees.all()

    return render(
        request,
        "academie/dashboard_enseignant.html",
        {
            "enseignant": enseignant,
            "formations": formations,
            "revenus": enseignant.revenus_generes(),
            "remuneration": enseignant.part_remuneration(),
            "nb_etudiants": enseignant.nb_etudiants_formes(),
            "note_moyenne": enseignant.note_moyenne_temoignages(),
        },
    )


# ================================================
# Page de dépassement de limite (rate limiting)
# ================================================
def vue_limite_depassee(request, exception=None):
    return render(request, 'academie/limite_depassee.html', status=429)