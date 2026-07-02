import json
import hashlib
import markdown as markdown_lib
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.db.models import Count
from django.db.models import Q, Count, Avg
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.template.loader import render_to_string
from django.utils import timezone
from datetime import timedelta
from django.db.models.functions import TruncMonth
from .models import (
    Formation, Inscription, Ecole, Quiz, Question, ResultatQuiz,
    Module, Lecon, ProgressionLecon, Parcours, Sujet, Reponse, Reaction, ProjetEtudiant, Certificat
)
from .forms import InscriptionForm, InscriptionCompteForm, ConnexionForm, SujetForm, ReponseForm 
from . import notifications
from .xp_utils import ajouter_xp
from .ia import (
    blessy_ai_repondre,
    recommander_formations,
    generer_contenu_formation,
    generer_quiz,
    generer_programme_complet,
    generer_contenu_lecon,
    generer_parcours_oriente,
    attribuer_badges,
    assistant_code,
    generateur_exercices,
    explication_concept,
    correction_automatique,
    parcours_adaptatif,
    chatbot_tuteur,
    simuler_carriere,
)
def _construire_contexte_utilisateur(request):
    """Construit un contexte utilisateur pour personnaliser les réponses du chatbot."""
    contexte_utilisateur = None
    if request.user.is_authenticated:
        formations_suivies = []
        progressions = (
            ProgressionLecon.objects.filter(utilisateur=request.user, terminee=True)
            .select_related('lecon__module__formation')
            .order_by('-date_completion')[:3]
        )
        for progression in progressions:
            formation = progression.lecon.module.formation
            if formation and formation.nom not in formations_suivies:
                formations_suivies.append(formation.nom)

        contexte_utilisateur = {
            'prenom': request.user.first_name or request.user.username,
            'formations_suivies': formations_suivies,
        }
    return contexte_utilisateur

# ================================================
# Pages principales
# ================================================

def accueil(request):
    """Page d'accueil avec statistiques dynamiques."""
    formations = Formation.objects.filter(actif=True)[:4]

    nb_etudiants = User.objects.filter(is_active=True).count()
    nb_formations = Formation.objects.filter(actif=True).count()
    nb_sujets_forum = Sujet.objects.count()

    stats = [
        {'valeur': nb_etudiants, 'suffixe': '+', 'label': 'Étudiants'},
        {'valeur': nb_formations, 'suffixe': '', 'label': 'Formations'},
        {'valeur': nb_sujets_forum, 'suffixe': '', 'label': 'Sujets forum'},
    ]
    print("DEBUG STATS:", stats)
    return render(request, 'academie/accueil.html', {
        'formations': formations,
        'stats': stats,
    })


def formations(request):
    """Page des formations organisées par école + formations gratuites + parcours professionnels."""

    ecoles = Ecole.objects.prefetch_related('formations').all()

    formations_gratuites = Formation.objects.filter(
        actif=True,
        gratuit=True
    )

    parcours_list = Parcours.objects.prefetch_related(
        'formations'
    ).filter(actif=True)

    return render(request, 'academie/formations.html', {
        'ecoles': ecoles,
        'formations_gratuites': formations_gratuites,
        'parcours_list': parcours_list,
    })


def detail_formation(request, formation_id):
    """Page de détail d'une formation avec son programme complet."""
    formation = Formation.objects.prefetch_related(
        'modules__lecons'
    ).get(id=formation_id, actif=True)

    pourcentage_progression = 0
    if request.user.is_authenticated:
        pourcentage_progression = formation.progression_pour(request.user)

    return render(request, 'academie/detail_formation.html', {
        'formation': formation,
        'pourcentage_progression': pourcentage_progression,
    })


def apropos(request):
    """Page à propos."""
    return render(request, 'academie/apropos.html')


def contact(request):
    """Page de contact avec formulaire d'inscription."""
    if request.method == 'POST':
        form = InscriptionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                '✅ Merci ! Votre message a été envoyé. '
                'Nous vous répondrons dans les 24 heures.'
            )
            return redirect('contact')
        else:
            messages.error(
                request,
                '❌ Une erreur est survenue. '
                'Veuillez vérifier les champs.'
            )
    else:
        form = InscriptionForm()
    return render(request, 'academie/contact.html', {'form': form})


# ================================================
# Authentification
# ================================================

def inscription_compte(request):
    """Créer un nouveau compte étudiant."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = InscriptionCompteForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(
                request,
                f'🎉 Bienvenue {user.first_name} ! '
                f'Ton compte a été créé avec succès.'
            )
            return redirect('dashboard')
        else:
            messages.error(
                request,
                '❌ Erreur lors de la création du compte. '
                'Vérifie les informations saisies.'
            )
    else:
        form = InscriptionCompteForm()

    return render(request, 'academie/inscription_compte.html',
                {'form': form})


def connexion(request):
    """Connexion à un compte existant."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = ConnexionForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(
                request,
                f'✅ Bienvenue {user.first_name or user.username} !'
            )
            return redirect('dashboard')
        else:
            messages.error(
                request,
                '❌ Identifiants incorrects. Vérifie ton nom '
                "d'utilisateur et ton mot de passe."
            )
    else:
        form = ConnexionForm(request)

    return render(request, 'academie/connexion.html', {'form': form})


def deconnexion(request):
    """Déconnexion."""
    logout(request)
    messages.success(request, '👋 Tu as été déconnecté avec succès.')
    return redirect('accueil')


