# ================================================
# SERVICES/PUSH_SERVICE.PY — Notifications Push (Firebase Cloud Messaging)
# Prêt à être utilisé avec executer_en_arriere_plan()
# ================================================

import logging

logger = logging.getLogger('academie')


def envoyer_push(utilisateur, titre, message, lien, categorie='general'):
    """
    Envoie une notification push à un utilisateur via Firebase Cloud Messaging.
    Pour l'instant, cette fonction est un placeholder — elle logge simplement
    la notification. Elle sera connectée à Firebase ultérieurement.
    """
    logger.info(f"📲 [PUSH] {utilisateur.username} — {titre} : {message}")
    # TODO: Intégrer Firebase Admin SDK pour envoyer une vraie notification push
    pass