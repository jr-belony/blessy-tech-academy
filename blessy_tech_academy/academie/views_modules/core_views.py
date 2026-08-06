# ================================================
# VIEWS_MODULES/CORE_VIEWS.PY — Vues transverses
# ================================================

import json
import logging
import hashlib
import base64
from io import BytesIO

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from django.db import connection
from django.core.cache import cache
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from django.views.decorators.cache import cache_page
from django_ratelimit.decorators import ratelimit
from django.utils import timezone, translation
from django.conf import settings
from django.template.loader import render_to_string
from django.shortcuts import get_object_or_404
# [AJOUT PLAYWRIGHT] 
from playwright.sync_api import sync_playwright 

from academie.models import (
    Ecole, Formation, Article, Parcours, ProgressionLecon,
    HistoriqueConversationIA, ProjetEtudiant, PushSubscription,
    Sujet, AccesFormationDebloque, BadgeForum, Order, Parrainage,
    Certificat, LogAudit, ConnexionUtilisateur, TentativeExamen,
    NoteLecon, StreakEtudiant, ResultatQuiz,
)
from academie.forms import ConnexionForm, InscriptionCompteForm
from academie import notifications
from academie.services.ia_service import (
    attribuer_badges,
    calculer_stats_etudiant,
    _circuit_ouvert,
)
from academie.decorators import exiger_acces_formation

logger = logging.getLogger('academie')

# ================================================
# Pages principales
# ================================================

@cache_page(60 * 10)  # 10 minutes
def accueil(request):
    """Page d'accueil avec statistiques dynamiques."""
    formations = Formation.objects.filter(actif=True)[:4]
    formations_gratuites = Formation.objects.filter(actif=True, gratuit=True)
    ecoles = Ecole.objects.all()
    parcours_list = Parcours.objects.filter(actif=True)
    nb_etudiants = User.objects.filter(is_active=True).count()
    nb_formations = Formation.objects.filter(actif=True).count()
    nb_sujets_forum = Sujet.objects.count()
    stats = [
        {"valeur": nb_etudiants, "suffixe": "+", "label": "Étudiants"},
        {"valeur": nb_formations, "suffixe": "", "label": "Formations"},
        {"valeur": nb_sujets_forum, "suffixe": "", "label": "Sujets forum"},
    ]
    articles_recents = Article.objects.filter(publie=True).order_by("-date_publication")[:3]

    return render(
        request,
        "academie/accueil.html",
        {
            "formations": formations,
            "formations_gratuites": formations_gratuites,
            "ecoles": ecoles,
            "parcours_list": parcours_list,
            "stats": stats,
            "articles_recents": articles_recents,
            "nb_etudiants": nb_etudiants,
            "nb_formations": nb_formations,
            "nb_sujets_forum": nb_sujets_forum,
        },
    )


@ratelimit(key='ip', rate='3/m', method='POST', block=True)
def contact(request):
    from django import forms
    class ContactForm(forms.Form):
        prenom = forms.CharField(max_length=100, label="Prénom")
        nom = forms.CharField(max_length=100, label="Nom")
        email = forms.EmailField(label="Email")
        sujet = forms.CharField(max_length=200, label="Sujet")
        message = forms.CharField(widget=forms.Textarea, label="Message")

    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            messages.success(request, "✅ Message envoyé avec succès !")
            return redirect("contact")
    else:
        form = ContactForm()
    return render(request, "academie/contact.html", {"form": form})


def apropos(request):
    return render(request, "academie/apropos.html")


@ratelimit(key="ip", rate="5/m", block=True)
def connexion(request):
    """Connexion à un compte existant."""
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = ConnexionForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            # Enregistrement du streak
            streak, _ = StreakEtudiant.objects.get_or_create(utilisateur=user)
            streak.enregistrer_activite_jour()
            messages.success(request, f"✅ Bienvenue {user.first_name or user.username} !")
            return redirect("dashboard")
        else:
            messages.error(
                request,
                "❌ Identifiants incorrects. Vérifie ton nom d'utilisateur et ton mot de passe.",
            )
    else:
        form = ConnexionForm(request)

    return render(request, "academie/connexion.html", {"form": form})


