import json
import markdown as markdown_lib
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q, Count, Avg
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import (Formation, Inscription, Ecole, Quiz, Question, ResultatQuiz, Module, Lecon, ProgressionLecon)
from .forms import InscriptionForm, InscriptionCompteForm, ConnexionForm
from .ia import (
    blessy_ai_repondre,
    recommander_formations,
    generer_contenu_formation,
    generer_quiz,
    generer_programme_complet,
    generer_contenu_lecon,
)


# ================================================
# Pages principales
# ================================================

def accueil(request):
    """Page d'accueil."""
    formations = Formation.objects.filter(actif=True)[:4]
    return render(request, 'academie/accueil.html',
                    {'formations': formations})


def formations(request):
    """Page des formations organisées par école."""
    ecoles = Ecole.objects.prefetch_related('formations').all()
    return render(request, 'academie/formations.html', {'ecoles': ecoles})

def detail_formation(request, formation_id):
    """Page de détail d'une formation avec son programme complet."""
    formation = Formation.objects.prefetch_related(
        'modules__lecons'
    ).get(id=formation_id, actif=True)

    return render(request, 'academie/detail_formation.html', {
        'formation': formation,
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
    """Tableau de bord étudiant (accès protégé)."""
    user = request.user

    # Formations en cours (au moins 1 leçon consultée)
    formations_actives = Formation.objects.filter(actif=True)

    formations_avec_progression = []
    for formation in formations_actives:
        pourcentage = formation.progression_pour(user)
        if pourcentage > 0:
            formations_avec_progression.append({
                'formation': formation,
                'pourcentage': pourcentage,
            })

    # Quiz récents de l'étudiant
    resultats_recents = ResultatQuiz.objects.filter(
        utilisateur=user
    ).select_related('quiz__formation')[:5]

    return render(request, 'academie/dashboard.html', {
        'user': user,
        'formations_avec_progression': formations_avec_progression,
        'resultats_recents': resultats_recents,
    })

# ================================================
# Statistiques (admin uniquement)
# ================================================

@staff_member_required
def statistiques(request):
    """Page de statistiques pour les administrateurs."""
    total_formations = Formation.objects.filter(actif=True).count()
    total_inscriptions = Inscription.objects.count()
    inscriptions_non_traitees = Inscription.objects.filter(traite=False).count()
    prix_moyen = Formation.objects.aggregate(Avg('prix'))['prix__avg']
    formations_populaires = Formation.objects.annotate(
        nombre_inscrits=Count('inscriptions')
    ).order_by('-nombre_inscrits')[:5]

    contexte = {
        'total_formations': total_formations,
        'total_inscriptions': total_inscriptions,
        'inscriptions_non_traitees': inscriptions_non_traitees,
        'prix_moyen': round(prix_moyen, 2) if prix_moyen else 0,
        'formations_populaires': formations_populaires,
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
    """Page du chat Blessy AI."""
    return render(request, 'academie/chat_ia.html')


@csrf_exempt
def api_chat_ia(request):
    """API endpoint pour le chat IA (AJAX)."""
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
            reponse = blessy_ai_repondre(question, formations_actives)

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

        return render(request, 'academie/resultat_quiz.html', {
            'quiz': quiz,
            'score': score,
            'total': total,
            'pourcentage': round((score / total) * 100) if total > 0 else 0,
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

            # Sauvegarde directement en base de données
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

    contenu_html = markdown_lib.markdown(lecon.contenu) if lecon.contenu else ''

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

            # Bascule l'état : si déjà terminée, on annule ; sinon on valide
            progression.terminee = not progression.terminee

            from django.utils import timezone
            progression.date_completion = timezone.now() if progression.terminee else None
            progression.save()

            # Calcule la nouvelle progression de la formation
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