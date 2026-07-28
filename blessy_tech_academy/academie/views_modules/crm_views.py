# ================================================
# VIEWS_MODULES/CRM_VIEWS.PY — Vues CRM (leads, interactions)
# ================================================

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from crm.models import Inscription, InteractionCRM
from academie.permissions import role_required



# ================================================
# Dashboard CRM
# ================================================
@login_required
@role_required("marketing", "support", "admin", "super_admin")
def dashboard_crm(request):
    """Centre CRM — gestion des leads/prospects."""
    statut_filtre = request.GET.get("statut", "")

    leads = Inscription.objects.select_related("formation", "assigne_a").prefetch_related(
        "interactions"
    )
    if statut_filtre:
        leads = leads.filter(statut_lead=statut_filtre)

    stats = {
        "total": Inscription.objects.count(),
        "nouveaux": Inscription.objects.filter(statut_lead="nouveau").count(),
        "convertis": Inscription.objects.filter(statut_lead="converti").count(),
        "perdus": Inscription.objects.filter(statut_lead="perdu").count(),
    }

    return render(
        request,
        "admin/dashboard_crm.html",
        {
            "title": "📢 Centre CRM",
            "leads": leads.order_by("-date_inscription")[:50],
            "stats": stats,
            "statut_filtre": statut_filtre,
            "statuts": Inscription._meta.get_field("statut_lead").choices,
        },
    )


@login_required
@role_required("marketing", "support", "admin", "super_admin")
def ajouter_interaction_crm(request, inscription_id):
    """Ajoute une interaction à un lead."""
    if request.method == "POST":
        inscription = get_object_or_404(Inscription, id=inscription_id)
        InteractionCRM.objects.create(
            inscription=inscription,
            type_interaction=request.POST.get("type_interaction", "note"),
            contenu=request.POST.get("contenu", ""),
            auteur=request.user,
        )
        nouveau_statut = request.POST.get("nouveau_statut")
        if nouveau_statut:
            inscription.statut_lead = nouveau_statut
            inscription.save()
        messages.success(request, "✅ Interaction ajoutée")
    return redirect("dashboard_crm")