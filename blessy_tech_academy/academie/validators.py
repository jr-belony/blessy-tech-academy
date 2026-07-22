# ================================================
# VALIDATORS.PY
# Blessy Tech Academy
# Version : 2.0
#
# Validation professionnelle des fichiers uploadés
#
# Compatible avec :
# - ProjetEtudiant
# - Academie.logo
# - Enseignant.document_cv
# - Transaction.preuve_paiement
# - Tous les futurs uploads
# ================================================

import os

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile

from PIL import Image
from pypdf import PdfReader


# ==========================================================
# CONSTANTES
# ==========================================================

EXTENSIONS_IMAGE_AUTORISEES = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
}

EXTENSIONS_DOCUMENT_AUTORISEES = {
    ".pdf",
}

TAILLE_MAX_IMAGE_MO = 5
TAILLE_MAX_DOCUMENT_MO = 10


# ==========================================================
# OUTILS
# ==========================================================

def taille_max_octets(mo: int) -> int:
    return mo * 1024 * 1024


def verifier_extension(fichier: UploadedFile, extensions):
    extension = os.path.splitext(fichier.name)[1].lower()

    if extension not in extensions:
        raise ValidationError(
            f"Extension non autorisée ({extension})."
        )


def verifier_taille(fichier: UploadedFile, taille_max_mo: int):
    if fichier.size > taille_max_octets(taille_max_mo):
        raise ValidationError(
            f"Le fichier dépasse la taille maximale autorisée ({taille_max_mo} Mo)."
        )


# ==========================================================
# VALIDATION IMAGE
# ==========================================================

def verifier_image_reelle(fichier: UploadedFile):
    """
    Vérifie que le fichier est une véritable image.
    """

    try:

        position = fichier.tell()

        image = Image.open(fichier)

        image.verify()

        fichier.seek(position)

    except Exception:
        raise ValidationError(
            "Le fichier n'est pas une image valide."
        )


def valider_image(fichier: UploadedFile):
    """
    Validation professionnelle d'une image.

    Vérifie :

    ✔ Extension
    ✔ Taille
    ✔ Intégrité de l'image
    """

    verifier_extension(
        fichier,
        EXTENSIONS_IMAGE_AUTORISEES,
    )

    verifier_taille(
        fichier,
        TAILLE_MAX_IMAGE_MO,
    )

    verifier_image_reelle(fichier)


# ==========================================================
# VALIDATION PDF
# ==========================================================

def verifier_pdf_valide(fichier: UploadedFile):
    """
    Vérifie que le PDF est lisible.
    """

    try:

        position = fichier.tell()

        PdfReader(fichier)

        fichier.seek(position)

    except Exception:
        raise ValidationError(
            "Le PDF est invalide ou corrompu."
        )


def valider_document(fichier: UploadedFile):
    """
    Validation professionnelle des documents.

    Actuellement :

    ✔ PDF uniquement
    ✔ Taille
    ✔ Intégrité
    """

    verifier_extension(
        fichier,
        EXTENSIONS_DOCUMENT_AUTORISEES,
    )

    verifier_taille(
        fichier,
        TAILLE_MAX_DOCUMENT_MO,
    )

    verifier_pdf_valide(fichier)


# ==========================================================
# PREUVE DE PAIEMENT
# ==========================================================

def valider_preuve_paiement(fichier: UploadedFile):
    """
    Accepte :

    ✔ Image
    ✔ PDF
    """

    extension = os.path.splitext(fichier.name)[1].lower()

    if extension in EXTENSIONS_IMAGE_AUTORISEES:

        return valider_image(fichier)

    if extension in EXTENSIONS_DOCUMENT_AUTORISEES:

        return valider_document(fichier)

    raise ValidationError(
        "La preuve de paiement doit être une image ou un PDF."
    )


# ================================================
# VALIDATORS.PY — Filtre anti-spam contenu forum
# ================================================

import re

def detecter_spam_probable(texte):
    """Heuristiques simples anti-spam — retourne True si suspect."""
    if not texte:
        return False

    nb_liens = len(re.findall(r'https?://', texte))
    if nb_liens >= 4:
        return True

    if len(set(texte.split())) < len(texte.split()) * 0.3 and len(texte.split()) > 10:
        return True  # trop répétitif

    mots_suspects = ['viagra', 'casino', 'crypto gratuit', 'gagner de l\'argent rapidement']
    texte_lower = texte.lower()
    if any(mot in texte_lower for mot in mots_suspects):
        return True

    return False