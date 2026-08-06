"""
Signaux Django pour Blessy Tech Academy.
- Compression automatique des images uploadées (ProjetEtudiant, Formation)
- Détection des connexions suspectes et historique des connexions
- Auto-création ProfilUtilisateur et WorkflowFormation
- Invalidation du cache progression (ProgressionLecon)
- Invalidation du cache catalogue (Formation) par versionnage
"""

import os
import logging
from io import BytesIO

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.signals import user_logged_in
from django.core.cache import cache
from django.core.files.base import ContentFile
from django.core.mail import send_mail
from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from PIL import Image

from .models import (
    ConnexionUtilisateur,
    ProjetEtudiant,
    Enrollment,
    Formation,
    ProgressionLecon,
    AccesFormationDebloque,
)

logger = logging.getLogger('academie')

TAILLE_MAX = (1200, 1200)
QUALITE_JPEG = 82


# ================================================
# FONCTION UTILITAIRE : Compression d'image
# ================================================
def compresser_image(image_field, taille_max=TAILLE_MAX, qualite=QUALITE_JPEG):
    """
    Redimensionne et compresse une image en mémoire.
    Retourne un ContentFile prêt à être sauvegardé, ou None si erreur.
    """
    try:
        img = Image.open(image_field)

        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        img.thumbnail(taille_max, Image.Resampling.LANCZOS)

        buffer = BytesIO()
        img.save(buffer, format="JPEG", quality=qualite, optimize=True)
        buffer.seek(0)

        nom_original = os.path.splitext(image_field.name)[0]
        nouveau_nom = f"{nom_original}.jpg"

        return ContentFile(buffer.read(), name=nouveau_nom)

    except Exception:
        return None


# ================================================
# SIGNAL : pre_save (ProjetEtudiant)
# ================================================
@receiver(pre_save, sender=ProjetEtudiant)
def compresser_image_projet(sender, instance, **kwargs):
    if not instance.image:
        return

    if instance.pk:
        try:
            ancien = ProjetEtudiant.objects.get(pk=instance.pk)
            if ancien.image == instance.image:
                return
        except ProjetEtudiant.DoesNotExist:
            pass

    if hasattr(instance.image, "file"):
        image_compressee = compresser_image(instance.image)
        if image_compressee:
            instance.image.save(image_compressee.name, image_compressee, save=False)


# ================================================
# SIGNAL : pre_save (Formation)
# ================================================
@receiver(pre_save, sender=Formation)
def compresser_illustration_formation(sender, instance, **kwargs):
    if not instance.illustration:
        return

    if instance.pk:
        try:
            ancien = Formation.objects.get(pk=instance.pk)
            if ancien.illustration == instance.illustration:
                return
        except Formation.DoesNotExist:
            pass

    if hasattr(instance.illustration, "file"):
        image_compressee = compresser_image(instance.illustration, taille_max=(1600, 900))
        if image_compressee:
            instance.illustration.save(image_compressee.name, image_compressee, save=False)