@login_required(login_url='/connexion/')
def dashboard(request):
    """Tableau de bord étudiant moderne."""
    from .ia import calculer_stats_etudiant, attribuer_badges

    user = request.user
    stats = calculer_stats_etudiant(user)

    # Récupère les derniers badges (max 6)
    tous_badges = stats['badges']

    # Formations récemment actives (triées par progression)
    formations_actives = sorted(
        stats['en_cours'],
        key=lambda f: f['pourcentage'],
        reverse=True
    )[:4]
    nouveaux_badges = attribuer_badges(user)
    if nouveaux_badges:
        messages.success(request, f'🎉 Nouveau(x) badge(s) : {", ".join(nouveaux_badges)} !')
    for badge_type in nouveaux_badges: notifications.notifier_badge(user, badge_type)
    return render(request, 'academie/dashboard.html', {
        'user': user,
        'stats': stats,
        'badges': tous_badges,
        'formations_actives': formations_actives,
    })
# ================================================
# Statistiques (admin uniquement)
# ================================================

@staff_member_required
def statistiques(request):
    """Centre de Commande EdTech - Phases 1, 2 et 3."""
    from django.db.models import Sum
    from django.db.models.functions import TruncMonth

    # --- KPIs Phase 1 ---
    total_etudiants = User.objects.filter(is_active=True).count()
    total_formations = Formation.objects.filter(actif=True).count()
    total_certificats = Certificat.objects.count()
    total_leads = Inscription.objects.filter(formation__gratuit=True).count()
    total_inscriptions = Inscription.objects.count()
    taux_conversion = 0
    if total_leads > 0:
        taux_conversion = round((total_inscriptions / total_leads) * 100)

    # --- Tunnel Freemium (Phase 2) ---
    telechargements = total_leads
    comptes_crees = User.objects.count()
    inscriptions_payantes = Inscription.objects.filter(formation__gratuit=False).count()
    certificats_delivres = total_certificats
    taux_leads_comptes = round((comptes_crees / telechargements) * 100) if telechargements > 0 else 0
    taux_comptes_payant = round((inscriptions_payantes / comptes_crees) * 100) if comptes_crees > 0 else 0
    taux_payant_certif = round((certificats_delivres / inscriptions_payantes) * 100) if inscriptions_payantes > 0 else 0

    # --- Revenus (Phase 2) ---
    total_revenus = Inscription.objects.filter(formation__gratuit=False).aggregate(
        total=Sum('formation__prix')
    )['total'] or 0

    # --- Certificats ce mois ---
    debut_mois = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    certificats_mois = Certificat.objects.filter(date_emission__gte=debut_mois).count()

    # --- IA Analytics (Phase 3) ---
    quiz_generees = Quiz.objects.count()
    contenus_generes = Lecon.objects.filter(contenu__isnull=False).exclude(contenu='').count()

    # --- Formations populaires ---
    formations_populaires = Formation.objects.filter(actif=True).annotate(
        nb_inscriptions=Count('inscriptions')
    ).order_by('-nb_inscriptions')[:5]

    # --- Inscriptions par mois ---
    douze_mois = timezone.now() - timedelta(days=365)
    inscriptions_mensuelles = (
        Inscription.objects
        .filter(date_inscription__gte=douze_mois)
        .annotate(mois=TruncMonth('date_inscription'))
        .values('mois')
        .annotate(total=Count('id'))
        .order_by('mois')
    )
    mois_labels = [item['mois'].strftime('%b %Y') for item in inscriptions_mensuelles]
    mois_data = [item['total'] for item in inscriptions_mensuelles]

    # --- Activité forum ---
    total_sujets = Sujet.objects.count()
    total_reponses = Reponse.objects.count()
    membres_actifs = User.objects.annotate(
        nb_actions=Count('sujets_forum', distinct=True) + Count('reponses_forum', distinct=True)
    ).filter(nb_actions__gt=0).count()

    # --- Centre d'alertes ---
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
        # Phase 1
        'total_etudiants': total_etudiants,
        'total_formations': total_formations,
        'total_certificats': total_certificats,
        'total_revenus': total_revenus,
        'total_leads': total_leads,
        'total_inscriptions': total_inscriptions,
        'taux_conversion': taux_conversion,
        'formations_populaires': formations_populaires,
        'mois_labels': mois_labels,
        'mois_data': mois_data,
        'total_sujets': total_sujets,
        'total_reponses': total_reponses,
        'membres_actifs': membres_actifs,
        'alertes': alertes,
        # Phase 2
        'telechargements': telechargements,
        'comptes_crees': comptes_crees,
        'inscriptions_payantes': inscriptions_payantes,
        'certificats_delivres': certificats_delivres,
        'taux_leads_comptes': taux_leads_comptes,
        'taux_comptes_payant': taux_comptes_payant,
        'taux_payant_certif': taux_payant_certif,
        'certificats_mois': certificats_mois,
        # Phase 3
        'quiz_generees': quiz_generees,
        'contenus_generes': contenus_generes,
    }
    return render(request, 'academie/statistiques.html', contexte)

# ================================================
# Recherche
# ================================================

def recherche_formations(request):
    """Recherche de formations par mot-clé."""
    terme = request.GET.get('q', '')

    if terme:
        resultats = Formation.objects.filter(
            Q(nom__icontains=terme) |
            Q(description__icontains=terme) |
            Q(debouches__icontains=terme),
            actif=True
        ).select_related('ecole')
    else:
        resultats = Formation.objects.none()

    return render(request, 'academie/recherche.html', {
        'resultats': resultats,
        'terme': terme,
    })


# ================================================
# Intelligence Artificielle — Blessy AI
# ================================================

