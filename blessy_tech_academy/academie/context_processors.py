from .models import Notification

def notifications_non_lues(request):
    if request.user.is_authenticated:
        nb = Notification.objects.filter(utilisateur=request.user, lue=False).count()
        return {'nb_notifications': nb}
    return {'nb_notifications': 0}