# academie/services/certificat_pdf.py
import base64
import logging
from io import BytesIO
import qrcode
from django.template.loader import render_to_string
from django.conf import settings
from django.http import HttpResponse
from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)

# ================================================
# FONCTION — Détermine la variante du certificat
# ================================================
def determiner_variante(certificat):
    """Détermine le titre selon le contexte — maintenant basé sur un vrai champ."""
    if certificat.parcours_origine:
        return "PARCOURS PROFESSIONNEL CERTIFIANT", "Parcours Professionnel Certifiant"
    if certificat.formation and certificat.formation.gratuit:
        return "ATTESTATION DE RÉUSSITE", "Attestation de réussite"
    return "CERTIFICAT DE RÉUSSITE", "Formation certifiante"


# ================================================
# SERVICE — Génération du PDF officiel
# ================================================
def generer_pdf_certificat_officiel(certificat, request=None):
    """
    Génère un PDF du certificat selon le modèle officiel (A4 paysage).
    Retourne les bytes du PDF, ou None en cas d'erreur.
    """
    try:
        # 1. Préparer le contexte
        from content.models import Certificat
        if not isinstance(certificat, Certificat):
            raise TypeError("L'objet passé n'est pas un Certificat.")

        # QR Code
        url_verification = f"{settings.SITE_URL}/certificat/{certificat.uuid}/"
        qr = qrcode.QRCode(version=1, box_size=10, border=2)
        qr.add_data(url_verification)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        qr_code_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

        # Déterminer la variante
        type_certificat, label_certificat = determiner_variante(certificat)

        # Contexte pour le template
        contexte = {
            'logo_url': f"{settings.SITE_URL}/static/img/logo-bta.png",
            'type_certificat': type_certificat,          # Titre du certificat
            'label_certificat': label_certificat,        # Description (pour usage futur)
            'partenaire_logo': '',
            'mention': '',
            'prenom': certificat.utilisateur.first_name,
            'nom': certificat.utilisateur.last_name,
            'username': certificat.utilisateur.username,
            'formation_nom': certificat.formation.nom if certificat.formation else 'Formation',
            'ecole_nom': certificat.formation.ecole.nom if certificat.formation and certificat.formation.ecole else '',
            'date_emission': certificat.date_emission,
            'numero_certificat': certificat.numero,
            'uuid': str(certificat.uuid),
            'qr_code_data': qr_code_base64,
            'signataire_nom': 'Jean Raymond BELONY',
            'signataire_titre': 'PDG & Fondateur',
            'verification_text': 'Certificat vérifiable en ligne – blessytechacademy.com',
            'url_verification': url_verification,
        }

        # 2. Rendre le HTML
        html = render_to_string("academie/pdf/certificat_officiel.html", contexte)

        # 3. Générer le PDF avec Playwright
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

        return pdf_bytes

    except Exception as e:
        logger.error(f"Erreur lors de la génération du PDF pour le certificat {certificat.numero} : {e}")
        return None