# ================================================
# SIGNAL : user_logged_in (version sécurisée, sans géolocalisation externe)
# ================================================
@receiver(user_logged_in)
def enregistrer_connexion(sender, request, user, **kwargs):
    """
    Enregistre la connexion de l'utilisateur avec IP et navigateur.
    Aucun appel externe (ip-api.com) – conforme RGPD.
    """
    ip = request.META.get("HTTP_X_FORWARDED_FOR", request.META.get("REMOTE_ADDR", ""))
    if ip:
        ip = ip.split(",")[0].strip()
    if not ip:
        ip = "0.0.0.0"

    user_agent = request.META.get("HTTP_USER_AGENT", "")[:300]

    # Journalisation locale
    logger.info(f"Connexion de {user.username} depuis IP {ip}")

    # Détection suspecte basée uniquement sur l'IP (pas de pays/ville)
    derniere = (
        ConnexionUtilisateur.objects.filter(utilisateur=user).order_by("-date_connexion").first()
    )
    suspecte = False
    if derniere and derniere.adresse_ip != ip:
        suspecte = True

    # Création de l'enregistrement (pays et ville vides)
    ConnexionUtilisateur.objects.create(
        utilisateur=user,
        adresse_ip=ip,
        navigateur=user_agent,
        pays="",      # plus de géolocalisation externe
        ville="",
        suspecte=suspecte,
    )

    # Email d'alerte en cas de suspect (conserve la logique)
    if suspecte and user.email:
        try:
            send_mail(
                subject="🔐 Nouvelle connexion détectée sur votre compte BTA",
                message=(
                    f"Bonjour {user.first_name or user.username},\n\n"
                    f"Une nouvelle connexion à votre compte Blessy Tech Academy a été détectée :\n\n"
                    f"📍 Adresse IP : {ip}\n"
                    f"🖥️ Navigateur : {user_agent[:100]}\n\n"
                    f"Si vous n'êtes pas à l'origine de cette connexion, changez immédiatement votre mot de passe.\n\n"
                    f"L'équipe BTA"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True,
            )
        except Exception:
            pass


# ================================================
# SIGNAL — Auto-création ProfilUtilisateur à l'inscription
# ================================================

@receiver(post_save, sender=User)
def creer_profil_utilisateur(sender, instance, created, **kwargs):
    """Crée automatiquement un ProfilUtilisateur pour chaque nouveau User."""
    if created:
        from .models import ProfilUtilisateur

        ProfilUtilisateur.objects.get_or_create(utilisateur=instance, defaults={"role": "etudiant"})


# ================================================
# SIGNAL — Auto-création WorkflowFormation
# ================================================
@receiver(post_save, sender=Formation)
def creer_workflow_formation(sender, instance, created, **kwargs):
    """Crée automatiquement un WorkflowFormation pour chaque nouvelle Formation."""
    if created:
        from .models import WorkflowFormation

        WorkflowFormation.objects.get_or_create(
            formation=instance, defaults={"etat_actuel": "brouillon"}
        )


# ================================================
# SIGNAL — Invalidation cache progression (leçon terminée)
# ================================================
@receiver(post_save, sender=ProgressionLecon)
def invalider_cache_progression(sender, instance, **kwargs):
    """Vide le cache de progression dès qu'une leçon est marquée terminée."""
    formation = instance.lecon.module.formation
    cache_key = f"progression_formation_{formation.id}_user_{instance.utilisateur.id}"
    cache.delete(cache_key)


# ================================================
# SIGNAL — Invalidation cache catalogue formations (versionnage)
# ================================================
@receiver(post_save, sender=Formation)
@receiver(post_delete, sender=Formation)
def invalider_cache_catalogue_formations(sender, **kwargs):
    """Invalide le cache du catalogue dès qu'une formation est modifiée/supprimée."""
    version_actuelle = cache.get('formations_cache_version', 1)
    cache.set('formations_cache_version', version_actuelle + 1, None)  # jamais expiré


# ================================================
# SIGNAL — Synchronisation Enrollment → AccesFormationDebloque
# ================================================
@receiver(post_save, sender=Enrollment)
def synchroniser_acces_formation(sender, instance, created, **kwargs):
    """
    Crée ou met à jour AccesFormationDebloque lors d'une nouvelle inscription.
    Assure la rétrocompatibilité : tout utilisateur inscrit via Enrollment
    obtient automatiquement son accès technique dérivé.
    """
    # On ne crée l'accès que si l'inscription est active (statut='actif')
    if instance.statut == 'actif':
        acces, _ = AccesFormationDebloque.objects.get_or_create(
            utilisateur=instance.utilisateur,
            formation=instance.formation,
            defaults={
                'nom_formation_snapshot': instance.formation.nom,
                'commande_origine': instance.commande_origine,
            }
        )
        # Si l'accès existait déjà mais était lié à une commande différente,
        # on peut éventuellement mettre à jour la commande_origine si elle est
        # plus récente ou si elle était nulle. (Optionnel, selon votre logique métier)
        if acces.commande_origine is None and instance.commande_origine:
            acces.commande_origine = instance.commande_origine
            acces.save()