# ================================================
# DECORATORS.PY — CORRECTIF CRITIQUE : Décorateur d'accès centralisé
# ================================================

from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def exiger_acces_formation(recuperer_formation):
    """
    Décorateur générique — bloque l'accès si l'utilisateur n'a pas 
    payé/débloqué la formation associée à l'objet demandé (leçon, 
    quiz, examen, certificat...).

    Usage :
        @exiger_acces_formation(lambda lecon_id: Lecon.objects.get(id=lecon_id).module.formation)
        def lire_lecon(request, lecon_id): ...
    """
    def decorateur(vue_func):
        @wraps(vue_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, "🔐 Connecte-toi pour accéder à ce contenu.")
                return redirect('connexion')

            try:
                formation = recuperer_formation(*args, **kwargs)
            except Exception:
                messages.error(request, "❌ Contenu introuvable.")
                return redirect('formations')

            from .views_modules.learning_views import verifier_acces_formation
            if not verifier_acces_formation(request.user, formation):
                messages.error(
                    request,
                    "🔒 Tu dois avoir accès à cette formation pour consulter ce contenu."
                )
                return redirect('detail_formation', formation_id=formation.id)

            return vue_func(request, *args, **kwargs)
        return wrapper
    return decorateur