def deconnexion(request):
    """Déconnexion."""
    logout(request)
    messages.success(request, "👋 Tu as été déconnecté avec succès.")
    return redirect("accueil")


@ratelimit(key='ip', rate='3/h', method='POST', block=True)
def inscription_compte(request):
    """Créer un nouveau compte étudiant."""
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = InscriptionCompteForm(request.POST)
        if form.is_valid():
            user = form.save()

            # ================================================
            # Parrainage — association automatique si ?ref= présent
            # ================================================
            code_ref = request.GET.get('ref') or request.POST.get('ref')
            if code_ref:
                try:
                    parrainage = Parrainage.objects.get(
                        code_parrainage=code_ref, statut='invite'
                    )
                    parrainage.filleul_utilisateur = user
                    parrainage.statut = 'inscrit'
                    parrainage.date_conversion = timezone.now()
                    parrainage.save()
                except Parrainage.DoesNotExist:
                    pass  # code invalide, on ignore

            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            # Enregistrement du streak
            streak, _ = StreakEtudiant.objects.get_or_create(utilisateur=user)
            streak.enregistrer_activite_jour()
            messages.success(
                request,
                f"🎉 Bienvenue {user.first_name} ! Ton compte a été créé avec succès.",
            )
            return redirect("dashboard")
        else:
            messages.error(
                request,
                "❌ Erreur lors de la création du compte. Vérifie les informations saisies.",
            )
    else:
        form = InscriptionCompteForm()

    return render(request, "academie/inscription_compte.html", {"form": form})

# ================================================
# Tableau de bord
# ================================================

@login_required(login_url="/connexion/")
def dashboard(request):
    """Tableau de bord étudiant — version optimisée, sans calcul inutile."""
    user = request.user

    # --- Formations avec progression (optimisé : 1 requête) ---
    formation_ids_actives = ProgressionLecon.objects.filter(
        utilisateur=user
    ).values_list('lecon__module__formation_id', flat=True).distinct()

    formations_avec_progression = []
    for formation in Formation.objects.filter(id__in=formation_ids_actives).select_related('ecole'):
        pourcentage = formation.progression_pour(user)   # optimisé + cache
        if pourcentage > 0:
            formations_avec_progression.append({
                'formation': formation,
                'pourcentage': pourcentage
            })
    # Trier par progression décroissante (comme avant)
    formations_avec_progression.sort(key=lambda x: x['pourcentage'], reverse=True)

    # --- Badges ---
    tous_badges = BadgeForum.objects.filter(utilisateur=user).order_by('-date_obtention')
    nouveaux_badges = attribuer_badges(user)
    if nouveaux_badges:
        messages.success(request, f"🎉 Nouveau(x) badge(s) : {', '.join(nouveaux_badges)} !")
    for badge_type in nouveaux_badges:
        notifications.notifier_badge(user, badge_type)

    # --- Streak ---
    streak, _ = StreakEtudiant.objects.get_or_create(utilisateur=user)

    # --- Résultats de quiz récents ---
    resultats_recents = ResultatQuiz.objects.filter(utilisateur=user).select_related('quiz__formation')[:5]

    # --- Historique de connexions ---
    connexions = ConnexionUtilisateur.objects.filter(utilisateur=user).order_by("-date_connexion")[:5]

    # --- Examens passés ---
    examens_passes = (
        TentativeExamen.objects.filter(utilisateur=user)
        .select_related("examen")
        .order_by("-date_passage")[:10]
    )

    return render(
        request,
        "academie/dashboard.html",
        {
            "user": user,
            "formations_actives": formations_avec_progression,   # compatible avec l'ancien template
            "badges": tous_badges,
            "formations_avec_progression": formations_avec_progression,  # pour éviter de casser d'éventuelles références
            "resultats_recents": resultats_recents,
            "connexions": connexions,
            "examens_passes": examens_passes,
            "streak": streak,
        },
    )


# ================================================
# Recherche
# ================================================

