# ================================================
# VIEWS_MODULES/BILLING_VIEWS.PY — Vues paiement
# ================================================

from decimal import Decimal
import json
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction as db_transaction
from django.db.models import Sum, Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from billing.models import (
    Order, OrderItem, Coupon, MoyenPaiement, Transaction,
    Invoice, AccesFormationDebloque, Promotion,
    AlerteFraude, detecter_fraude_potentielle,   # <-- ajouté
)
from academie.models import Formation, Enrollment  # <-- AJOUT DE Enrollment
from academie.payment_gateways import stripe_gateway, moncash_gateway, paypal_gateway
from academie.permissions import enregistrer_log, role_required
from academie.services.async_tasks import executer_en_arriere_plan
from academie.services.email_service import _envoyer_email

import logging
from django.conf import settings
from django.db.models import F
import stripe
import paypalrestsdk

logger = logging.getLogger('academie')


# ================================================
# Fonction utilitaire (copiée depuis views.py)
# ================================================

def _prix_avec_promotion(formation):
    """Calcule le prix réel en tenant compte des promotions actives."""
    prix_original = Decimal(str(formation.prix))
    for promo in Promotion.objects.filter(actif=True):
        if promo.s_applique_a(formation):
            reduction = prix_original * (Decimal(promo.pourcentage_reduction) / 100)
            return prix_original - reduction, promo
    return prix_original, None


# ================================================
# Vues de paiement
# ================================================

@login_required(login_url="/connexion/")
def initier_achat(request, formation_id):
    """Étape 1 — Crée une commande en attente pour une formation."""
    formation = Formation.objects.get(id=formation_id, actif=True)

    if formation.gratuit:
        messages.info(request, "Cette formation est gratuite — accès direct !")
        return redirect("detail_formation", formation_id=formation.id)

    # Empêche le rachat si déjà débloquée
    deja_debloquee = AccesFormationDebloque.objects.filter(
        utilisateur=request.user, formation=formation
    ).exists()
    if deja_debloquee:
        messages.info(request, "Tu as déjà accès à cette formation !")
        return redirect("detail_formation", formation_id=formation.id)

    prix_final, promo = _prix_avec_promotion(formation)

    with db_transaction.atomic():
        commande = Order.objects.create(
            utilisateur=request.user, sous_total=prix_final, total=prix_final
        )
        OrderItem.objects.create(
            commande=commande,
            formation=formation,
            type_produit="formation",
            nom_produit_snapshot=formation.nom,
            icone_produit_snapshot=formation.icone,
            ecole_nom_snapshot=str(formation.ecole) if formation.ecole else "",
            prix_unitaire=prix_final,
        )
        commande.recalculer_total()

    return redirect("checkout", order_reference=commande.reference)


@login_required(login_url="/connexion/")
def checkout(request, order_reference):
    """Étape 2 — Page de paiement : choix moyen + coupon."""
    commande = Order.objects.prefetch_related("items").get(
        reference=order_reference, utilisateur=request.user
    )

    if request.method == "POST":
        code_coupon = request.POST.get("code_coupon", "").strip().upper()
        moyen_id = request.POST.get("moyen_paiement")

        if code_coupon:
            try:
                coupon = Coupon.objects.get(code=code_coupon)
                valide, message_erreur = coupon.est_valide()
                if valide:
                    commande.coupon_applique = coupon
                    commande.save()
                    commande.recalculer_total()
                    messages.success(request, f"✅ Coupon '{code_coupon}' appliqué !")
                else:
                    messages.error(request, f"❌ {message_erreur}")
            except Coupon.DoesNotExist:
                messages.error(request, "❌ Code coupon invalide.")
            return redirect("checkout", order_reference=order_reference)

        if moyen_id:
            moyen = MoyenPaiement.objects.get(id=moyen_id)
            commande.moyen_paiement = moyen
            commande.save()
            return redirect("confirmer_paiement", order_reference=order_reference)

    moyens_paiement = MoyenPaiement.objects.filter(actif=True)
    return render(
        request,
        "academie/checkout.html",
        {
            "commande": commande,
            "moyens_paiement": moyens_paiement,
        },
    )


