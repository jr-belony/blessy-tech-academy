# ================================================
# PAYMENT_GATEWAYS/NATCASH_GATEWAY.PY
# NatCash n'a pas d'API publique standardisée comme MonCash.
# Structure prête pour intégration dès que Natcom fournit leurs
# identifiants d'API (contact : partenariat.natcom@natcom.ht)
# En attendant : fonctionne en mode "manuel avec référence"
# ================================================


def creer_paiement(commande):
    """
    Mode transitoire : redirige vers le flux manuel existant
    (upload preuve + validation admin) en attendant l'API officielle.
    """
    return None, "NatCash : en attente d'accès API — utilise le paiement manuel pour l'instant."
