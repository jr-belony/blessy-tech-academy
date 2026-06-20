import google.generativeai as genai
from django.conf import settings
import json


def initialiser_ia():
    """Configure le SDK Gemini avec la clé API."""
    genai.configure(api_key=settings.GEMINI_API_KEY)
    return genai.GenerativeModel('gemini-2.5-flash')


def blessy_ai_repondre(question, contexte_formations=None):
    """Répond à une question via Blessy AI."""
    try:
        model = initialiser_ia()

        prompt_systeme = """
Tu es Blessy AI, l'assistant intelligent de Blessy Tech Academy.
Tu aides les étudiants à choisir leurs formations et à progresser
dans leur parcours numérique.

Blessy Tech Academy est une école de technologie haïtienne qui propose :
- Des formations en développement web (Python, Django, HTML/CSS)
- Des formations en Intelligence Artificielle
- De la maintenance informatique
- De la bureautique professionnelle
- Du graphic design

Tu réponds toujours en français, avec bienveillance et professionnalisme.
Tu es concis (3-5 phrases maximum) et orienté vers l'action.
Si tu ne sais pas quelque chose, tu le dis honnêtement.
"""

        if contexte_formations:
            formations_texte = "\n".join([
                f"- {f.nom} ({f.duree_mois} mois, {f.prix} USD)"
                for f in contexte_formations
            ])
            prompt_systeme += f"\n\nFormations actuellement disponibles :\n{formations_texte}"

        prompt_complet = f"{prompt_systeme}\n\nQuestion de l'étudiant : {question}"

        reponse = model.generate_content(prompt_complet)
        return reponse.text

    except Exception as e:
        return (
            "Désolé, je ne suis pas disponible en ce moment. "
            "Contactez-nous sur contact@blessyconnect.com"
        )


def recommander_formations(interets, formations_disponibles):
    """Recommande des formations selon les intérêts de l'étudiant."""
    try:
        model = initialiser_ia()

        formations_texte = "\n".join([
            f"- {f.nom} : {f.description} ({f.duree_mois} mois, {f.prix} USD)"
            for f in formations_disponibles
        ])

        prompt = f"""
Tu es un conseiller pédagogique de Blessy Tech Academy.

Voici les formations disponibles :
{formations_texte}

Un étudiant dit : "{interets}"

Recommande 2-3 formations adaptées à son profil, en expliquant
POURQUOI chacune lui convient. Sois précis et encourageant.
Réponds en français.
"""
        reponse = model.generate_content(prompt)
        return reponse.text

    except Exception as e:
        return "Impossible de générer des recommandations pour le moment."


def generer_contenu_formation(nom_formation, ecole_nom=""):
    """
    Génère automatiquement le contenu d'une formation via l'IA.

    Args:
        nom_formation: Le nom de la formation (ex: "Cybersécurité")
        ecole_nom: Le nom de l'école associée (optionnel, pour contexte)

    Returns:
        dict: {description, debouches, prerequis, certifications}
    """
    try:
        model = initialiser_ia()

        prompt = f"""
Tu es un expert pédagogique de Blessy Tech Academy, une école de
technologie en Haïti.

Génère le contenu pour une formation nommée "{nom_formation}"
{f'dans la catégorie "{ecole_nom}"' if ecole_nom else ''}.

Réponds UNIQUEMENT au format JSON suivant, sans texte avant ou après,
sans balises markdown :

{{
    "description": "Description engageante en 2-3 phrases, orientée résultats",
    "debouches": "Liste des débouchés professionnels, séparés par des virgules",
    "prerequis": "Prérequis nécessaires ou 'Aucun prérequis technique nécessaire'",
    "certifications": "Certifications reconnues pertinentes, séparées par des virgules"
}}

Le contenu doit être en français, professionnel, et adapté au
contexte haïtien et international.
"""
        reponse = model.generate_content(prompt)
        texte = reponse.text.strip()

        texte = texte.replace('```json', '').replace('```', '').strip()

        contenu = json.loads(texte)
        return contenu

    except Exception as e:
        return {
            'description': '',
            'debouches': '',
            'prerequis': '',
            'certifications': '',
            'erreur': str(e)
        }