@login_required(login_url="/connexion/")
def confirmer_paiement(request, order_reference):
    """Étape 3 — Confirmation : paiement manuel ou redirection externe."""
    commande = Order.objects.get(reference=order_reference, utilisateur=request.user)

    if request.method == "POST":
        preuve = request.FILES.get("preuve_paiement")
        reference_externe = request.POST.get("reference_externe", "")

        with db_transaction.atomic():
            Transaction.objects.create(
                commande=commande,
                moyen_paiement=commande.moyen_paiement,
                reference_externe=reference_externe,
                preuve_paiement=preuve,
                montant=commande.total,
                statut="en_verification" if commande.moyen_paiement.code == "manuel" else "initiee",
            )

        messages.success(
            request,
            "✅ Paiement soumis ! Notre équipe valide généralement sous 24h. "
            "Tu recevras un email de confirmation dès validation.",
        )
        return redirect("mes_commandes")

    return render(request, "academie/confirmer_paiement.html", {"commande": commande})


@login_required(login_url="/connexion/")
def mes_commandes(request):
    """Dashboard étudiant — Mes commandes/factures/remboursements."""
    commandes = Order.objects.filter(utilisateur=request.user).prefetch_related("items", "facture")
    return render(request, "academie/mes_commandes.html", {"commandes": commandes})


@login_required(login_url="/connexion/")
def rediriger_paiement_externe(request, order_reference):
    """Route vers la bonne passerelle selon le moyen choisi."""
    commande = Order.objects.get(reference=order_reference, utilisateur=request.user)
    code_moyen = commande.moyen_paiement.code

    url_succes = request.build_absolute_uri(f"/paiement-succes/{order_reference}/")
    url_annulation = request.build_absolute_uri(f"/checkout/{order_reference}/")

    if code_moyen == "stripe":
        url, session_id = stripe_gateway.creer_session_paiement(
            commande, url_succes, url_annulation
        )
        if url:
            Transaction.objects.create(
                commande=commande,
                moyen_paiement=commande.moyen_paiement,
                reference_externe=session_id,
                montant=commande.total,
                statut="initiee",
            )
            return redirect(url)
        messages.error(request, f"Erreur Stripe : {session_id}")

    elif code_moyen == "moncash":
        url, erreur = moncash_gateway.creer_paiement(commande)
        if url:
            return redirect(url)
        messages.error(request, erreur)

    elif code_moyen == "paypal":
        url, payment_id = paypal_gateway.creer_paiement(commande, url_succes, url_annulation)
        if url:
            Transaction.objects.create(
                commande=commande,
                moyen_paiement=commande.moyen_paiement,
                reference_externe=payment_id,
                montant=commande.total,
                statut="initiee",
            )
            return redirect(url)
        messages.error(request, "Erreur PayPal")

    return redirect("confirmer_paiement", order_reference=order_reference)



