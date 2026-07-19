# ================================================
# PAYMENT_GATEWAYS/STRIPE_GATEWAY.PY
# Nécessite : pip install stripe
# Variables Railway requises : STRIPE_SECRET_KEY, STRIPE_PUBLIC_KEY, 
#                               STRIPE_WEBHOOK_SECRET
# ================================================

import stripe
from django.conf import settings

stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', '')


def creer_session_paiement(commande, url_succes, url_annulation):
    """Crée une session Stripe Checkout pour une commande unique."""
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {'name': item.nom_produit_snapshot},
                    'unit_amount': int(item.prix_unitaire * 100),
                },
                'quantity': 1,
            } for item in commande.items.all()],
            mode='payment',
            success_url=url_succes,
            cancel_url=url_annulation,
            client_reference_id=commande.reference,
            customer_email=commande.utilisateur.email,
        )
        return session.url, session.id
    except Exception as e:
        return None, str(e)


def creer_abonnement_stripe(user, plan, url_succes, url_annulation):
    """Crée une session Stripe pour un abonnement récurrent."""
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{'price': plan.stripe_price_id, 'quantity': 1}],
            mode='subscription',
            success_url=url_succes,
            cancel_url=url_annulation,
            customer_email=user.email,
        )
        return session.url, session.id
    except Exception as e:
        return None, str(e)


def charger_renouvellement(abonnement):
    """Vérifie le statut du renouvellement automatique via l'API Stripe."""
    try:
        sub = stripe.Subscription.retrieve(abonnement.stripe_subscription_id)
        return sub.status == 'active'
    except Exception:
        return False


def traiter_webhook(payload, sig_header):
    """Traite les événements webhook Stripe (paiement confirmé, échec, etc.)."""
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
        return event
    except Exception as e:
        return None