# ================================================
# VIEWS.PY — Recherche avancée (filtres multi-critères)
# Compatible avec le template recherche.html existant
# ================================================

def recherche(request):
    """Recherche globale enrichie — full-text + filtres école/niveau/gratuit."""
    from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
    from django.db.models import Q
    from ..models import Formation, Article, Sujet, Ecole

    terme = request.GET.get('q', '').strip()
    ecole_id = request.GET.get('ecole', '')
    niveau = request.GET.get('niveau', '')
    gratuit_seulement = request.GET.get('gratuit') == '1'

    resultats_formations = Formation.objects.filter(actif=True).select_related('ecole')

    if terme:
        query = SearchQuery(terme, config='french')
        resultats_formations = resultats_formations.annotate(
            rang=SearchRank(
                SearchVector('nom', weight='A') + SearchVector('description', weight='B'),
                query
            )
        ).filter(rang__gt=0.01).order_by('-rang')

        if not resultats_formations:
            resultats_formations = Formation.objects.filter(
                Q(actif=True, nom__icontains=terme) |
                Q(actif=True, description__icontains=terme)
            )

    if ecole_id:
        resultats_formations = resultats_formations.filter(ecole_id=ecole_id)
    if niveau:
        resultats_formations = resultats_formations.filter(niveau=niveau)
    if gratuit_seulement:
        resultats_formations = resultats_formations.filter(gratuit=True)

    # Limiter à 20 formations pour l'affichage
    resultats_formations = resultats_formations[:20]

    resultats_articles = (
        Article.objects.filter(publie=True, titre__icontains=terme)
        .select_related('auteur')[:10]
        if terme else []
    )

    resultats_forum = (
        Sujet.objects.filter(titre__icontains=terme)
        .select_related('auteur')[:10]
        if terme else []
    )

    return render(request, 'academie/recherche.html', {
        'terme': terme,
        'resultats_formations': resultats_formations,
        'resultats_articles': resultats_articles,
        'resultats_forum': resultats_forum,
        'ecoles': Ecole.objects.all(),
        'ecole_filtre': ecole_id,
        'niveau_filtre': niveau,
        'gratuit_filtre': gratuit_seulement,
        'nb_total': len(resultats_formations) + len(resultats_articles) + len(resultats_forum),
    })


def recherche_formations(request):
    """Recherche de formations par mot-clé."""
    terme = request.GET.get("q", "")

    if terme:
        resultats = Formation.objects.filter(
            Q(nom__icontains=terme)
            | Q(description__icontains=terme)
            | Q(debouches__icontains=terme),
            actif=True,
        ).select_related("ecole")
    else:
        resultats = Formation.objects.none()

    return render(
        request,
        "academie/recherche.html",
        {
            "resultats": resultats,
            "terme": terme,
        },
    )


# ================================================
# Pages utilitaires
# ================================================

def health_check(request):
    """Endpoint de santé — utilisé par les services de monitoring."""
    statut = {'statut': 'ok', 'verifications': {}}
    code_http = 200

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        statut['verifications']['database'] = 'ok'
    except Exception as e:
        statut['verifications']['database'] = f'erreur: {str(e)}'
        statut['statut'] = 'degrade'
        code_http = 503

    try:
        cache.set('health_check_test', 'ok', 10)
        statut['verifications']['cache'] = 'ok' if cache.get('health_check_test') == 'ok' else 'erreur'
    except Exception:
        statut['verifications']['cache'] = 'indisponible (fallback local actif)'

    statut['verifications']['ia_gemini'] = 'circuit_ouvert' if _circuit_ouvert() else 'ok'

    return JsonResponse(statut, status=code_http)


def page_offline(request):
    return render(request, "academie/offline.html")


# ================================================
# Données personnelles (RGPD-like)
# ================================================

