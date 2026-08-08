# ================================================
# academie/services/certificat_pdf.py
# Génération de certificat PDF via Playwright
# ================================================

import base64
import logging
from io import BytesIO
import qrcode
from django.template.loader import render_to_string
from django.conf import settings
from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)

# ================================================
# CONSTANTES — Ordre des formations pour la Cohorte Pilote
# ================================================

ORDRE_FORMATIONS_COHORTE = [
    'Bureautique Professionnelle',
    'Intelligence Artificielle',
    'Internet, Recherche et Productivité',
]
NOM_BONUS = 'Microsoft Excel pour la Gestion de Stock'


# ================================================
# FONCTION 1 — Construction de la liste ordonnée des formations
# ================================================

def construire_liste_formations_ordonnee(certificat):
    """
    Respecte l'ordre exact demandé : Bureautique → IA → Internet,
    puis Bonus en dernier avec le nom exact 'Microsoft Excel pour la Gestion de Stock'.
    """
    toutes = list(certificat.formations_incluses.all())
    principales = []
    bonus = []

    # 1. Ajouter les formations principales dans l'ordre défini
    for nom_attendu in ORDRE_FORMATIONS_COHORTE:
        f = next((x for x in toutes if x.nom == nom_attendu), None)
        if f:
            principales.append({'nom': f.nom, 'bonus': False})

    # 2. Identifier la formation bonus (celle qui contient 'stock' et 'excel')
    formation_bonus = next(
        (x for x in toutes if 'stock' in x.nom.lower() and 'excel' in x.nom.lower()),
        None
    )
    if formation_bonus:
        bonus.append({'nom': NOM_BONUS, 'bonus': True})

    # 3. Retourner la liste complète (principales puis bonus)
    return principales + bonus


# ================================================
# FONCTION 2 — Déterminer la variante du certificat
# ================================================

def determiner_variante(certificat):
    """Détermine le titre selon le contexte."""
    if certificat.parcours_origine:
        return "PARCOURS PROFESSIONNEL CERTIFIANT", "Parcours Professionnel Certifiant"
    if certificat.formation and certificat.formation.gratuit:
        return "ATTESTATION DE RÉUSSITE", "Attestation de réussite"
    return "CERTIFICAT DE RÉUSSITE", "Formation certifiante"


# ================================================
# FONCTION 3 — Déterminer le template et le nom de la cohorte
# ================================================

def determiner_template_et_contexte_cohorte(certificat):
    """
    Vérifie si ce certificat est issu du processus contrôlé lié à une Cohorte.
    Retourne le chemin du template et le nom de la cohorte.
    """
    from academie.models import EligibiliteCertification

    eligibilite = EligibiliteCertification.objects.filter(
        certificat_genere=certificat
    ).select_related('cohorte').first()

    if eligibilite and eligibilite.cohorte:
        return 'academie/pdf/certificat_officiel_cohorte_pilote.html', eligibilite.cohorte.nom

    return 'academie/pdf/certificat_officiel.html', None


# ================================================
# FONCTION 4 — Conversion d'un champ image en base64
# ================================================

def image_vers_base64(champ_image):
    """
    Convertit un ImageField en data-URI base64 pour intégration HTML directe.
    """
    if not champ_image:
        return ''
    try:
        with champ_image.open('rb') as f:
            donnees = f.read()
        return f"data:image/png;base64,{base64.b64encode(donnees).decode()}"
    except Exception:
        return ''


# ================================================
# FONCTION PRINCIPALE — Génération du PDF officiel
# ================================================

