# ================================================
# VIEWS_MODULES/CONTENT_VIEWS.PY — Ressources, Portfolio, Notifications, Classement
# ================================================

import filetype
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

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
    CompetenceValidee,
    DemandeTemoignage,
    Evenement,
    Inscription,
)
from academie.models import Competence


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


def portfolio_public(request, username):
    """Page portfolio publique — consultable par recruteurs sans connexion."""
    utilisateur = get_object_or_404(User, username=username)
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
# Workflow Témoignage complet (jamais auto-publié)
# ================================================

@login_required(login_url='/connexion/')
def repondre_temoignage(request, demande_id):
    demande = get_object_or_404(DemandeTemoignage, id=demande_id, utilisateur=request.user)

    if request.method == 'POST':
        demande.reponse_texte = request.POST.get('reponse_texte', '')
        demande.note = request.POST.get('note') or None
        demande.consentement_publication = request.POST.get('consentement') == 'on'
        demande.statut = 'consentement_donne' if demande.consentement_publication else 'refusee'
        demande.date_reponse = timezone.now()
        demande.save()
        messages.success(request, "✅ Merci pour ton retour !")
        return redirect('dashboard')

    return render(request, 'academie/repondre_temoignage.html', {'demande': demande})


@staff_member_required
def valider_temoignages_en_attente(request):
    demandes = DemandeTemoignage.objects.filter(statut='consentement_donne').select_related('utilisateur', 'formation')

    if request.method == 'POST':
        demande_id = request.POST.get('demande_id')
        demande = get_object_or_404(DemandeTemoignage, id=demande_id)

        temoignage = Temoignage.objects.create(
            prenom_nom=demande.utilisateur.get_full_name() or demande.utilisateur.username,
            formation_suivie=demande.formation,
            texte=demande.reponse_texte,
            note=demande.note or 5,
            initiales=(demande.utilisateur.first_name[:1] + demande.utilisateur.last_name[:1]).upper() or demande.utilisateur.username[:2].upper(),
            approuve=True,
        )
        demande.statut = 'publiee'
        demande.temoignage_publie = temoignage
        demande.save()
        messages.success(request, "✅ Témoignage publié.")
        return redirect('valider_temoignages_en_attente')

    return render(request, 'admin/valider_temoignages.html', {'demandes': demandes})


# ================================================
# Page Preuve Sociale (résultats réels uniquement)
# ================================================

def resultats_et_preuves(request):
    """Page publique de preuve sociale — cœur de la stratégie PROOF→TRUST."""
    from ..models import Cohorte, Temoignage, Certificat, ProjetEtudiant, CompetenceValidee
    from django.contrib.auth.models import User

    cohortes_actives = Cohorte.objects.filter(actif=True).prefetch_related('formations', 'membres')
    temoignages_publies = Temoignage.objects.filter(approuve=True).select_related('formation_suivie').order_by('-date_creation')[:12]
    certificats_recents = Certificat.objects.filter(
        statut='valide'
    ).select_related('utilisateur', 'formation').order_by('-date_emission')[:8]   # ← corrigé

    projets_valides = ProjetEtudiant.objects.filter(
        valide_par_formateur__isnull=False
    ).select_related('auteur', 'formation_liee').order_by('-date_validation')[:9]

    total_certificats = Certificat.objects.filter(statut='valide').count()
    total_competences_validees = CompetenceValidee.objects.count()
    total_projets_realises = ProjetEtudiant.objects.count()
    total_etudiants_actifs = User.objects.filter(progressions__isnull=False).distinct().count()

    return render(request, 'academie/resultats_et_preuves.html', {
        'cohortes_actives': cohortes_actives,
        'temoignages': temoignages_publies,
        'certificats_recents': certificats_recents,
        'projets_valides': projets_valides,
        'total_certificats': total_certificats,
        'total_competences_validees': total_competences_validees,
        'total_projets_realises': total_projets_realises,
        'total_etudiants_actifs': total_etudiants_actifs,
    })


def partenariats(request):
    """Page vitrine partenaires — vide au départ, structure prête pour Phase 4."""
    from ..models import Partenaire
    partenaires = Partenaire.objects.filter(actif=True)
    return render(request, 'academie/partenariats.html', {'partenaires': partenaires})


def ambassadeurs(request):
    """Page publique présentant les ambassadeurs de la plateforme."""
    from ..models import Ambassadeur
    ambassadeurs = Ambassadeur.objects.filter(visible_publiquement=True).select_related('utilisateur')
    return render(request, 'academie/ambassadeurs.html', {'ambassadeurs': ambassadeurs})


