# ================================================
# PAYMENT_GATEWAYS/PAYPAL_GATEWAY.PY
# Nécessite : pip install paypalrestsdk
# Variables Railway requises : PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET,
#                               PAYPAL_MODE (sandbox|live)
# ================================================

import paypalrestsdk
from django.conf import settings

paypalrestsdk.configure(
    {
        "mode": getattr(settings, "PAYPAL_MODE", "sandbox"),
        "client_id": getattr(settings, "PAYPAL_CLIENT_ID", ""),
        "client_secret": getattr(settings, "PAYPAL_CLIENT_SECRET", ""),
    }
)


def creer_paiement(commande, url_succes, url_annulation):
    """Crée un paiement PayPal et retourne l'URL d'approbation."""
    payment = paypalrestsdk.Payment(
        {
            "intent": "sale",
            "payer": {"payment_method": "paypal"},
            "redirect_urls": {"return_url": url_succes, "cancel_url": url_annulation},
            "transactions": [
                {
                    "item_list": {
                        "items": [
                            {
                                "name": item.nom_produit_snapshot,
                                "sku": str(item.id),
                                "price": str(item.prix_unitaire),
                                "currency": "USD",
                                "quantity": 1,
                            }
                            for item in commande.items.all()
                        ]
                    },
                    "amount": {"total": str(commande.total), "currency": "USD"},
                    "description": f"Commande {commande.reference} — Blessy Tech Academy",
                }
            ],
        }
    )

    if payment.create():
        for link in payment.links:
            if link.rel == "approval_url":
                return link.href, payment.id
    return None, payment.error


def executer_paiement(payment_id, payer_id):
    """Finalise un paiement PayPal après approbation utilisateur."""
    payment = paypalrestsdk.Payment.find(payment_id)
    if payment.execute({"payer_id": payer_id}):
        return True
    return False
