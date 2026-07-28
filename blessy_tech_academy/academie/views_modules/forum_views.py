# ================================================
# VIEWS_MODULES/FORUM_VIEWS.PY — Vues Forum
# ================================================

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db.models import Count, Q, Subquery, OuterRef, IntegerField
from django.shortcuts import render, redirect, get_object_or_404
from django_ratelimit.decorators import ratelimit

from forum.models import Sujet, Reponse, Reaction, BadgeForum
from academie.models import Formation, LogAudit
from academie.validators import detecter_spam_probable
from academie.xp_utils import ajouter_xp
from academie.services.ia_service import attribuer_badges
from academie import notifications


# ================================================
# Vues du forum
# ================================================

def forum_liste(request):
    """Page principale du forum — liste tous les sujets."""
    categorie = request.GET.get("categorie", "")
    formation_id = request.GET.get("formation", "")
    recherche = request.GET.get("q", "")

    sujet_ct = ContentType.objects.get_for_model(Sujet)
    reactions_subquery = Reaction.objects.filter(
        content_type=sujet_ct,
        object_id=OuterRef('id')
    ).values('object_id').annotate(cnt=Count('id')).values('cnt')

    sujets = Sujet.objects.select_related("auteur", "formation").annotate(
        nb_reponses_calc=Count("reponses", distinct=True),
        nb_likes_calc=Subquery(reactions_subquery, output_field=IntegerField()),
    )

    if categorie:
        sujets = sujets.filter(categorie=categorie)

    if formation_id:
        sujets = sujets.filter(formation_id=formation_id)

    if recherche:
        sujets = sujets.filter(Q(titre__icontains=recherche) | Q(contenu__icontains=recherche))

    paginator = Paginator(sujets, 10)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)

    formations = Formation.objects.filter(actif=True)

    return render(
        request,
        "academie/forum/liste.html",
        {
            "sujets": page_obj,
            "page_obj": page_obj,
            "formations": formations,
            "categorie_active": categorie,
            "formation_active": formation_id,
            "categories": Sujet.CATEGORIES,
            "recherche": recherche,
        },
    )


def forum_detail(request, sujet_id):
    """Page de détail d'un sujet avec ses réponses."""
    sujet = (
        Sujet.objects.select_related("auteur", "formation")
        .prefetch_related("reponses__auteur", "reponses__reactions", "reactions")
        .get(id=sujet_id)
    )

    sujet.vues += 1
    sujet.save(update_fields=["vues"])

    likes_sujets = set()
    likes_reponses = set()

    if request.user.is_authenticated:
        likes_sujets = set(
            Reaction.objects.filter(utilisateur=request.user, sujet=sujet).values_list(
                "sujet_id", flat=True
            )
        )
        likes_reponses = set(
            Reaction.objects.filter(utilisateur=request.user, reponse__sujet=sujet).values_list(
                "reponse_id", flat=True
            )
        )

    if request.method == "POST" and request.user.is_authenticated:
        contenu = request.POST.get("contenu", "").strip()
        if contenu:
            Reponse.objects.create(
                sujet=sujet,
                contenu=contenu,
                auteur=request.user,
            )
            ajouter_xp(request.user, "reponse_forum")
            messages.success(request, "✅ Réponse publiée !")
            return redirect("forum_detail", sujet_id=sujet_id)

    return render(
        request,
        "academie/forum/detail.html",
        {
            "sujet": sujet,
            "likes_sujets": likes_sujets,
            "likes_reponses": likes_reponses,
        },
    )


@ratelimit(key='user', rate='10/h', method='POST', block=True)
@login_required(login_url="/connexion/")
def forum_creer(request):
    """Créer un nouveau sujet."""
    if request.method == "POST":
        titre = request.POST.get("titre", "").strip()
        contenu = request.POST.get("contenu", "").strip()
        categorie = request.POST.get("categorie", "general")
        formation_id = request.POST.get("formation", "")

        if not titre or not contenu:
            messages.error(request, "❌ Titre et contenu sont obligatoires.")
            formations = Formation.objects.filter(actif=True)
            return render(
                request,
                "academie/forum/creer.html",
                {
                    "form": SujetForm(),  # Note : SujetForm doit être importé
                    "formations": formations,
                    "categories": Sujet.CATEGORIES,
                },
            )

        if detecter_spam_probable(contenu):
            messages.error(request, "❌ Ton message a été détecté comme potentiellement indésirable. Contacte le support si c'est une erreur.")
            LogAudit.objects.create(
                utilisateur=request.user,
                action='suppression',
                description=f"Sujet forum bloqué (spam suspecté) : {titre[:50]}",
            )
            return redirect('forum_creer')

        sujet = Sujet.objects.create(
            titre=titre,
            contenu=contenu,
            categorie=categorie,
            auteur=request.user,
            formation_id=formation_id if formation_id else None,
        )

        attribuer_badges(request.user)
        notifications.creer_notification(
            request.user,
            "📝 Sujet créé",
            f'Ton sujet "{sujet.titre}" a été publié avec succès.',
            f"/forum/{sujet.id}/",
        )
        messages.success(request, "✅ Sujet créé avec succès !")
        return redirect("forum_detail", sujet_id=sujet.id)

    formations = Formation.objects.filter(actif=True)
    # SujetForm est utilisé, mais il n'est pas défini ici; il vient de academie.forms
    from academie.forms import SujetForm
    return render(
        request,
        "academie/forum/creer.html",
        {
            "form": SujetForm(),
            "formations": formations,
            "categories": Sujet.CATEGORIES,
        },
    )


def forum_membres(request):
    """Classement des membres du forum."""
    membres = (
        User.objects.annotate(
            nb_sujets=Count("sujets_forum", distinct=True),
            nb_reponses=Count("reponses_forum", distinct=True),
            nb_solutions=Count(
                "reponses_forum", filter=Q(reponses_forum__acceptee=True), distinct=True
            ),
            nb_likes=Count("reactions_forum", distinct=True),
        )
        .filter(Q(nb_sujets__gt=0) | Q(nb_reponses__gt=0))
        .order_by("-nb_reponses", "-nb_solutions", "-nb_sujets")[:20]
    )

    return render(
        request,
        "academie/forum/membres.html",
        {
            "membres": membres,
        },
    )