def chat_ia(request):
    """Page du chat Blessy AI avec historique."""
    historique = request.session.get('chat_historique', [])
    return render(request, 'academie/chat_ia.html', {
        'historique_chat': historique,
    })


@csrf_exempt
def api_chat_ia(request):
    """API endpoint pour le chat IA (AJAX) avec mémoire de conversation."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            question = data.get('question', '').strip()

            if not question:
                return JsonResponse({'erreur': 'Question vide'}, status=400)

            if len(question) > 500:
                return JsonResponse(
                    {'erreur': 'Question trop longue (max 500 caractères)'},
                    status=400
                )

            formations_actives = Formation.objects.filter(actif=True)[:5]
            historique = request.session.get('chat_historique', [])
            contexte_utilisateur = _construire_contexte_utilisateur(request)

            reponse = blessy_ai_repondre(
                question,
                formations_actives,
                historique=historique,
                contexte_utilisateur=contexte_utilisateur,
            )

            historique.append({'role': 'user', 'content': question})
            historique.append({'role': 'assistant', 'content': reponse})
            request.session['chat_historique'] = historique[-12:]
            request.session.modified = True

            return JsonResponse({'reponse': reponse})

        except Exception as e:
            return JsonResponse({'erreur': str(e)}, status=500)

    return JsonResponse({'erreur': 'Méthode non autorisée'}, status=405)

def recommandations_ia(request):
    """Page de recommandations personnalisées."""
    recommandations = None
    interets = ''

    if request.method == 'POST':
        interets = request.POST.get('interets', '').strip()
        if interets:
            formations_actives = Formation.objects.filter(actif=True)
            recommandations = recommander_formations(interets, formations_actives)

    return render(request, 'academie/recommandations_ia.html', {
        'recommandations': recommandations,
        'interets': interets,
    })


@staff_member_required
@csrf_exempt
def api_generer_formation(request):
    """API pour générer le contenu d'une formation via l'IA (admin only)."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            nom = data.get('nom', '').strip()
            ecole = data.get('ecole', '').strip()

            if not nom:
                return JsonResponse({'erreur': 'Nom de formation requis'}, status=400)

            contenu = generer_contenu_formation(nom, ecole)

            return JsonResponse(contenu)

        except Exception as e:
            return JsonResponse({'erreur': str(e)}, status=500)

    return JsonResponse({'erreur': 'Méthode non autorisée'}, status=405)


# ================================================
# Quiz Intelligents
# ================================================

@staff_member_required
@csrf_exempt
def api_generer_quiz(request):
    """API pour générer un quiz via l'IA (admin only)."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            sujet = data.get('sujet', '').strip()
            nombre = int(data.get('nombre', 5))

            if not sujet:
                return JsonResponse({'erreur': 'Sujet requis'}, status=400)

            questions = generer_quiz(sujet, nombre)

            if not questions:
                return JsonResponse({'erreur': 'Génération échouée'}, status=500)

            return JsonResponse({'questions': questions})

        except Exception as e:
            return JsonResponse({'erreur': str(e)}, status=500)

    return JsonResponse({'erreur': 'Méthode non autorisée'}, status=405)


def liste_quiz(request, formation_id):
    """Affiche les quiz disponibles pour une formation."""
    formation = Formation.objects.get(id=formation_id)
    quiz_disponibles = Quiz.objects.filter(formation=formation, actif=True)
    return render(request, 'academie/liste_quiz.html', {
        'formation': formation,
        'quiz_disponibles': quiz_disponibles,
    })


@login_required(login_url='/connexion/')
def passer_quiz(request, quiz_id):
    """Page pour passer un quiz."""
    quiz = Quiz.objects.prefetch_related('questions').get(id=quiz_id)

    if request.method == 'POST':
        score = 0
        total = quiz.questions.count()

        for question in quiz.questions.all():
            reponse_utilisateur = request.POST.get(f'question_{question.id}')
            if reponse_utilisateur == question.bonne_reponse:
                score += 1

        ResultatQuiz.objects.create(
            utilisateur=request.user,
            quiz=quiz,
            score=score,
            total_questions=total
        )

        # Attribution des badges (toujours)
        attribuer_badges(request.user)

        # XP seulement si score >= 70%
        pourcentage = round((score / total) * 100) if total > 0 else 0
        if pourcentage >= 70:
            from .xp_utils import ajouter_xp
            ajouter_xp(request.user, 'quiz_reussi')

            # Notification de succès
            notifications.creer_notification(
                request.user,
                "📝 Quiz réussi !",
                f"Tu as obtenu {score}/{total} au quiz \"{quiz.titre}\".",
                f"/formation/{quiz.formation.id}/quiz/"
            )

        return render(request, 'academie/resultat_quiz.html', {
            'quiz': quiz,
            'score': score,
            'total': total,
            'pourcentage': pourcentage,
        })

    return render(request, 'academie/passer_quiz.html', {'quiz': quiz})

@staff_member_required
@csrf_exempt
def api_generer_programme(request):
    """API pour générer un programme complet (modules+leçons) via l'IA."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            formation_id = data.get('formation_id')

            if not formation_id:
                return JsonResponse({'erreur': 'ID de formation requis'}, status=400)

            formation = Formation.objects.get(id=formation_id)

            programme = generer_programme_complet(
                formation.nom,
                formation.description,
                formation.niveau
            )

            if not programme:
                return JsonResponse({'erreur': 'Génération échouée'}, status=500)

            for index_module, module_data in enumerate(programme, start=1):
                module = Module.objects.create(
                    formation=formation,
                    titre=module_data.get('titre', f'Module {index_module}'),
                    description=module_data.get('description', ''),
                    ordre=index_module
                )

                for index_lecon, lecon_data in enumerate(module_data.get('lecons', []), start=1):
                    Lecon.objects.create(
                        module=module,
                        titre=lecon_data.get('titre', f'Leçon {index_lecon}'),
                        resume=lecon_data.get('resume', ''),
                        duree_minutes=lecon_data.get('duree_minutes', 15),
                        ordre=index_lecon
                    )

            return JsonResponse({
                'succes': True,
                'nombre_modules': len(programme),
                'message': f'{len(programme)} modules créés avec succès !'
            })

        except Formation.DoesNotExist:
            return JsonResponse({'erreur': 'Formation introuvable'}, status=404)
        except Exception as e:
            return JsonResponse({'erreur': str(e)}, status=500)

    return JsonResponse({'erreur': 'Méthode non autorisée'}, status=405)