@login_required(login_url='/connexion/')
def exporter_mes_donnees(request):
    """Génère un export JSON complet des données de l'utilisateur connecté."""
    user = request.user

    donnees = {
        'profil': {
            'username': user.username, 'email': user.email,
            'prenom': user.first_name, 'nom': user.last_name,
            'date_inscription': user.date_joined.isoformat(),
        },
        'formations_suivies': list(
            AccesFormationDebloque.objects.filter(utilisateur=user).values('nom_formation_snapshot', 'date_deblocage')
        ),
        'progressions': list(
            ProgressionLecon.objects.filter(utilisateur=user).values('lecon__titre', 'terminee', 'date_completion')
        ),
        'commandes': list(
            Order.objects.filter(utilisateur=user).values('reference', 'total', 'statut', 'date_creation')
        ),
        'badges': list(BadgeForum.objects.filter(utilisateur=user).values('type_badge', 'date_obtention')),
        'projets_portfolio': list(ProjetEtudiant.objects.filter(auteur=user).values('titre', 'description', 'date_creation')),
        'conversations_ia': list(
            HistoriqueConversationIA.objects.filter(utilisateur=user).values('role', 'contenu', 'date_creation')
        ),
    }

    reponse = HttpResponse(
        json.dumps(donnees, indent=2, default=str, ensure_ascii=False),
        content_type='application/json'
    )
    reponse['Content-Disposition'] = f'attachment; filename="mes_donnees_bta_{user.username}.json"'
    return reponse


@login_required(login_url='/connexion/')
def supprimer_mon_compte(request):
    """Anonymise le compte utilisateur — conserve les données comptables légalement requises."""
    if request.method == 'POST':
        confirmation = request.POST.get('confirmation', '')
        if confirmation != 'SUPPRIMER':
            messages.error(request, "❌ Confirmation incorrecte.")
            return redirect('dashboard')

        user = request.user
        user_id = user.id

        user.username = f"utilisateur_supprime_{user_id}"
        user.email = f"supprime_{user_id}@anonyme.local"
        user.first_name = "Utilisateur"
        user.last_name = "Supprimé"
        user.is_active = False
        user.set_unusable_password()
        user.save()

        ProjetEtudiant.objects.filter(auteur=user).delete()
        HistoriqueConversationIA.objects.filter(utilisateur=user).delete()
        LogAudit.objects.create(
            utilisateur=None, action='suppression',
            description=f"Compte utilisateur #{user_id} anonymisé (demande RGPD)",
        )

        logout(request)
        messages.success(request, "✅ Ton compte a été supprimé et tes données anonymisées.")
        return redirect('accueil')

    return render(request, 'academie/confirmer_suppression_compte.html')


# ================================================
# Langues, Sitemap, Robots, Rate limit
# ================================================

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
# VIEWS.PY — Enrichissement sitemap_xml() avec toutes les formations
# Remplace la version existante (qui n'avait que les articles)
# ================================================

def sitemap_xml(request):
    articles = Article.objects.filter(publie=True)
    formations = Formation.objects.filter(actif=True).exclude(slug='')
    return render(request, 'academie/sitemap.xml', {
        'articles': articles,
        'formations': formations,
    }, content_type='application/xml')


def robots_txt(request):
    contenu = "User-agent: *\nAllow: /\nSitemap: " + request.build_absolute_uri("/sitemap.xml")
    return HttpResponse(contenu, content_type="text/plain")


def vue_limite_depassee(request, exception=None):
    return render(request, 'academie/limite_depassee.html', status=429)


# ================================================
# Téléchargement PDF d'un certificat (par formation_id) — utilisateur connecté
# ================================================

