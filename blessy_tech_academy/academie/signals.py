"""
Signaux Django pour Blessy Tech Academy.
- Compression automatique des images uploadées (ProjetEtudiant, Formation)
- Détection des connexions suspectes et historique des connexions
"""

import os
from io import BytesIO

import requests
from django.conf import settings
from django.contrib.auth.signals import user_logged_in
from django.core.files.base import ContentFile
from django.core.mail import send_mail
from django.db.models.signals import pre_save
from django.dispatch import receiver
from PIL import Image
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from .models import ConnexionUtilisateur, Formation, ProjetEtudiant

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

        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')

        img.thumbnail(taille_max, Image.Resampling.LANCZOS)

        buffer = BytesIO()
        img.save(buffer, format='JPEG', quality=qualite, optimize=True)
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

    if hasattr(instance.image, 'file'):
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

    if hasattr(instance.illustration, 'file'):
        image_compressee = compresser_image(instance.illustration, taille_max=(1600, 900))
        if image_compressee:
            instance.illustration.save(image_compressee.name, image_compressee, save=False)


# ================================================
# FONCTION UTILITAIRE : Géolocalisation IP
# ================================================
def get_geo_info(ip):
    try:
        response = requests.get(f'http://ip-api.com/json/{ip}', timeout=3)
        if response.status_code == 200:
            data = response.json()
            return data.get('country', ''), data.get('city', '')
    except Exception:
        pass
    return '', ''


# ================================================
# SIGNAL : user_logged_in
# ================================================
@receiver(user_logged_in)
def enregistrer_connexion(sender, request, user, **kwargs):
    # Correction : IP par défaut '0.0.0.0' si aucune IP réelle n'est trouvée
    ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', '0.0.0.0')).split(',')[0].strip()
    if not ip:
        ip = '0.0.0.0'
    user_agent = request.META.get('HTTP_USER_AGENT', '')[:300]
    pays, ville = get_geo_info(ip)

    derniere = ConnexionUtilisateur.objects.filter(utilisateur=user).order_by('-date_connexion').first()
    suspecte = False
    if derniere and (derniere.pays != pays or derniere.adresse_ip != ip):
        suspecte = True

    ConnexionUtilisateur.objects.create(
        utilisateur=user,
        adresse_ip=ip,
        navigateur=user_agent,
        pays=pays,
        ville=ville,
        suspecte=suspecte,
    )

    # === Email d'alerte (protégé) ===
    if suspecte and user.email:
        try:
            send_mail(
                subject='🔐 Nouvelle connexion détectée sur votre compte BTA',
                message=(
                    f'Bonjour {user.first_name or user.username},\n\n'
                    f'Une nouvelle connexion à votre compte Blessy Tech Academy a été détectée :\n\n'
                    f'📍 Adresse IP : {ip}\n'
                    f'🌍 Pays : {pays}\n'
                    f'🏙️ Ville : {ville}\n'
                    f'🖥️ Navigateur : {user_agent[:100]}\n\n'
                    f'Si vous n\'êtes pas à l\'origine de cette connexion, changez immédiatement votre mot de passe.\n\n'
                    f'L\'équipe BTA'
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
        ProfilUtilisateur.objects.get_or_create(utilisateur=instance, defaults={'role': 'etudiant'})


# ================================================
# SIGNAL — Auto-création WorkflowFormation
# ================================================
@receiver(post_save, sender=Formation)
def creer_workflow_formation(sender, instance, created, **kwargs):
    """Crée automatiquement un WorkflowFormation pour chaque nouvelle Formation."""
    if created:
        from .models import WorkflowFormation
        WorkflowFormation.objects.get_or_create(formation=instance, defaults={'etat_actuel': 'brouillon'})