@staff_member_required
@csrf_exempt
def api_generer_contenu_lecon(request):
    """API pour générer le contenu d'UNE leçon via l'IA."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            lecon_id = data.get('lecon_id')

            if not lecon_id:
                return JsonResponse({'erreur': 'ID de leçon requis'}, status=400)

            lecon = Lecon.objects.select_related('module__formation').get(id=lecon_id)

            contenu = generer_contenu_lecon(
                titre_lecon=lecon.titre,
                resume_lecon=lecon.resume,
                contexte_formation=lecon.module.formation.nom,
                contexte_module=lecon.module.titre
            )

            lecon.contenu = contenu
            lecon.save()

            return JsonResponse({
                'succes': True,
                'contenu': contenu,
            })

        except Lecon.DoesNotExist:
            return JsonResponse({'erreur': 'Leçon introuvable'}, status=404)
        except Exception as e:
            return JsonResponse({'erreur': str(e)}, status=500)

    return JsonResponse({'erreur': 'Méthode non autorisée'}, status=405)


@staff_member_required
@csrf_exempt
def api_generer_contenu_module(request):
    """API pour générer le contenu de TOUTES les leçons d'un module."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            module_id = data.get('module_id')

            if not module_id:
                return JsonResponse({'erreur': 'ID de module requis'}, status=400)

            module = Module.objects.select_related('formation').prefetch_related('lecons').get(id=module_id)

            lecons = module.lecons.all()
            nombre_traitees = 0

            for lecon in lecons:
                contenu = generer_contenu_lecon(
                    titre_lecon=lecon.titre,
                    resume_lecon=lecon.resume,
                    contexte_formation=module.formation.nom,
                    contexte_module=module.titre
                )
                lecon.contenu = contenu
                lecon.save()
                nombre_traitees += 1

            return JsonResponse({
                'succes': True,
                'nombre_lecons': nombre_traitees,
                'message': f'{nombre_traitees} leçons mises à jour avec succès !'
            })

        except Module.DoesNotExist:
            return JsonResponse({'erreur': 'Module introuvable'}, status=404)
        except Exception as e:
            return JsonResponse({'erreur': str(e)}, status=500)

    return JsonResponse({'erreur': 'Méthode non autorisée'}, status=405)


@login_required(login_url='/connexion/')
def lire_lecon(request, lecon_id):
    """Page de lecture d'une leçon (réservée aux connectés)."""
    lecon = Lecon.objects.select_related('module__formation').get(id=lecon_id)

    contenu_html = lecon.contenu

    lecons_module = list(lecon.module.lecons.all())
    index_actuel = lecons_module.index(lecon)
    lecon_precedente = lecons_module[index_actuel - 1] if index_actuel > 0 else None
    lecon_suivante = lecons_module[index_actuel + 1] if index_actuel < len(lecons_module) - 1 else None

    progression = ProgressionLecon.objects.filter(
        utilisateur=request.user,
        lecon=lecon
    ).first()
    lecon_terminee = progression.terminee if progression else False

    formation = lecon.module.formation
    pourcentage_formation = formation.progression_pour(request.user)
    return render(request, 'academie/lire_lecon.html', {
        'lecon': lecon,
        'contenu_html': contenu_html,
        'lecon_precedente': lecon_precedente,
        'lecon_suivante': lecon_suivante,
        'lecon_terminee': lecon_terminee,
        'pourcentage_formation': pourcentage_formation,
    })


@login_required(login_url='/connexion/')
@csrf_exempt
def marquer_lecon_terminee(request, lecon_id):
    """Marque une leçon comme terminée (ou non) pour l'utilisateur connecté."""
    if request.method == 'POST':
        try:
            lecon = Lecon.objects.get(id=lecon_id)

            progression, cree = ProgressionLecon.objects.get_or_create(
                utilisateur=request.user,
                lecon=lecon,
            )

            progression.terminee = not progression.terminee
            progression.date_completion = timezone.now() if progression.terminee else None
            progression.save()

            # Ajouter XP seulement si la leçon est maintenant terminée
            if progression.terminee:
                ajouter_xp(request.user, 'lecon_terminee')

                # Notification si la formation est maintenant complétée
                formation = lecon.module.formation
                pourcentage = formation.progression_pour(request.user)
                if pourcentage == 100:
                    notifications.notifier_formation_completee(request.user, formation.nom)

            formation = lecon.module.formation
            nouveau_pourcentage = formation.progression_pour(request.user)

            return JsonResponse({
                'succes': True,
                'terminee': progression.terminee,
                'progression_formation': nouveau_pourcentage,
            })

        except Lecon.DoesNotExist:
            return JsonResponse({'erreur': 'Leçon introuvable'}, status=404)
        except Exception as e:
            return JsonResponse({'erreur': str(e)}, status=500)

    return JsonResponse({'erreur': 'Méthode non autorisée'}, status=405)
