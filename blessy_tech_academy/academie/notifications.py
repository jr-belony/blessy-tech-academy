"""Fonctions utilitaires pour créer des notifications."""

from .models import Notification


def creer_notification(utilisateur, titre, message, lien=""):
    """Crée une notification pour un utilisateur."""
    if not utilisateur or not utilisateur.is_authenticated:
        return None
    return Notification.objects.create(
        utilisateur=utilisateur,
        titre=titre,
        message=message,
        lien=lien,
    )


def notifier_badge(utilisateur, type_badge):
    """Notification quand un badge est débloqué."""
    from .models import BadgeForum

    badges_dict = dict(BadgeForum.TYPES_BADGES)
    nom_badge = badges_dict.get(type_badge, type_badge)
    creer_notification(
        utilisateur,
        "🏅 Nouveau badge !",
        f"Tu as débloqué le badge : {nom_badge}. Continue comme ça !",
        "/dashboard/",
    )


def notifier_reponse_forum(utilisateur, sujet_titre, sujet_id):
    """Notification quand quelqu'un répond à un sujet."""
    creer_notification(
        utilisateur,
        "💬 Nouvelle réponse sur le forum",
        f'Quelqu\'un a répondu à ton sujet "{sujet_titre}".',
        f"/forum/{sujet_id}/",
    )


def notifier_quiz_reussi(utilisateur, quiz_titre, score, total):
    """Notification quand un quiz est réussi avec un bon score."""
    pourcentage = round((score / total) * 100) if total > 0 else 0
    if pourcentage >= 70:
        creer_notification(
            utilisateur,
            "📝 Quiz réussi !",
            f'Tu as obtenu {score}/{total} ({pourcentage}%) au quiz "{quiz_titre}".',
            "/dashboard/",
        )


def notifier_formation_completee(utilisateur, formation_nom):
    """Notification quand une formation est terminée à 100%."""
    creer_notification(
        utilisateur,
        "🎓 Formation complétée !",
        f'Félicitations, tu as terminé la formation "{formation_nom}". Télécharge ton certificat !',
        "/dashboard/",
    )
