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
    
    
def generer_quiz(sujet, nombre_questions=5):
    """
    Génère un quiz complet via l'IA.

    Args:
        sujet: Le sujet du quiz (ex: "Python Fondamental")
        nombre_questions: Nombre de questions à générer

    Returns:
        list: Liste de dictionnaires {texte, choix_a, choix_b, 
              choix_c, choix_d, bonne_reponse, explication}
    """
    try:
        model = initialiser_ia()

        prompt = f"""
Tu es un expert pédagogique de Blessy Tech Academy.

Génère {nombre_questions} questions à choix multiples sur le sujet : "{sujet}"

Niveau : débutant à intermédiaire, adapté à des étudiants en formation.

Réponds UNIQUEMENT avec un tableau JSON valide, sans texte avant/après,
sans balises markdown, au format EXACT suivant :

[
    {{
        "texte": "Question ici ?",
        "choix_a": "Option A",
        "choix_b": "Option B",
        "choix_c": "Option C",
        "choix_d": "Option D",
        "bonne_reponse": "a",
        "explication": "Brève explication de la bonne réponse"
    }}
]

Les questions doivent être en français, claires et pédagogiques.
"bonne_reponse" doit être exactement "a", "b", "c" ou "d" (minuscule).
"""
        reponse = model.generate_content(prompt)
        texte = reponse.text.strip()
        texte = texte.replace('```json', '').replace('```', '').strip()

        questions = json.loads(texte)
        return questions

    except Exception as e:
        return []
    
def generer_programme_complet(nom_formation, description_formation="", niveau="debutant"):
    """
    Génère un programme complet (modules + leçons) pour une formation.

    Args:
        nom_formation: Le nom de la formation
        description_formation: Description existante (contexte)
        niveau: Niveau de la formation (debutant, intermediaire, avance, professionnel)

    Returns:
        list: Liste de modules, chacun avec ses leçons
              [{titre, description, lecons: [{titre, resume, duree_minutes}]}]
    """
    try:
        model = initialiser_ia()

        prompt = f"""
Tu es un concepteur pédagogique expert pour Blessy Tech Academy,
une école de technologie professionnelle en Haïti.

Crée un programme de cours complet et structuré pour la formation :
"{nom_formation}"

Contexte : {description_formation}
Niveau : {niveau}

Le programme doit être progressif (du plus simple au plus avancé),
pratique, et orienté vers de vrais résultats professionnels.

Réponds UNIQUEMENT avec un tableau JSON valide, sans texte avant/après,
sans balises markdown, au format EXACT suivant :

[
    {{
        "titre": "Titre du Module 1",
        "description": "Brève description de ce que couvre ce module",
        "lecons": [
            {{
                "titre": "Titre de la leçon",
                "resume": "Résumé en 1 phrase de ce qu'on apprend",
                "duree_minutes": 20
            }}
        ]
    }}
]

Crée entre 4 et 6 modules, avec 3 à 5 leçons par module.
Tout doit être en français, professionnel et pédagogique.
"""
        reponse = model.generate_content(prompt)
        texte = reponse.text.strip()
        texte = texte.replace('```json', '').replace('```', '').strip()

        programme = json.loads(texte)
        return programme

    except Exception as e:
        return []