# ================================================
# Certificats PDF
# ================================================

@login_required(login_url='/connexion/')
def telecharger_certificat(request, formation_id):
    """Génère et télécharge le certificat PDF avec QR code de vérification."""
    from .models import Certificat
    import qrcode
    from io import BytesIO
    import base64

    formation = Formation.objects.prefetch_related(
        'modules__lecons'
    ).get(id=formation_id, actif=True)

    pourcentage = formation.progression_pour(request.user)

    if pourcentage < 100:
        messages.error(
            request,
            f'❌ Tu dois compléter 100% de la formation pour obtenir le certificat '
            f'(progression actuelle : {pourcentage}%).'
        )
        return redirect('detail_formation', formation_id=formation_id)

    # Génère un numéro de certificat unique
    chaine = f"{request.user.id}-{formation.id}-{request.user.date_joined}"
    numero = f"BTA-{hashlib.md5(chaine.encode()).hexdigest()[:8].upper()}"

    # Crée le certificat en base s'il n'existe pas
    certificat, created = Certificat.objects.get_or_create(
        utilisateur=request.user,
        formation=formation,
        defaults={'numero': numero}
    )
    # Si déjà existant, utiliser le numéro existant
    if not created:
        numero = certificat.numero

    # URL de vérification
    url_verification = request.build_absolute_uri(
        f"/certificat/{numero}/"
    )

    # Génère le QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(url_verification)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    # Convertit l'image en base64 pour l'insérer dans le HTML
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    qr_code_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

    contexte = {
        'prenom': request.user.first_name or request.user.username,
        'nom': request.user.last_name or '',
        'formation': formation,
        'date_emission': certificat.date_emission.strftime('%d %B %Y'),
        'numero_certificat': numero,
        'qr_code_base64': qr_code_base64,
        'url_verification': url_verification,
    }

    html_certificat = render_to_string(
        'academie/pdf/certificat.html',
        contexte,
        request=request
    )

    try:
        from weasyprint import HTML
        pdf = HTML(
            string=html_certificat,
            base_url=request.build_absolute_uri('/')
        ).write_pdf()

        nom_fichier = f"certificat-{formation.nom.replace(' ', '-').lower()}-BTA.pdf"
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{nom_fichier}"'
        return response

    except Exception as e:
        messages.error(
            request,
            f'❌ Erreur lors de la génération du certificat : {str(e)}'
        )
        return redirect('detail_formation', formation_id=formation_id)

    
    
    # ================================================
# Forum Communautaire
# ================================================

