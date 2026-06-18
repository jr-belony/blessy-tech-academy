from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Avg
from .models import Formation, Inscription
from .forms import InscriptionForm, InscriptionCompteForm, ConnexionForm


# ================================================
# Pages principales
# ================================================

def accueil(request):
    """Page d'accueil."""
    formations = Formation.objects.filter(actif=True)[:4]
    return render(request, 'academie/accueil.html',
                  {'formations': formations})


def formations(request):
    """Page des formations."""
    toutes_formations = Formation.objects.filter(actif=True)
    return render(request, 'academie/formations.html',
                  {'formations': toutes_formations})


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
    return render(request, 'academie/dashboard.html', {'user': user})


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