# ================================================
# VALIDATORS.PY
# Blessy Tech Academy
# Version : 3.0 — Renforcée (magic bytes)
#
# Validation professionnelle des fichiers uploadés.
# Vérifie l'extension, la taille et les premiers octets réels (magic bytes)
# pour empêcher l'usurpation d'extension (ex : .exe renommé en .jpg).
# ================================================

import os
import re

from django.core.exceptions import ValidationError

# ==========================================================
# CONSTANTES
# ==========================================================

EXTENSIONS_IMAGE_AUTORISEES = {".jpg", ".jpeg", ".png", ".webp"}
EXTENSIONS_DOCUMENT_AUTORISEES = {".pdf"}

TAILLE_MAX_IMAGE_MO = 5
TAILLE_MAX_DOCUMENT_MO = 10

# Signatures magiques des formats autorisés (premiers octets)
SIGNATURES_MAGIC_BYTES = {
    b'\xff\xd8\xff': 'jpg',         # JPEG
    b'\x89PNG\r\n\x1a\n': 'png',    # PNG
    b'RIFF': 'webp',               # WebP (conteneur RIFF)
    b'%PDF': 'pdf',                # PDF
}


# ==========================================================
# OUTILS
# ==========================================================

def _taille_max_octets(mo: int) -> int:
    return mo * 1024 * 1024


def _verifier_extension(fichier, extensions_autorisees):
    extension = os.path.splitext(fichier.name)[1].lower()
    if extension not in extensions_autorisees:
        raise ValidationError(
            f"Extension non autorisée ({extension}). "
            f"Extensions acceptées : {', '.join(extensions_autorisees)}"
        )


def _verifier_taille(fichier, taille_max_mo: int):
    if fichier.size > _taille_max_octets(taille_max_mo):
        raise ValidationError(
            f"Le fichier dépasse la taille maximale autorisée ({taille_max_mo} Mo)."
        )


def _verifier_magic_bytes(fichier, types_attendus: list) -> bool:
    """
    Vérifie que les premiers octets du fichier correspondent
    à l'un des types attendus. Empêche l'usurpation d'extension.
    """
    try:
        pos = fichier.tell()
        fichier.seek(0)
        entete = fichier.read(16)
        fichier.seek(pos)
    except Exception:
        return False

    for signature, type_reel in SIGNATURES_MAGIC_BYTES.items():
        if entete.startswith(signature) and type_reel in types_attendus:
            return True
    return False


# ==========================================================
# VALIDATION IMAGE
# ==========================================================

def valider_image(fichier):
    """
    Validation renforcée d'une image :
    ✔ Extension autorisée
    ✔ Taille max
    ✔ Magic bytes (JPEG, PNG, WebP)
    """
    _verifier_extension(fichier, EXTENSIONS_IMAGE_AUTORISEES)
    _verifier_taille(fichier, TAILLE_MAX_IMAGE_MO)

    if not _verifier_magic_bytes(fichier, ['jpg', 'png', 'webp']):
        raise ValidationError(
            "Le contenu du fichier ne correspond pas à une image valide "
            "(extension usurpée détectée)."
        )


# ==========================================================
# VALIDATION PDF
# ==========================================================

def valider_document(fichier):
    """
    Validation renforcée d'un document :
    ✔ Extension autorisée (PDF uniquement)
    ✔ Taille max
    ✔ Magic bytes (PDF)
    """
    _verifier_extension(fichier, EXTENSIONS_DOCUMENT_AUTORISEES)
    _verifier_taille(fichier, TAILLE_MAX_DOCUMENT_MO)

    if not _verifier_magic_bytes(fichier, ['pdf']):
        raise ValidationError(
            "Le contenu du fichier ne correspond pas à un PDF valide "
            "(extension usurpée détectée)."
        )


# ==========================================================
# PREUVE DE PAIEMENT
# ==========================================================

def valider_preuve_paiement(fichier):
    """
    Validation renforcée d'une preuve de paiement :
    ✔ Extension image ou PDF
    ✔ Taille max
    ✔ Magic bytes correspondant au type détecté
    """
    extension = os.path.splitext(fichier.name)[1].lower()
    extensions_acceptees = EXTENSIONS_IMAGE_AUTORISEES | EXTENSIONS_DOCUMENT_AUTORISEES

    if extension not in extensions_acceptees:
        raise ValidationError(
            f"Format non autorisé ({extension}). "
            f"Formats acceptés : {', '.join(extensions_acceptees)}"
        )

    _verifier_taille(fichier, TAILLE_MAX_IMAGE_MO)

    if extension in EXTENSIONS_IMAGE_AUTORISEES:
        if not _verifier_magic_bytes(fichier, ['jpg', 'png', 'webp']):
            raise ValidationError(
                "Le fichier n'est pas une image valide (extension usurpée)."
            )
    else:
        if not _verifier_magic_bytes(fichier, ['pdf']):
            raise ValidationError(
                "Le fichier n'est pas un PDF valide (extension usurpée)."
            )


# ================================================
# VALIDATORS.PY — Filtre anti-spam contenu forum
# ================================================

def detecter_spam_probable(texte):
    """Heuristiques simples anti-spam — retourne True si suspect."""
    if not texte:
        return False

    nb_liens = len(re.findall(r'https?://', texte))
    if nb_liens >= 4:
        return True

    if len(set(texte.split())) < len(texte.split()) * 0.3 and len(texte.split()) > 10:
        return True  # trop répétitif

    mots_suspects = ['viagra', 'casino', 'crypto gratuit', "gagner de l'argent rapidement"]
    texte_lower = texte.lower()
    if any(mot in texte_lower for mot in mots_suspects):
        return True

    return False