def forum_liste(request):
    """Page principale du forum — liste tous les sujets."""
    categorie = request.GET.get('categorie', '')
    formation_id = request.GET.get('formation', '')
    recherche = request.GET.get('q', '')

    sujets = Sujet.objects.select_related(
        'auteur', 'formation'
    ).all()

    if categorie:
        sujets = sujets.filter(categorie=categorie)

    if formation_id:
        sujets = sujets.filter(formation_id=formation_id)

    if recherche:
        sujets = sujets.filter(
            Q(titre__icontains=recherche) |
            Q(contenu__icontains=recherche)
        )

    # Pagination — 10 sujets par page
    paginator = Paginator(sujets, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    formations = Formation.objects.filter(actif=True)

    return render(request, 'academie/forum/liste.html', {
        'sujets': page_obj,
        'page_obj': page_obj,
        'formations': formations,
        'categorie_active': categorie,
        'formation_active': formation_id,
        'categories': Sujet.CATEGORIES,
        'recherche': recherche,
    })

def forum_detail(request, sujet_id):
    """Page de détail d'un sujet avec ses réponses."""
    sujet = Sujet.objects.select_related(
        'auteur', 'formation'
    ).prefetch_related(
        'reponses__auteur', 'reponses__reactions',
        'reactions'
    ).get(id=sujet_id)

    # Incrémente le compteur de vues
    sujet.vues += 1
    sujet.save(update_fields=['vues'])

    # Likes de l'utilisateur connecté
    likes_sujets = set()
    likes_reponses = set()

    if request.user.is_authenticated:
        likes_sujets = set(
            Reaction.objects.filter(
                utilisateur=request.user,
                sujet=sujet
            ).values_list('sujet_id', flat=True)
        )
        likes_reponses = set(
            Reaction.objects.filter(
                utilisateur=request.user,
                reponse__sujet=sujet
            ).values_list('reponse_id', flat=True)
        )

    # Traitement du formulaire de réponse
    if request.method == 'POST' and request.user.is_authenticated:
        contenu = request.POST.get('contenu', '').strip()
        if contenu:
            Reponse.objects.create(
                sujet=sujet,
                contenu=contenu,
                auteur=request.user,
            )

            # Ajouter XP pour la réponse postée
            ajouter_xp(request.user, 'reponse_forum')

            messages.success(request, '✅ Réponse publiée !')
            return redirect('forum_detail', sujet_id=sujet_id)

    return render(request, 'academie/forum/detail.html', {
        'sujet': sujet,
        'likes_sujets': likes_sujets,
        'likes_reponses': likes_reponses,
    })

@login_required(login_url='/connexion/')
def forum_creer(request):
    """Créer un nouveau sujet."""
    if request.method == 'POST':
        titre = request.POST.get('titre', '').strip()
        contenu = request.POST.get('contenu', '').strip()
        categorie = request.POST.get('categorie', 'general')
        formation_id = request.POST.get('formation', '')

        if not titre or not contenu:
            messages.error(request, '❌ Titre et contenu sont obligatoires.')
        else:
            sujet = Sujet.objects.create(
                titre=titre,
                contenu=contenu,
                categorie=categorie,
                auteur=request.user,
                formation_id=formation_id if formation_id else None,
            )

            attribuer_badges(request.user)
            ajouter_xp(request.user, 'sujet_forum')                     # ← XP ajouté ici

            notifications.creer_notification(
                request.user,
                "📝 Sujet créé",
                f"Ton sujet \"{sujet.titre}\" a été publié avec succès.",
                f"/forum/{sujet.id}/"
            )
            messages.success(request, '✅ Sujet créé avec succès !')
            return redirect('forum_detail', sujet_id=sujet.id)

    formations = Formation.objects.filter(actif=True)
    return render(request, 'academie/forum/creer.html', {
        'formations': formations,
        'categories': Sujet.CATEGORIES,
    })


@login_required(login_url='/connexion/')
@csrf_exempt
def forum_liker(request, type_cible, cible_id):
    """Toggle like sur un sujet ou une réponse."""
    if request.method == 'POST':
        try:
            if type_cible == 'sujet':
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

            elif type_cible == 'reponse':
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
                return JsonResponse({'erreur': 'Type invalide'}, status=400)

            return JsonResponse({
                'succes': True,
                'liked': liked,
                'total': total,
            })

        except Exception as e:
            return JsonResponse({'erreur': str(e)}, status=500)

    return JsonResponse({'erreur': 'Méthode non autorisée'}, status=405)


@login_required(login_url='/connexion/')
def forum_accepter_reponse(request, reponse_id):
    """Marque une réponse comme solution acceptée."""
    if request.method == 'POST':
        reponse = Reponse.objects.select_related('sujet').get(id=reponse_id)

        # Seul l'auteur du sujet peut accepter une réponse
        if request.user != reponse.sujet.auteur:
            messages.error(
                request,
                '❌ Seul l\'auteur du sujet peut accepter une réponse.'
            )
            return redirect('forum_detail', sujet_id=reponse.sujet.id)

        # Désactive toutes les autres réponses acceptées
        Reponse.objects.filter(sujet=reponse.sujet).update(acceptee=False)

        # Active celle-ci
        reponse.acceptee = True
        reponse.save()

        # Marque le sujet comme résolu
        reponse.sujet.resolu = True
        reponse.sujet.save()
        attribuer_badges(reponse.auteur)

        # Ajouter XP pour la réponse acceptée
        ajouter_xp(reponse.auteur, 'reponse_acceptee')

        notifications.creer_notification(
            reponse.auteur,
            "✅ Réponse acceptée",
            f"Ta réponse sur \"{reponse.sujet.titre}\" a été acceptée comme solution.",
            f"/forum/{reponse.sujet.id}/"
        )
        messages.success(request, '✅ Réponse marquée comme solution !')
        return redirect('forum_detail', sujet_id=reponse.sujet.id)

    return redirect('forum_liste')


@login_required(login_url='/connexion/')
def forum_creer(request):
    """Créer un nouveau sujet."""
    if request.method == 'POST':
        titre = request.POST.get('titre', '').strip()
        contenu = request.POST.get('contenu', '').strip()
        categorie = request.POST.get('categorie', 'general')
        formation_id = request.POST.get('formation', '')

        if not titre or not contenu:
            messages.error(request, '❌ Titre et contenu sont obligatoires.')
            formations = Formation.objects.filter(actif=True)
            return render(request, 'academie/forum/creer.html', {
                'form': SujetForm(),
                'formations': formations,
                'categories': Sujet.CATEGORIES,
            })

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
            f"Ton sujet \"{sujet.titre}\" a été publié avec succès.",
            f"/forum/{sujet.id}/"
        )
        messages.success(request, '✅ Sujet créé avec succès !')
        return redirect('forum_detail', sujet_id=sujet.id)

    formations = Formation.objects.filter(actif=True)
    return render(request, 'academie/forum/creer.html', {
        'form': SujetForm(),
        'formations': formations,
        'categories': Sujet.CATEGORIES,
    })

def forum_membres(request):
    """Classement des membres du forum."""
    from django.contrib.auth.models import User

    membres = User.objects.annotate(
        nb_sujets=Count('sujets_forum', distinct=True),
        nb_reponses=Count('reponses_forum', distinct=True),
        nb_solutions=Count(
            'reponses_forum',
            filter=Q(reponses_forum__acceptee=True),
            distinct=True
        ),
        nb_likes=Count('reactions_forum', distinct=True),
    ).filter(
        Q(nb_sujets__gt=0) | Q(nb_reponses__gt=0)
    ).order_by('-nb_reponses', '-nb_solutions', '-nb_sujets')[:20]

    return render(request, 'academie/forum/membres.html', {
        'membres': membres,
    })

# ================================================
# Parcours d'Orientation Intelligent
# ================================================

