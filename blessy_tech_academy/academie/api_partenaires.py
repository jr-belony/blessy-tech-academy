# ================================================
# API_PARTENAIRES.PY — CORRECTIF : clarification request.user
# L'audit signale : "request.user peut être remplacé par un objet 
# PartenaireAPI, source de confusion" — DRF fait ça par design 
# (authenticate() retourne (user, auth)), mais on documente et 
# sécurise explicitement pour éviter toute confusion future
# ================================================

def obtenir_partenaire_depuis_request(request):
    """
    Accesseur explicite — à utiliser dans TOUTES les vues API 
    partenaires au lieu de 'request.user' directement, pour éviter 
    toute ambiguïté avec un vrai User Django.
    Retourne None si la requête n'est pas authentifiée via clé API partenaire.
    """
    from .models import PartenaireAPI
    if isinstance(request.user, PartenaireAPI):
        return request.user
    return None