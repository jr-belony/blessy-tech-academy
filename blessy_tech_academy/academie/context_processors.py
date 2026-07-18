from .models import Notification


def notifications_non_lues(request):
    if request.user.is_authenticated:
        nb = Notification.objects.filter(utilisateur=request.user, lue=False).count()
        return {"nb_notifications": nb}
    return {"nb_notifications": 0}


def academie_courante(request):
    """Rend l'Academie courante ET ses couleurs disponibles dans tous les templates."""
    academie = getattr(request, "academie_courante", None)
    return {
        "academie_courante": academie,
        "couleur_principale_dynamique": academie.couleur_principale if academie else "#0B2447",
        "couleur_accent_dynamique": academie.couleur_accent if academie else "#00B4D8",
    }