def orientation_ia(request):
    """Page du parcours d'orientation personnalisé."""

    profils = [
        ('lyceen_etudiant', 'Lycéen / Étudiant', '🎓'),
        ('professionnel', 'Professionnel', '💼'),
        ('entrepreneur', 'Entrepreneur', '🚀'),
        ('numerique', 'Déjà dans le numérique', '👨‍💻'),
    ]

    objectifs = [
        ('developpeur', 'Devenir développeur', '💻'),
        ('design_creation', 'Design & Création', '🎨'),
        ('marketing_business', 'Marketing & Business', '📊'),
        ('maitriser_ia', "Maîtriser l'IA", '🤖'),
        ('technicien', 'Technicien informatique', '🔧'),
    ]

    disponibilites = [
        ('1-2h', '1-2h par jour', '⏰'),
        ('3-4h', '3-4h par jour', '⏱'),
        ('temps_plein', 'Temps plein', '🔥'),
    ]

    resultat = None
    erreur = None

    if request.method == 'POST':
        profil = request.POST.get('profil', '')
        objectif = request.POST.get('objectif', '')
        disponibilite = request.POST.get('disponibilite', '')
        details = request.POST.get('details', '').strip()

        if profil and objectif and disponibilite:
            formations = Formation.objects.filter(actif=True).select_related('ecole')
            resultat = generer_parcours_oriente(
                profil, objectif, disponibilite, details, formations
            )

            if 'erreur' in resultat:
                erreur = resultat['erreur']
                resultat = None
        else:
            erreur = "Veuillez répondre aux 3 premières questions."

    return render(request, 'academie/orientation.html', {
        'resultat': resultat,
        'erreur': erreur,
        'profils': profils,
        'objectifs': objectifs,
        'disponibilites': disponibilites,
        'post_data': request.POST if request.method == 'POST' else None,
    })


# ================================================
# VUES API POUR LE BOUTON IA (6 fonctionnalités)
# ================================================


@csrf_exempt
@require_POST
def api_assistant_code(request):
    """API 1 : Assistant Code - Analyse et corrige le code"""
    try:
        data = json.loads(request.body)
        code = data.get('code', '')
        langage = data.get('langage', 'python')
        question = data.get('question', '')

        if not code:
            return JsonResponse({'erreur': 'Le champ "code" est requis.'}, status=400)

        reponse = assistant_code(code=code, langage=langage, question=question)
        return JsonResponse({'reponse': reponse, 'fonction': 'assistant_code'})
    except json.JSONDecodeError:
        return JsonResponse({'erreur': 'JSON invalide'}, status=400)
    except Exception as e:
        return JsonResponse({'erreur': str(e)}, status=500)


@csrf_exempt
@require_POST
def api_generateur_exercices(request):
    """API 2 : Générateur d'exercices personnalisés"""
    try:
        data = json.loads(request.body)
        sujet = data.get('sujet', '')
        niveau = data.get('niveau', 'debutant')
        format_ex = data.get('format_exercice', 'code')

        if not sujet:
            return JsonResponse({'erreur': 'Le champ "sujet" est requis.'}, status=400)

        reponse = generateur_exercices(sujet=sujet, niveau=niveau, format_exercice=format_ex)
        return JsonResponse({'reponse': reponse, 'fonction': 'generateur_exercices'})
    except json.JSONDecodeError:
        return JsonResponse({'erreur': 'JSON invalide'}, status=400)
    except Exception as e:
        return JsonResponse({'erreur': str(e)}, status=500)


@csrf_exempt
@require_POST
def api_explication_concept(request):
    """API 3 : Explication de concept"""
    try:
        data = json.loads(request.body)
        question = data.get('question', '')
        niveau_eleve = data.get('niveau_eleve', 'debutant')

        if not question:
            return JsonResponse({'erreur': 'Le champ "question" est requis.'}, status=400)

        reponse = explication_concept(question=question, niveau_eleve=niveau_eleve)
        return JsonResponse({'reponse': reponse, 'fonction': 'explication_concept'})
    except json.JSONDecodeError:
        return JsonResponse({'erreur': 'JSON invalide'}, status=400)
    except Exception as e:
        return JsonResponse({'erreur': str(e)}, status=500)


@csrf_exempt
@require_POST
def api_correction_automatique(request):
    """API 4 : Correction automatique d'exercice"""
    try:
        data = json.loads(request.body)
        enonce = data.get('enonce', '')
        reponse_eleve = data.get('reponse_eleve', '')
        bareme = data.get('bareme', '')

        if not enonce or not reponse_eleve:
            return JsonResponse({'erreur': 'Les champs "enonce" et "reponse_eleve" sont requis.'}, status=400)

        reponse = correction_automatique(enonce=enonce, reponse_eleve=reponse_eleve, bareme=bareme)
        return JsonResponse({'reponse': reponse, 'fonction': 'correction_automatique'})
    except json.JSONDecodeError:
        return JsonResponse({'erreur': 'JSON invalide'}, status=400)
    except Exception as e:
        return JsonResponse({'erreur': str(e)}, status=500)


@csrf_exempt
@require_POST
def api_parcours_adaptatif(request):
    """API 5 : Recommandation de parcours adaptatif"""
    try:
        data = json.loads(request.body)
        profil_scores = data.get('profil_scores', {})
        parcours_actuel = data.get('parcours_actuel', '')
        objectif = data.get('objectif', '')

        if not profil_scores:
            return JsonResponse({'erreur': 'Le champ "profil_scores" est requis.'}, status=400)

        reponse = parcours_adaptatif(
            profil_scores=profil_scores,
            parcours_actuel=parcours_actuel,
            objectif=objectif
        )
        return JsonResponse({'reponse': reponse, 'fonction': 'parcours_adaptatif'})
    except json.JSONDecodeError:
        return JsonResponse({'erreur': 'JSON invalide'}, status=400)
    except Exception as e:
        return JsonResponse({'erreur': str(e)}, status=500)


