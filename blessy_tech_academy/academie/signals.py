"""
Signaux Django pour Blessy Tech Academy.
- Compression automatique des images uploadées (ProjetEtudiant, Formation)
- Détection des connexions suspectes et historique des connexions
"""

import os
from io import BytesIO
from PIL import Image
from django.core.files.base import ContentFile
from django.db.models.signals import pre_save
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
import requests
from .models import ProjetEtudiant, Formation, ConnexionUtilisateur

TAILLE_MAX = (1200, 1200)
QUALITE_JPEG = 82


# ================================================
# FONCTION UTILITAIRE : Compression d'image
# Rôle : Redimensionne et compresse une image en mémoire
# Utilisée par : compresser_image_projet, compresser_illustration_formation
# ================================================
def compresser_image(image_field, taille_max=TAILLE_MAX, qualite=QUALITE_JPEG):
    """
    Redimensionne et compresse une image en mémoire.
    Retourne un ContentFile prêt à être sauvegardé, ou None si erreur.
    """
    try:
        img = Image.open(image_field)

        # Convertit en RGB si nécessaire (PNG avec transparence, etc.)
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')

        # Redimensionne si trop grande (garde le ratio)
        img.thumbnail(taille_max, Image.Resampling.LANCZOS)

        # Sauvegarde en mémoire compressée
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
# Rôle : Compresse automatiquement l'image d'un projet avant sauvegarde
# ================================================
@receiver(pre_save, sender=ProjetEtudiant)
def compresser_image_projet(sender, instance, **kwargs):
    """Compresse automatiquement l'image d'un ProjetEtudiant avant sauvegarde."""
    if not instance.image:
        return

    # Évite de recompresser une image déjà traitée (si l'objet existe déjà en base)
    if instance.pk:
        try:
            ancien = ProjetEtudiant.objects.get(pk=instance.pk)
            if ancien.image == instance.image:
                return  # image inchangée, ne rien faire
        except ProjetEtudiant.DoesNotExist:
            pass

    # Vérifie que le fichier est bien une image en mémoire (nouvel upload)
    if hasattr(instance.image, 'file'):
        image_compressee = compresser_image(instance.image)
        if image_compressee:
            instance.image.save(image_compressee.name, image_compressee, save=False)


# ================================================
# SIGNAL : pre_save (Formation)
# Rôle : Compresse l'illustration d'une formation avant sauvegarde
# ================================================
@receiver(pre_save, sender=Formation)
def compresser_illustration_formation(sender, instance, **kwargs):
    """Compresse l'illustration d'une formation avant sauvegarde."""
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
# Rôle : Récupère pays et ville via l'API gratuite ip-api.com
# Utilisée par : enregistrer_connexion
# ================================================
def get_geo_info(ip):
    """Récupère le pays et la ville via l'API gratuite ip-api.com."""
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
# Rôle : Enregistre chaque connexion dans ConnexionUtilisateur
#        Détecte les connexions suspectes (IP ou pays différent)
#        Envoie un email d'alerte si connexion suspecte
# ================================================
@receiver(user_logged_in)
def enregistrer_connexion(sender, request, user, **kwargs):
    """Callback exécuté à chaque connexion réussie."""
    # Récupère l'adresse IP réelle (derrière proxy)
    ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', '')).split(',')[0].strip()
    user_agent = request.META.get('HTTP_USER_AGENT', '')[:300]
    pays, ville = get_geo_info(ip)

    # Vérifie si la connexion est suspecte (IP ou pays différent de la dernière connexion)
    derniere = ConnexionUtilisateur.objects.filter(utilisateur=user).order_by('-date_connexion').first()
    suspecte = False
    if derniere and (derniere.pays != pays or derniere.adresse_ip != ip):
        suspecte = True

    # Sauvegarde la connexion
    ConnexionUtilisateur.objects.create(
        utilisateur=user,
        adresse_ip=ip,
        navigateur=user_agent,
        pays=pays,
        ville=ville,
        suspecte=suspecte,
    )

    # Envoie un email d'alerte si connexion suspecte
    if suspecte and user.email:
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