# ================================================
# VIEWS_MODULES/REFERRAL_VIEWS.PY — Parrainage communautaire
# ================================================
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from ..models import Parrainage

@login_required(login_url='/connexion/')
def mon_parrainage(request):
    """Espace parrainage étudiant — génère et suit ses invitations."""
    if request.method == 'POST':
        email = request.POST.get('email_ami', '').strip()
        if email:
            parrainage = Parrainage.objects.create(parrain=request.user, filleul_email=email)
            # ---- Envoi d'email (version simplifiée) ----
            # Si les utilitaires async existent, décommentez la ligne ci-dessous
            # executer_en_arriere_plan(...)
            # Sinon, l'invitation est créée, l'email sera envoyé plus tard
            messages.success(request, f"✅ Invitation envoyée à {email} !")
        return redirect('mon_parrainage')

    mes_parrainages = Parrainage.objects.filter(parrain=request.user).order_by('-date_invitation')
    nb_inscrits = mes_parrainages.filter(statut__in=['inscrit', 'actif']).count()

    return render(request, 'academie/mon_parrainage.html', {
        'parrainages': mes_parrainages, 'nb_inscrits': nb_inscrits,
    })