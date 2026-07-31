# ================================================
# VIEWS_MODULES/CONTENT_VIEWS.PY — Ressources, Portfolio, Notifications, Classement
# ================================================

import filetype
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.shortcuts import redirect, render

from ..models import (
    Article,
    BadgeForum,
    Certificat,
    Formation,
    Notification,
    OutilRecommande,
    ProfilUtilisateur,
    ProjetEtudiant,
    Temoignage,
    CompetenceValidee,          # <-- déjà présent
)
from academie.models import Competence  # si besoin (déjà accessible via formation.competences)


# ================================================
# Ressources
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


# ================================================
# Espace Recrutement / Portfolio
# ================================================

def espace_recrutement(request):
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

            projet = ProjetEtudiant.objects.create(
                auteur=request.user,
                titre=titre,
                description=description,
                technologies=technologies,
                lien=lien if lien else None,
                image=image,
                formation_liee_id=formation_liee_id,
            )

            # --- Auto-remplissage des compétences liées à la formation ---
            competences_validees = []
            if formation_liee_id:
                try:
                    formation = Formation.objects.get(id=formation_liee_id)
                    competences_formation = formation.competences.all()
                    if competences_formation.exists():
                        # Associer les compétences au projet
                        projet.competences_demontrees.set(competences_formation)
                        # Valider chaque compétence avec source 'projet'
                        for competence in competences_formation:
                            cv, created = CompetenceValidee.objects.get_or_create(
                                utilisateur=request.user,
                                competence=competence,
                                source_type='projet',
                                projet_origine=projet,
                                defaults={
                                    'niveau': 'acquis',
                                    'formation_origine': formation,
                                }
                            )
                            if created:
                                competences_validees.append(cv)
                except Formation.DoesNotExist:
                    pass

            if competences_validees:
                noms = ", ".join(cv.competence.nom for cv in competences_validees)
                messages.success(request, f"✅ Projet ajouté avec succès ! Compétences validées : {noms}.")
            else:
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


# ================================================
# Certificat et notifications
# ================================================

def verifier_certificat_public(request, numero_certificat):
    """Vérification publique d'un certificat — accessible sans connexion."""
    certificat = Certificat.objects.select_related('utilisateur', 'formation').filter(
        numero=numero_certificat
    ).first()

    if not certificat:
        return render(request, 'academie/verifier_certificat.html', {
            'valide': False,
            'message': "Ce certificat n'existe pas ou le numéro est incorrect.",
        })

    return render(request, 'academie/verifier_certificat.html', {
        'valide': True,
        'certificat': certificat,
        'nom_affiche': certificat.utilisateur.get_full_name() or certificat.utilisateur.username,
        'formation_nom': certificat.formation.nom if certificat.formation else "Formation supprimée",
        'date_obtention': certificat.date_emission,
    })


@login_required(login_url="/connexion/")
def notifications_liste(request):
    notifs = Notification.objects.filter(utilisateur=request.user).order_by("-date_creation")[:30]
    ids_non_lues = [n.id for n in notifs if not n.lue]
    if ids_non_lues:
        Notification.objects.filter(id__in=ids_non_lues).update(lue=True)
    return render(request, "academie/notifications.html", {"notifications": notifs})


# ================================================
# Profil de compétences
# ================================================

@login_required(login_url='/connexion/')
def mon_profil_competences(request):
    """Carte de compétences de l'étudiant — le cœur visible de la démonstration."""
    competences_validees = CompetenceValidee.objects.filter(
        utilisateur=request.user
    ).select_related('competence', 'examen_origine', 'formation_origine').order_by('-date_validation')

    par_categorie = {}
    for cv in competences_validees:
        cat = cv.competence.get_categorie_display()
        if cat not in par_categorie:
            par_categorie[cat] = []
        par_categorie[cat].append(cv)

    return render(request, 'academie/profil_competences.html', {
        'competences_par_categorie': par_categorie,
        'total_competences': competences_validees.values('competence').distinct().count(),
    })


def classement(request):
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


# ================================================
# VIEWS.PY — Portfolio public partageable (/portfolio/username/)
# ================================================

def portfolio_public(request, username):
    """Page portfolio publique — consultable par recruteurs sans connexion."""
    utilisateur = User.objects.get(username=username)
    projets = ProjetEtudiant.objects.filter(auteur=utilisateur).prefetch_related('competences_demontrees')
    competences_validees = CompetenceValidee.objects.filter(utilisateur=utilisateur).select_related('competence')
    certificats = Certificat.objects.filter(utilisateur=utilisateur).select_related('formation')

    return render(request, 'academie/portfolio_public.html', {
        'profil_utilisateur': utilisateur,
        'projets': projets,
        'nb_competences': competences_validees.values('competence').distinct().count(),
        'competences_validees': competences_validees[:12],
        'certificats': certificats,
    })