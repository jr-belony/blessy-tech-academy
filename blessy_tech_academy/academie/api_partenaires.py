# ================================================
# API_PARTENAIRES.PY — Utilitaires pour l'API partenaire
# ================================================

from functools import wraps
from rest_framework.response import Response

# ================================================
# Accesseur explicite pour le partenaire
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


# ================================================
# Journalisation des requêtes partenaires (locale)
# ================================================

def journaliser_requete_partenaire(request, partenaire, code_http):
    """
    Journalise un appel API partenaire avec son code HTTP.
    Peut être enrichie pour écrire dans LogAudit ou LogRequetePartenaire.
    """
    print(f"[PARTENAIRE API] {partenaire.nom} - {request.path} - HTTP {code_http}")


# ================================================
# Décorateur : exiger_scope
# ================================================

def exiger_scope(scope_requis):
    """
    Décorateur pour les vues API partenaires.
    Vérifie que le partenaire authentifié possède le scope requis.
    Usage : @exiger_scope('formations.lire')
    """
    def decorateur(methode):
        @wraps(methode)
        def wrapper(self, request, *args, **kwargs):
            partenaire = obtenir_partenaire_depuis_request(request)
            if not partenaire:
                return Response({'erreur': 'Authentification requise'}, status=401)
            if not partenaire.a_le_scope(scope_requis):
                journaliser_requete_partenaire(request, partenaire, 403)
                return Response(
                    {'erreur': f'Scope "{scope_requis}" non autorisé pour ce partenaire.'},
                    status=403
                )
            return methode(self, request, *args, **kwargs)
        return wrapper
    return decorateur