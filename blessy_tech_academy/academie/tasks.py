# ================================================
# TASKS.PY — Tâches Dramatiq persistantes (survivent aux redémarrages)
# Migration progressive depuis services/async_tasks.py (threading)
# ================================================

import dramatiq
from django.contrib.auth.models import User


@dramatiq.actor(max_retries=3, min_backoff=5000)
def tache_envoyer_email(template_path, contexte, destinataire, sujet, from_email=None):
    """Version Dramatiq de l'envoi email — persistante et avec retry automatique."""
    from .services.email_service import _envoyer_email
    _envoyer_email(template_path, contexte, destinataire, sujet, from_email)


@dramatiq.actor(max_retries=3, min_backoff=5000)
def tache_envoyer_push(utilisateur_id, titre, corps, url_cible='/', type_notif='systeme'):
    """Version Dramatiq de l'envoi push."""
    from .services.push_service import envoyer_push
    try:
        utilisateur = User.objects.get(id=utilisateur_id)
        envoyer_push(utilisateur, titre, corps, url_cible, type_notif)
    except User.DoesNotExist:
        pass


@dramatiq.actor(max_retries=2, min_backoff=10000, time_limit=120000)
def tache_generer_facture_pdf(commande_id):
    """Génération PDF facture en arrière-plan (opération potentiellement lourde)."""
    from .models import Order, Invoice
    from django.template.loader import render_to_string
    from weasyprint import HTML

    commande = Order.objects.get(id=commande_id)
    facture, _ = Invoice.objects.get_or_create(commande=commande)

    html_string = render_to_string('academie/pdf/facture.html', {'commande': commande, 'facture': facture})
    pdf_bytes = HTML(string=html_string).write_pdf()

    from django.core.files.base import ContentFile
    facture.fichier_pdf.save(f"facture_{facture.numero_facture}.pdf", ContentFile(pdf_bytes), save=True)


@dramatiq.actor(max_retries=1, time_limit=60000)
def tache_backfill_stats_academie(academie_id):
    """Recalcul de statistiques lourdes en arrière-plan (évite de bloquer le Dashboard Exécutif)."""
    from django.core.cache import cache
    from .models import Academie, Formation, Order
    from django.db.models import Sum

    academie = Academie.objects.get(id=academie_id)
    ca_total = Order.objects.filter(
        items__formation__ecole__academie=academie, statut='paye'
    ).distinct().aggregate(t=Sum('total'))['t'] or 0

    cache.set(f"stats_ca_academie_{academie_id}", ca_total, 3600)