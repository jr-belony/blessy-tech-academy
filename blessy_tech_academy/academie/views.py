from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Formation
from .forms import InscriptionForm


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
                'Veuillez vérifier les champs et réessayer.'
            )
    else:
        form = InscriptionForm()

    return render(request, 'academie/contact.html', {'form': form})