def generer_pdf_certificat_officiel(certificat, request=None):
    """
    Génère un PDF du certificat selon le modèle officiel (A4 paysage).
    Choisit automatiquement le template selon que le certificat est lié
    à une cohorte pilote ou non.
    Retourne les bytes du PDF, ou None en cas d'erreur.
    """
    try:
        # ÉTAPE 1 : Validation de l'objet
        from content.models import Certificat
        if not isinstance(certificat, Certificat):
            raise TypeError("L'objet passé n'est pas un Certificat.")

        # ÉTAPE 2 : Détermination du template et de la cohorte
        template_a_utiliser, cohorte_nom = determiner_template_et_contexte_cohorte(certificat)
        # ÉTAPE 3 : Détermination de la variante
        titre_principal, mention_type = determiner_variante(certificat)
        # ÉTAPE 4 : Génération du QR Code (dynamique)
        url_verification = f"{settings.SITE_URL}/certificat/{certificat.uuid}/"
        qr = qrcode.QRCode(version=1, box_size=10, border=2)
        qr.add_data(url_verification)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        qr_code_base64_dynamique = base64.b64encode(buffer.getvalue()).decode("utf-8")
        # ÉTAPE 5 : Construction du contexte
        contexte = {
            # 5.1 — Informations générales
            'certificat': certificat,
            'titre_principal': titre_principal,
            'mention_type': mention_type,

            # 5.2 — Identité du bénéficiaire
            'nom_complet': certificat.utilisateur.get_full_name() or certificat.utilisateur.username,
            'prenom': certificat.utilisateur.first_name,
            'nom': certificat.utilisateur.last_name,
            'username': certificat.utilisateur.username,

            # 5.3 — Formation et école
            'formation_nom': certificat.formation.nom if certificat.formation else '',
            'ecole_nom': certificat.formation.ecole.nom if certificat.formation and certificat.formation.ecole else '',

            # 5.4 — Niveau (exclu pour la cohorte pilote)
            'niveau_affiche': '' if template_a_utiliser.endswith('cohorte_pilote.html') else (
                certificat.get_niveau_display() if hasattr(certificat, 'get_niveau_display') else ''
            ),

            # 5.5 — Dates et cohorte
            'date_affichee': getattr(certificat, 'date_obtention', certificat.date_emission),
            'date_emission': certificat.date_emission,
            'cohorte_nom': cohorte_nom,

            # 5.6 — QR Code (base64 depuis l'image stockée ou généré)
            'qr_code_base64': image_vers_base64(getattr(certificat, 'qr_code_image', None)) or qr_code_base64_dynamique,
            'qr_code_data': qr_code_base64_dynamique,

            # 5.7 — Programme et formations incluses (ordre exact pour cohorte)
            'libelle_programme': certificat.libelle_programme or 'Compétences Numériques Professionnelles',
            'formations_incluses': construire_liste_formations_ordonnee(certificat) if template_a_utiliser.endswith('cohorte_pilote.html') else [],
            # 5.8 — Éléments visuels
            'logo_url': f"{settings.SITE_URL}/static/img/logo-bta.png",
            'type_certificat': titre_principal,
            'label_certificat': mention_type,
            'numero_certificat': certificat.numero,
            'uuid': str(certificat.uuid),
            'signataire_nom': 'Jean Raymond BELONY',
            'signataire_titre': 'PDG & Fondateur',
            'verification_text': 'Certificat vérifiable en ligne – blessytechacademy.com',
            'url_verification': url_verification,
        }
        # ÉTAPE 6 : Rendu HTML avec le template sélectionné
        html = render_to_string(template_a_utiliser, contexte)
        # ÉTAPE 7 : Génération du PDF avec Playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_content(html, wait_until="networkidle")
            pdf_bytes = page.pdf(
                format="A4",
                landscape=True,
                print_background=True,
                margin={"top": "0mm", "bottom": "0mm", "left": "0mm", "right": "0mm"}
            )
            browser.close()
        # ÉTAPE 8 : Retour des bytes du PDF
        return pdf_bytes

    except Exception as e:
        logger.error(f"Erreur lors de la génération du PDF pour le certificat {certificat.numero} : {e}")
        return None


# ================================================
# FONCTION ASYNCHRONE — Pour Dramatiq
# ================================================

def generer_pdf_certificat_async(certificat_id):
    """
    Point d'entrée pour Dramatiq — génère le PDF en arrière-plan.
    """
    from academie.models import Certificat
    from django.core.files.base import ContentFile

    certificat = Certificat.objects.get(id=certificat_id)
    pdf_bytes = generer_pdf_certificat_officiel(certificat)
    if pdf_bytes:
        certificat.fichier_pdf.save(
            f"certificat_{certificat.numero}.pdf",
            ContentFile(pdf_bytes),
            save=True
        )
        logger.info(f"PDF généré pour certificat {certificat.numero}")
    else:
        logger.error(f"Échec génération PDF pour certificat {certificat.numero}")