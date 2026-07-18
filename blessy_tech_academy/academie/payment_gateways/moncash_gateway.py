# ================================================
# PAYMENT_GATEWAYS/MONCASH_GATEWAY.PY
# API officielle MonCash Digicel (REST + OAuth2)
# Variables Railway requises : MONCASH_CLIENT_ID, MONCASH_CLIENT_SECRET,
#                               MONCASH_MODE (sandbox|live)
# Documentation : https://moncashbutton.digicelgroup.com/Moncash-doc/
# ================================================

import requests
from django.conf import settings

BASE_URLS = {
    "sandbox": "https://sandbox.moncashbutton.digicelgroup.com/Api",
    "live": "https://moncashbutton.digicelgroup.com/Api",
}


def _obtenir_token():
    """Récupère un token OAuth2 MonCash."""
    mode = getattr(settings, "MONCASH_MODE", "sandbox")
    url = f"{BASE_URLS[mode]}/oauth/token"

    response = requests.post(
        url,
        data={
            "grant_type": "client_credentials",
            "scope": "read,write",
        },
        auth=(settings.MONCASH_CLIENT_ID, settings.MONCASH_CLIENT_SECRET),
    )

    if response.status_code == 200:
        return response.json().get("access_token")
    return None


def creer_paiement(commande):
    """Crée une transaction de paiement MonCash — retourne l'URL de redirection."""
    token = _obtenir_token()
    if not token:
        return None, "Impossible de s'authentifier auprès de MonCash."

    mode = getattr(settings, "MONCASH_MODE", "sandbox")
    url = f"{BASE_URLS[mode]}/v1/CreatePayment"

    response = requests.post(
        url,
        json={"amount": float(commande.total), "orderId": commande.reference},
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )

    if response.status_code in (200, 202):
        redirect_url = f"{BASE_URLS[mode]}/v1/redirect?token={token}"
        return redirect_url, None
    return None, f"Erreur MonCash : {response.text}"


def verifier_transaction(order_reference):
    """Vérifie le statut d'une transaction MonCash via orderId."""
    token = _obtenir_token()
    if not token:
        return False, None

    mode = getattr(settings, "MONCASH_MODE", "sandbox")
    url = f"{BASE_URLS[mode]}/v1/RetrieveTransactionPayment"

    response = requests.post(
        url, json={"orderId": order_reference}, headers={"Authorization": f"Bearer {token}"}
    )

    if response.status_code == 200:
        data = response.json().get("payment", {})
        return data.get("message") == "successful", data.get("transaction_id")
    return False, None