@login_required(login_url="/connexion/")
@exiger_acces_formation(lambda formation_id: Formation.objects.get(id=formation_id))
def telecharger_certificat(request, formation_id):
    """
    Télécharge le certificat PDF pour une formation terminée à 100%.
    URL : /formation/<int:formation_id>/certificat/
    """
    import base64
    from io import BytesIO
    import qrcode
    from django.template.loader import render_to_string
    from content.models import Certificat

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

    certificat, _ = Certificat.objects.get_or_create(
        utilisateur=request.user,
        formation=formation,
        defaults={}
    )

    # --- QR Code ---
    url_verification = request.build_absolute_uri(f"/certificat/{certificat.uuid}/")
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(url_verification)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    qr_code_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

    # Contexte pour le template
    contexte = {
        'logo_url': request.build_absolute_uri('/static/img/logo-bta.png'),
        'type_certificat': 'Certificat de Réussite',
        'partenaire_logo': '',
        'mention': '',
        'prenom': request.user.first_name,
        'nom': request.user.last_name,
        'username': request.user.username,          # <-- AJOUTÉ
        'formation_nom': formation.nom,
        'ecole_nom': formation.ecole.nom,
        'date_emission': certificat.date_emission,  # <-- Objet datetime (pour le filtre |date)
        'numero_certificat': certificat.numero,
        'uuid': str(certificat.uuid),
        'qr_code_data': qr_code_base64,
        'signataire_nom': 'Jean Raymond BELONY',
        'signataire_titre': 'PDG & Fondateur',
        'verification_text': 'Certificat vérifiable en ligne – blessytechacademy.com',
        'url_verification': request.build_absolute_uri(f'/certificat/{certificat.uuid}/'),
    }

    # Génération du HTML avec le modèle officiel
    html = render_to_string("academie/pdf/certificat_officiel.html", contexte, request=request)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_content(html, wait_until="networkidle")
            
            pdf_bytes = page.pdf(
                format="A4",
                landscape=True,
                print_background=True,
                margin={"top": "0mm", "bottom": "0mm", "left": "0mm", "right": "0mm"}
            )
            browser.close()

        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="certificat-{certificat.numero}.pdf"'
        return response
    except Exception as e:
        messages.error(request, f"❌ Erreur lors de la génération du certificat : {str(e)}")
        return redirect("detail_formation", formation_id=formation_id)


# ================================================
# Téléchargement PDF d'un certificat par UUID (public)
# ================================================

def telecharger_certificat_pdf(request, uuid):
    """
    Génère et télécharge un certificat au format PDF à partir de son UUID.
    URL : /certificat/<uuid:uuid>/telecharger/
    """
    import base64
    from io import BytesIO
    import qrcode
    from django.template.loader import render_to_string
    from content.models import Certificat

    certificat = get_object_or_404(Certificat, uuid=uuid)

    # --- QR Code ---
    url_verification = request.build_absolute_uri(f"/certificat/{certificat.uuid}/")
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(url_verification)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    qr_code_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

    # Contexte pour le template
    contexte = {
        'logo_url': request.build_absolute_uri('/static/img/logo-bta.png'),
        'type_certificat': 'Certificat de Réussite',
        'partenaire_logo': '',
        'mention': '',
        'prenom': certificat.utilisateur.first_name,
        'nom': certificat.utilisateur.last_name,
        'username': certificat.utilisateur.username,          # <-- AJOUTÉ
        'formation_nom': certificat.formation.nom,
        'ecole_nom': certificat.formation.ecole.nom,
        'date_emission': certificat.date_emission,            # <-- Objet datetime
        'numero_certificat': certificat.numero,
        'uuid': str(certificat.uuid),
        'qr_code_data': qr_code_base64,
        'signataire_nom': 'Jean Raymond BELONY',
        'signataire_titre': 'PDG & Fondateur',
        'verification_text': 'Certificat vérifiable en ligne – blessytechacademy.com',
        'url_verification': request.build_absolute_uri(f'/certificat/{certificat.uuid}/'),
    }

    # Génération du HTML avec le modèle officiel
    html = render_to_string("academie/pdf/certificat_officiel.html", contexte, request=request)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_content(html, wait_until="networkidle")
            
            pdf_bytes = page.pdf(
                format="A4",
                landscape=True,
                print_background=True,
                margin={"top": "0mm", "bottom": "0mm", "left": "0mm", "right": "0mm"}
            )
            browser.close()

        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="certificat-{certificat.numero}.pdf"'
        return response
    except Exception as e:
        return HttpResponse(f"Erreur lors de la génération du PDF : {str(e)}", status=500)



# ================================================
# VIEWS.PY — Hub Explorer — vue d'ensemble visuelle du catalogue complet
# ================================================

def hub_explorer(request):
    """Page hub — rend visible et navigable tout ce qui a été construit."""
    return render(request, 'academie/hub_explorer.html')