def nos_ambassadeurs(request):
    """Met en avant les pilotes ayant CONSENTI à être visibles — preuve humaine forte."""
    from ..models import Ambassadeur
    ambassadeurs = Ambassadeur.objects.filter(visible_publiquement=True).select_related('utilisateur')
    return render(request, 'academie/nos_ambassadeurs.html', {'ambassadeurs': ambassadeurs})


def faq_confiance(request):
    """FAQ globale sur la confiance et la sécurité — rassure les visiteurs."""
    return render(request, 'academie/faq_confiance.html')


# ================================================
# Vues : Catalogue des Certifications
# ================================================

def certifications(request):
    """
    Catalogue public des certifications délivrées par BTA.
    Affiche toutes les formations qui délivrent un certificat,
    avec les infos : nom, prérequis, compétences validées, durée.
    """
    # Récupère toutes les formations actives qui délivrent un certificat
    formations_avec_certificat = Formation.objects.filter(
        actif=True,
        delivre_certificat=True
    ).select_related('ecole').prefetch_related(
        'modules',
        'competences',
        'learning_outcomes'
    ).order_by('ecole__nom', 'nom')

    # Comptage du nombre total de certifications
    total_certifications = formations_avec_certificat.count()

    # Compétences distinctes disponibles (pour facettage/filtrage éventuel)
    toutes_competences = Competence.objects.filter(
        formation__in=formations_avec_certificat
    ).distinct().order_by('nom')

    # Niveaux disponibles pour filtrage
    niveaux_disponibles = formations_avec_certificat.values_list(
        'niveau', flat=True
    ).distinct().order_by('niveau')

    # Mapping des niveaux pour affichage
    NIVEAUX_MAPPING = {
        'debutant': 'Débutant',
        'intermediaire': 'Intermédiaire',
        'avance': 'Avancé',
        'pro': 'Professionnel',
    }

    context = {
        'formations': formations_avec_certificat,
        'total_certifications': total_certifications,
        'toutes_competences': toutes_competences,
        'niveaux_disponibles': [
            {'value': niv, 'label': NIVEAUX_MAPPING.get(niv, niv.capitalize())}
            for niv in niveaux_disponibles
        ],
        'NIVEAUX_MAPPING': NIVEAUX_MAPPING,
    }

    return render(request, 'academie/certifications.html', context)


# ================================================
# VIEWS.PY — Galerie publique des portfolios apprenants
# ================================================

def galerie_portfolios(request):
    """Liste des apprenants ayant un portfolio public actif (au moins 1 projet)."""
    utilisateurs_avec_portfolio = User.objects.filter(
        projets__isnull=False
    ).distinct().annotate(nb_projets=Count('projets'))

    return render(request, 'academie/galerie_portfolios.html', {
        'apprenants': utilisateurs_avec_portfolio,
    })


# ================================================
# VIEWS.PY — Galerie publique des projets — validés en priorité
# ================================================

def galerie_projets(request):
    """Tous les projets publics, projets validés par formateur en premier."""
    projets = ProjetEtudiant.objects.select_related('auteur', 'formation_liee').order_by(
        '-valide_par_formateur', '-date_creation'
    )
    return render(request, 'academie/galerie_projets.html', {'projets': projets})


# ================================================
# VIEWS.PY — Page Témoignages dédiée
# ================================================

def temoignages_page(request):
    temoignages = Temoignage.objects.filter(approuve=True).select_related('formation_suivie').order_by('-en_vedette', '-date_creation')
    return render(request, 'academie/temoignages.html', {'temoignages': temoignages})


# ================================================
# VIEWS.PY — Page Événements (webinaires, hackathons)
# ================================================

def evenements(request):
    a_venir = Evenement.objects.filter(publie=True, date_debut__gte=timezone.now()).order_by('date_debut')
    passes = Evenement.objects.filter(publie=True, date_debut__lt=timezone.now()).order_by('-date_debut')[:6]
    return render(request, 'academie/evenements.html', {'a_venir': a_venir, 'passes': passes})


# ================================================
# VIEWS.PY — FAQ globale + Support (formulaire léger)
# ================================================

def faq_globale(request):
    return render(request, 'academie/faq_globale.html')


def support(request):
    """Page Support — réutilise le formulaire Inscription (CRM) avec source='support'."""
    if request.method == 'POST':
        Inscription.objects.create(
            prenom=request.POST.get('prenom', ''), nom=request.POST.get('nom', ''),
            email=request.POST.get('email', ''), message=request.POST.get('message', ''),
            sujet='Demande de support', source_lead='site',
        )
        messages.success(request, "✅ Ta demande a été envoyée. Notre équipe te répond sous 24h.")
        return redirect('support')
    return render(request, 'academie/support.html')