@csrf_exempt
@require_POST
def api_chatbot_tuteur(request):
    """API 6 : Chatbot tuteur conversationnel"""
    try:
        data = json.loads(request.body)
        message = data.get('message', '')
        historique = data.get('historique', [])
        niveau_eleve = data.get('niveau_eleve', 'debutant')

        if not message:
            return JsonResponse({'erreur': 'Le champ "message" est requis.'}, status=400)

        reponse = chatbot_tuteur(message=message, historique=historique, niveau_eleve=niveau_eleve)
        return JsonResponse({'reponse': reponse, 'fonction': 'chatbot_tuteur'})
    except json.JSONDecodeError:
        return JsonResponse({'erreur': 'JSON invalide'}, status=400)
    except Exception as e:
        return JsonResponse({'erreur': str(e)}, status=500)
    

    # ================================================
# Simulateur de carrière
# ================================================

@csrf_exempt
@require_POST
def api_simuler_carriere(request):
    """API pour le simulateur de carrière."""
    try:
        data = json.loads(request.body)
        metier = data.get('metier', '').strip()

        if not metier:
            return JsonResponse({'erreur': 'Le champ "metier" est requis.'}, status=400)

        reponse = simuler_carriere(metier=metier)
        return JsonResponse({'reponse': reponse, 'metier': metier})
    except json.JSONDecodeError:
        return JsonResponse({'erreur': 'JSON invalide'}, status=400)
    except Exception as e:
        return JsonResponse({'erreur': str(e)}, status=500)


def simulateur_carriere(request):
    """Page du simulateur de carrière."""
    metiers = [
        {'id': 'developpeur-web', 'nom': 'Développeur Web', 'icone': '💻'},
        {'id': 'analyste-donnees', 'nom': 'Analyste de Données', 'icone': '📊'},
        {'id': 'expert-cybersecurite', 'nom': 'Expert Cybersécurité', 'icone': '🔒'},
        {'id': 'designer-graphique', 'nom': 'Designer Graphique', 'icone': '🎨'},
        {'id': 'ia-machine-learning', 'nom': 'IA & Machine Learning', 'icone': '🤖'},
        {'id': 'administrateur-reseaux', 'nom': 'Administrateur Réseaux', 'icone': '🌐'},
    ]
    return render(request, 'academie/simulateur_carriere.html', {'metiers': metiers})


# ================================================
# Espace Recrutement / Portfolio
# ================================================

def espace_recrutement(request):
    """Page publique présentant les meilleurs étudiants avec leurs portfolios."""
    from django.contrib.auth.models import User
    from .models import Formation, BadgeForum, ProjetEtudiant
    from django.db.models import Count, Q

    etudiants_qs = User.objects.annotate(
        nb_formations=Count('progressions__lecon__module__formation', 
                            filter=Q(progressions__terminee=True), distinct=True),
        nb_quiz=Count('resultats_quiz', distinct=True),
        nb_projets=Count('projets', distinct=True),
        nb_badges=Count('badges_forum', distinct=True),
    ).filter(
        Q(nb_formations__gt=0) | Q(nb_projets__gt=0)
    ).order_by('-nb_badges', '-nb_formations')[:20]

    etudiants_data = []
    for user in etudiants_qs:
        # Formations complétées à 100%
        formations_completees = []
        for formation in Formation.objects.filter(actif=True):
            if formation.progression_pour(user) == 100:
                formations_completees.append(formation)

        # Projets récents (max 3)
        projets = ProjetEtudiant.objects.filter(auteur=user).order_by('-date_creation')[:3]

        # Badges
        badges = BadgeForum.objects.filter(utilisateur=user)

        etudiants_data.append({
            'user': user,
            'certifications': formations_completees,
            'badges': badges,
            'projets': projets,
            'nb_formations': user.nb_formations,
            'nb_quiz': user.nb_quiz,
            'nb_projets': user.nb_projets,
            'nb_badges': user.nb_badges,
        })

    return render(request, 'academie/recrutement.html', {
        'etudiants_data': etudiants_data,
    })

@login_required(login_url='/connexion/')
def mon_portfolio(request):
    """Page où l'étudiant gère ses projets."""
    if request.method == 'POST':
        titre = request.POST.get('titre', '').strip()
        description = request.POST.get('description', '').strip()
        technologies = request.POST.get('technologies', '').strip()
        lien = request.POST.get('lien', '').strip()
        image = request.FILES.get('image')

        if titre and description:
            ProjetEtudiant.objects.create(
                auteur=request.user,
                titre=titre,
                description=description,
                technologies=technologies,
                lien=lien if lien else None,
                image=image,
            )
            messages.success(request, '✅ Projet ajouté avec succès !')
            return redirect('mon_portfolio')
        else:
            messages.error(request, '❌ Titre et description sont obligatoires.')

    projets = ProjetEtudiant.objects.filter(auteur=request.user)
    return render(request, 'academie/portfolio.html', {
        'projets': projets,
    })


def verifier_certificat(request, numero):
    """Page publique de vérification d'un certificat."""
    from .models import Certificat
    certificat = None
    try:
        certificat = Certificat.objects.select_related('utilisateur', 'formation').get(numero=numero)
    except:
        pass

    return render(request, 'academie/verifier_certificat.html', {
        'certificat': certificat
    })


@login_required(login_url='/connexion/')
def notifications_liste(request):
    """Page listant les notifications de l'utilisateur connecté."""
    from .models import Notification
    notifs = Notification.objects.filter(utilisateur=request.user).order_by('-date_creation')[:30]
    # Marque comme lues toutes les notifications affichées
    ids_non_lues = [n.id for n in notifs if not n.lue]
    if ids_non_lues:
        Notification.objects.filter(id__in=ids_non_lues).update(lue=True)
    return render(request, 'academie/notifications.html', {'notifications': notifs})