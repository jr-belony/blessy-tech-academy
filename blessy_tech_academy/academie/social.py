"""
Module de partage automatique des formations sur les réseaux sociaux.
En attendant les tokens définitifs, les fonctions affichent le message
dans les logs Django. Pour activer le partage réel, décommentez les
appels API correspondants.
"""
import logging

logger = logging.getLogger(__name__)


def generer_message_partage(formation):
    """Génère un message de partage pour une formation."""
    if formation.message_partage:
        return formation.message_partage
    return (
        f"🚀 Nouvelle formation chez Blessy Tech Academy : {formation.nom} !\n"
        f"📚 {formation.description[:100]}...\n"
        f"⏱ {formation.duree_mois} mois | 💰 {formation.prix} USD\n"
        f"👉 Rejoins-nous : https://blessytechacademy.com/formations/{formation.id}/"
    )


def partager_formation(formation):
    """
    Partage une formation sur les réseaux sociaux configurés.
    Actuellement simulé (logs). Active les appels API quand les tokens
    seront disponibles.
    """
    message = generer_message_partage(formation)
    logger.info(f"📢 [SIMULATION] Partage de la formation '{formation.nom}' : {message}")

    # --- Facebook (à activer quand le token sera prêt) ---
    # import requests
    # url = f"https://graph.facebook.com/{PAGE_ID}/feed"
    # params = {
    #     "message": message,
    #     "access_token": FACEBOOK_PAGE_TOKEN,
    # }
    # response = requests.post(url, params=params)
    # if response.status_code == 200:
    #     logger.info("✅ Partagé sur Facebook avec succès.")
    # else:
    #     logger.error(f"❌ Erreur Facebook : {response.text}")

    # --- Twitter (à activer plus tard) ---
    # import tweepy
    # client = tweepy.Client(
    #     consumer_key=...,
    #     consumer_secret=...,
    #     access_token=...,
    #     access_token_secret=...,
    # )
    # client.create_tweet(text=message[:280])
    # logger.info("✅ Partagé sur Twitter avec succès.")

    return message