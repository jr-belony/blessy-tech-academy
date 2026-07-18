"""
================================================
EMAIL_SERVICE.PY — Couche centralisée d'envoi d'emails BTA
================================================
Toutes les vues du projet DOIVENT passer par ce module.
Changer de provider (SMTP → Brevo/Mailgun/SES/Resend) ne nécessite
AUCUNE modification des vues — uniquement settings.py.
"""

import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

logger = logging.getLogger("bta_emails")


# ================================================
# FONCTION CŒUR — Envoi générique
# ================================================
def _envoyer_email(template_path, contexte, destinataire, sujet, from_email=None):
    """
    Fonction interne : rend un template HTML et l'envoie.
    Toutes les fonctions publiques ci-dessous l'utilisent.
    """
    try:
        contexte.setdefault("site_url", getattr(settings, "SITE_URL", ""))
        html_content = render_to_string(template_path, contexte)

        email = EmailMultiAlternatives(
            subject=sujet,
            body=f"{sujet} — Ouvre cet email dans un client compatible HTML.",
            from_email=from_email or settings.DEFAULT_FROM_EMAIL,
            to=[destinataire],
        )
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)

        logger.info(f"✅ Email envoyé : {template_path} → {destinataire}")
        return True

    except Exception as e:
        logger.error(f"❌ Échec envoi email {template_path} → {destinataire} : {e}")
        return False


# ================================================
# EMAIL — Bienvenue
# ================================================
def send_welcome_email(user):
    return _envoyer_email(
        "emails/notifications/welcome.html",
        {
            "prenom": user.first_name or user.username,
            "lien_dashboard": f"{settings.SITE_URL}/dashboard/",
        },
        destinataire=user.email,
        sujet="🎉 Bienvenue chez Blessy Tech Academy !",
        from_email=settings.EMAIL_ADMISSIONS,
    )


# ================================================
# EMAIL — Certificat obtenu
# ================================================
def send_certificate_email(user, formation, lien_certificat):
    return _envoyer_email(
        "emails/notifications/certificate.html",
        {
            "prenom": user.first_name or user.username,
            "formation_nom": formation.nom,
            "lien_certificat": lien_certificat,
        },
        destinataire=user.email,
        sujet=f"🎓 Félicitations ! Ton certificat {formation.nom} est prêt",
        from_email=settings.EMAIL_CERTIFICATS,
    )


# ================================================
# EMAIL — Badge débloqué
# ================================================
def send_badge_email(user, badge):
    return _envoyer_email(
        "emails/notifications/badge.html",
        {
            "prenom": user.first_name or user.username,
            "badge_nom": badge.get_type_badge_display(),
            "badge_icone": "🏅",
            "lien_classement": f"{settings.SITE_URL}/forum/membres/",
        },
        destinataire=user.email,
        sujet=f"🏅 Nouveau badge débloqué : {badge.get_type_badge_display()}",
        from_email=settings.EMAIL_NOREPLY,
    )


# ================================================
# EMAIL — Résultat de quiz
# ================================================
def send_quiz_result_email(user, resultat_quiz):
    pourcentage = resultat_quiz.pourcentage()
    message = (
        "🎉 Excellent travail !"
        if pourcentage >= 70
        else (
            "👍 Continue tes efforts !"
            if pourcentage >= 50
            else "💪 Retente le quiz après avoir révisé !"
        )
    )
    return _envoyer_email(
        "emails/notifications/quiz_result.html",
        {
            "prenom": user.first_name or user.username,
            "quiz_titre": resultat_quiz.quiz.titre,
            "score_texte": f"{resultat_quiz.score}/{resultat_quiz.total_questions}",
            "pourcentage_texte": f"{pourcentage}%",
            "message_feedback": message,
            "lien_formation": f"{settings.SITE_URL}/formation/{resultat_quiz.quiz.formation.id}/",
        },
        destinataire=user.email,
        sujet=f"📝 Résultat de ton quiz — {resultat_quiz.quiz.titre}",
        from_email=settings.EMAIL_FORMATIONS,
    )


# ================================================
# EMAIL — Réinitialisation mot de passe
# ================================================
def send_reset_password_email(user, lien_reset):
    return _envoyer_email(
        "emails/notifications/reset_password.html",
        {
            "prenom": user.first_name or user.username,
            "lien_reset": lien_reset,
        },
        destinataire=user.email,
        sujet="🔐 Réinitialise ton mot de passe Blessy Tech Academy",
        from_email=settings.EMAIL_SUPPORT,
    )


# ================================================
# EMAIL — Réponse forum
# ================================================
def send_forum_reply_email(destinataire_user, auteur_reponse, sujet_obj, extrait):
    return _envoyer_email(
        "emails/notifications/forum_reply.html",
        {
            "auteur_reponse": auteur_reponse,
            "sujet_titre": sujet_obj.titre,
            "extrait_reponse": extrait[:200],
            "lien_sujet": f"{settings.SITE_URL}/forum/{sujet_obj.id}/",
        },
        destinataire=destinataire_user.email,
        sujet=f"💬 {auteur_reponse} a répondu à ton sujet",
        from_email=settings.EMAIL_NOREPLY,
    )


# ================================================
# NEWSLETTER — Envoi groupé (segmentation basique)
# ================================================
def send_newsletter(destinataires_emails, sujet, template_path, contexte):
    """
    Envoie une newsletter à une liste de destinataires.
    destinataires_emails : liste d'adresses email (queryset.values_list('email', flat=True))
    """
    resultats = {"envoyes": 0, "echecs": 0}
    for email_dest in destinataires_emails:
        succes = _envoyer_email(
            template_path,
            contexte.copy(),
            destinataire=email_dest,
            sujet=sujet,
            from_email=settings.EMAIL_NEWSLETTER,
        )
        resultats["envoyes" if succes else "echecs"] += 1
    return resultats
