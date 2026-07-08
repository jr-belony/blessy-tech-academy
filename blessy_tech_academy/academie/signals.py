"""
Signaux Django pour Blessy Tech Academy.
Compression automatique des images uploadées (ProjetEtudiant, Article, etc.)
"""

import os
from io import BytesIO
from PIL import Image
from django.core.files.base import ContentFile
from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import Formation
from .models import ProjetEtudiant

TAILLE_MAX = (1200, 1200)
QUALITE_JPEG = 82


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