@login_required(login_url='/connexion/')
def paiement_succes(request, order_reference):
    """
    Page de retour après paiement externe — vérification active auprès du prestataire.
    """
    from ..models import Order, Coupon, Invoice, Transaction
    from ..payment_gateways import moncash_gateway

    commande = Order.objects.select_related('moyen_paiement').get(
        reference=order_reference, utilisateur=request.user
    )

    if commande.statut == 'paye':
        messages.success(request, "✅ Paiement déjà confirmé — accès débloqué.")
        return redirect('mes_commandes')

    code_moyen = commande.moyen_paiement.code if commande.moyen_paiement else None
    transaction_recente = commande.transactions.order_by('-date_creation').first()
    paiement_verifie = False
    erreur_verification = None

    if code_moyen == 'stripe' and transaction_recente:
        try:
            stripe.api_key = settings.STRIPE_SECRET_KEY
            session = stripe.checkout.Session.retrieve(transaction_recente.reference_externe)
            paiement_verifie = (session.payment_status == 'paid')
        except Exception as e:
            erreur_verification = str(e)

    elif code_moyen == 'moncash' and transaction_recente:
        try:
            paiement_verifie, _ = moncash_gateway.verifier_transaction(commande.reference)
        except Exception as e:
            erreur_verification = str(e)

    elif code_moyen == 'paypal' and transaction_recente:
        try:
            paypalrestsdk.configure({
                'mode': settings.PAYPAL_MODE,
                'client_id': settings.PAYPAL_CLIENT_ID,
                'client_secret': settings.PAYPAL_CLIENT_SECRET,
            })
            payment = paypalrestsdk.Payment.find(transaction_recente.reference_externe)
            paiement_verifie = (payment.state == 'approved')
        except Exception as e:
            erreur_verification = str(e)

    else:
        erreur_verification = "Aucune transaction vérifiable associée à cette commande."

    if not paiement_verifie:
        logger.warning(
            f"⚠️ Tentative de validation paiement NON vérifiée — commande {commande.reference}, "
            f"utilisateur {request.user.username}, erreur: {erreur_verification}"
        )
        messages.error(
            request,
            "⏳ Ton paiement est en cours de vérification. Si le débit a bien eu lieu, "
            "l'accès sera débloqué automatiquement sous quelques minutes."
        )
        return redirect('mes_commandes')

    # ================================================
    # DÉTECTION DE FRAUDE AVANT VALIDATION DÉFINITIVE
    # ================================================
    adresse_ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', ''))
    alertes_detectees = detecter_fraude_potentielle(commande, adresse_ip)

    for niveau, raison in alertes_detectees:
        AlerteFraude.objects.create(commande=commande, niveau=niveau, raison=raison)
        if niveau == 'eleve':
            logger.warning(f"🚨 ALERTE FRAUDE ÉLEVÉE — commande {commande.reference} : {raison}")

    with db_transaction.atomic():
        commande.statut = 'paye'
        commande.date_paiement = timezone.now()
        commande.save()

        if transaction_recente:
            transaction_recente.statut = 'reussie'
            transaction_recente.save()

        # ========================================================
        # REMPLACEMENT : AccesFormationDebloque -> Enrollment.inscrire()
        # ========================================================
        for item in commande.items.select_related('formation').all():
            if item.formation:
                Enrollment.inscrire(
                    commande.utilisateur,
                    item.formation,
                    origine='achat',
                    commande_origine=commande
                )

        Invoice.objects.get_or_create(commande=commande)

        # ===== CORRECTIF : Utilisation atomique du coupon =====
        if commande.coupon_applique:
            succes, msg = commande.coupon_applique.utiliser_atomiquement()
            if not succes:
                logger.warning(f"Échec coupon : {msg}")

    messages.success(request, "🎉 Paiement confirmé ! Accès débloqué immédiatement.")
    return redirect('mes_commandes')


@csrf_exempt
def stripe_webhook(request):
    """Endpoint webhook Stripe — confirmation asynchrone officielle."""
    from academie.payment_gateways.stripe_gateway import traiter_webhook

    event = traiter_webhook(request.body, request.META.get('HTTP_STRIPE_SIGNATURE'))

    if event and event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        reference = session.get('client_reference_id')
        try:
            commande = Order.objects.get(reference=reference)
            if commande.statut != 'paye':
                commande.statut = 'paye'
                commande.date_paiement = timezone.now()
                commande.save()
                # ========================================================
                # REMPLACEMENT : AccesFormationDebloque -> Enrollment.inscrire()
                # ========================================================
                for item in commande.items.all():
                    if item.formation:
                        Enrollment.inscrire(
                            commande.utilisateur,
                            item.formation,
                            origine='achat',
                            commande_origine=commande
                        )
                Invoice.objects.get_or_create(commande=commande)
        except Order.DoesNotExist:
            pass

    return HttpResponse(status=200)