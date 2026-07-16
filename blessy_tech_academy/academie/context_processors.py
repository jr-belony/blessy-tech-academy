from .models import Notification

def notifications_non_lues(request):
    if request.user.is_authenticated:
        nb = Notification.objects.filter(utilisateur=request.user, lue=False).count()
        return {'nb_notifications': nb}
    return {'nb_notifications': 0}


def academie_courante(request):
    """Rend request.academie_courante disponible dans tous les templates sans passer par chaque vue."""
    return {'academie_courante': getattr(request, 'academie_courante', None)}