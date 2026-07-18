# ================================================
# ASYNC_TASKS.PY — Exécution asynchrone légère (sans infra Celery)
# Utilisé pour : envoi email, génération PDF, appels IA non bloquants
# Migration future vers Celery : remplacer @executer_en_arriere_plan 
# par @shared_task sans changer la signature des fonctions appelantes
# ================================================

import threading
import logging

logger = logging.getLogger('academie')


def executer_en_arriere_plan(fonction, *args, **kwargs):
    """
    Exécute une fonction dans un thread séparé — la requête HTTP 
    répond immédiatement sans attendre la fin de l'opération.

    Usage : executer_en_arriere_plan(send_certificate_email, user, formation, lien)
    """
    def wrapper():
        try:
            fonction(*args, **kwargs)
        except Exception as e:
            logger.error(f"❌ Erreur tâche asynchrone {fonction.__name__} : {e}")

    thread = threading.Thread(target=wrapper, daemon=True)
    thread.start()
    return thread