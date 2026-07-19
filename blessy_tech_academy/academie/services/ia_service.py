import json
import logging
import re
import google.genai as genai
from django.conf import settings
from .async_tasks import executer_en_arriere_plan
from .email_service import send_badge_email, send_certificate_email

logger = logging.getLogger(__name__)


# ================================================
# IA.PY — Parsing JSON robuste pour réponses Gemini
# Corrige le risque audit : "Prompt parsing JSON fragile"
# Ajoute cette fonction juste après les imports, avant toute autre fonction
# ================================================

logger = logging.getLogger('academie')

def parser_json_robuste(texte_brut, valeur_defaut=None):
    """
    Extrait et parse du JSON depuis une réponse Gemini de façon tolérante.
    Gère : balises markdown ```json, texte parasite avant/après, 
    guillemets mal échappés, JSON tronqué.
    """
    if not texte_brut:
        return valeur_defaut

    texte = texte_brut.strip()

    # Étape 1 : retire les balises markdown
    texte = re.sub(r'```(?:json)?\s*', '', texte)
    texte = texte.replace('```', '').strip()

    # Étape 2 : tentative directe
    try:
        return json.loads(texte)
    except json.JSONDecodeError:
        pass

    # Étape 3 : extrait le premier bloc {...} ou [...] valide via regex
    match_objet = re.search(r'\{.*\}', texte, re.DOTALL)
    match_liste = re.search(r'\[.*\]', texte, re.DOTALL)

    for match in [match_objet, match_liste]:
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                continue

    # Étape 4 : dernier recours — nettoie les virgules trainantes courantes
    try:
        texte_nettoye = re.sub(r',(\s*[}\]])', r'\1', texte)
        return json.loads(texte_nettoye)
    except json.JSONDecodeError:
        logger.warning(f"⚠️ Parsing JSON impossible malgré tentatives — réponse brute : {texte_brut[:200]}")
        return valeur_defaut


def initialiser_ia():
    """Configure et retourne le client Gemini."""
    return genai.Client(api_key=settings.GEMINI_API_KEY)


def construire_prompt_chat(
    question, historique=None, contexte_utilisateur=None, formations_disponibles=None
):
    """Construit un prompt contextualisé pour Blessy AI."""
    prompt = (
        "Tu es Blessy AI, l'assistant intelligent de Blessy Tech Academy. "
        "Tu aides les étudiants à choisir leurs formations et à progresser. "
        "Tu réponds toujours en français, avec bienveillance et professionnalisme. "
        "Sois concis, clair et orienté vers l'action.\n"
    )

    if contexte_utilisateur:
        prompt += f"\nContexte utilisateur :\n- Prénom : {contexte_utilisateur.get('prenom', '')}\n"
        formations_suivies = contexte_utilisateur.get("formations_suivies", [])
        if formations_suivies:
            prompt += "- Formations déjà suivies : " + ", ".join(formations_suivies) + "\n"

    if historique:
        prompt += "\nHistorique de conversation :\n"
        for message in historique[-8:]:
            role = "Étudiant" if message.get("role") == "user" else "Blessy AI"
            prompt += f"- {role} : {message.get('content', '')}\n"

    if formations_disponibles:
        prompt += "\nFormations disponibles :\n"
        for formation in formations_disponibles[:5]:
            prompt += f"- {formation.nom} ({formation.duree_mois} mois, {formation.prix} USD)\n"

    prompt += f"\nQuestion actuelle de l'étudiant : {question}"
    return prompt


def repondre_chat_ia(
    question, historique=None, contexte_utilisateur=None, formations_disponibles=None
):
    """Répond à une question avec contexte et historique de conversation."""
    try:
        client = initialiser_ia()
        prompt = construire_prompt_chat(
            question=question,
            historique=historique,
            contexte_utilisateur=contexte_utilisateur,
            formations_disponibles=formations_disponibles,
        )

        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        texte = (response.text or "").strip()
        return (
            texte
            or "Je n'ai pas pu générer une réponse précise pour le moment. Réessaie dans quelques secondes."
        )
    except Exception:
        logger.exception("Échec de l'appel à Gemini")
        from ..knowledge_base import rechercher_reponse_locale

        reponse_locale = rechercher_reponse_locale(question)
        if reponse_locale:
            return (
                reponse_locale
                + "\n\n_(Réponse automatique, notre IA est temporairement indisponible)_"
            )
        return "Désolé, le chatbot est temporairement indisponible. Vous pouvez nous contacter sur contact@blessyconnect.com."


def blessy_ai_repondre(
    question, contexte_formations=None, historique=None, contexte_utilisateur=None
):
    """Compatibilité avec l'ancienne signature et support mémoire/personnalisation."""
    return repondre_chat_ia(
        question=question,
        historique=historique,
        contexte_utilisateur=contexte_utilisateur,
        formations_disponibles=list(contexte_formations) if contexte_formations else None,
    )


def recommander_formations(interets, formations_disponibles):
    """Recommande des formations selon les intérêts de l'étudiant."""
    try:
        client = initialiser_ia()
        formations_texte = "\n".join(
            [
                f"- {f.nom} : {f.description} ({f.duree_mois} mois, {f.prix} USD)"
                for f in formations_disponibles
            ]
        )
        prompt = (
            f"Tu es un conseiller pédagogique de Blessy Tech Academy.\n\n"
            f"Formations disponibles :\n{formations_texte}\n\n"
            f'Un étudiant dit : "{interets}"\n\n'
            "Recommande 2-3 formations adaptées à son profil, en expliquant "
            "POURQUOI chacune lui convient. Sois précis et encourageant. "
            "Réponds en français."
        )
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        return response.text.strip()
    except Exception:
        logger.exception("Erreur recommandation formations")
        return "Impossible de générer des recommandations pour le moment."


def generer_contenu_formation(nom_formation, ecole_nom=""):
    """Génère automatiquement le contenu d'une formation via l'IA."""
    try:
        client = initialiser_ia()
        prompt = (
            f"Tu es un expert pédagogique de Blessy Tech Academy, une école de technologie en Haïti.\n\n"
            f'Génère le contenu pour une formation nommée "{nom_formation}"'
            f"{' dans la catégorie \"' + ecole_nom + '\"' if ecole_nom else ''}.\n\n"
            "Réponds UNIQUEMENT au format JSON suivant, sans texte avant ou après, sans balises markdown :\n\n"
            "{\n"
            '    "description": "Description engageante en 2-3 phrases, orientée résultats",\n'
            '    "debouches": "Liste des débouchés professionnels, séparés par des virgules",\n'
            '    "prerequis": "Prérequis nécessaires ou \'Aucun prérequis technique nécessaire\'",\n'
            '    "certifications": "Certifications reconnues pertinentes, séparées par des virgules"\n'
            "}\n\n"
            "Le contenu doit être en français, professionnel, et adapté au contexte haïtien et international."
        )
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        # Utilisation du parsing robuste
        return parser_json_robuste(response.text, valeur_defaut={
            "description": "",
            "debouches": "",
            "prerequis": "",
            "certifications": ""
        })
    except Exception as e:
        logger.exception("Erreur génération contenu formation")
        return {
            "description": "",
            "debouches": "",
            "prerequis": "",
            "certifications": "",
            "erreur": str(e),
        }


def generer_quiz(sujet, nombre_questions=5):
    """Génère un quiz complet via l'IA."""
    try:
        client = initialiser_ia()
        prompt = (
            f"Tu es un expert pédagogique de Blessy Tech Academy.\n\n"
            f'Génère {nombre_questions} questions à choix multiples sur le sujet : "{sujet}"\n\n'
            "Niveau : débutant à intermédiaire, adapté à des étudiants en formation.\n\n"
            "Réponds UNIQUEMENT avec un tableau JSON valide, sans texte avant/après, "
            "sans balises markdown, au format EXACT suivant :\n\n"
            "[\n"
            "    {\n"
            '        "texte": "Question ici ?",\n'
            '        "choix_a": "Option A",\n'
            '        "choix_b": "Option B",\n'
            '        "choix_c": "Option C",\n'
            '        "choix_d": "Option D",\n'
            '        "bonne_reponse": "a",\n'
            '        "explication": "Brève explication de la bonne réponse"\n'
            "    }\n"
            "]\n\n"
            "Les questions doivent être en français, claires et pédagogiques. "
            '"bonne_reponse" doit être exactement "a", "b", "c" ou "d" (minuscule).'
        )
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        # Utilisation du parsing robuste
        return parser_json_robuste(response.text, valeur_defaut=[])
    except Exception:
        logger.exception("Erreur génération quiz")
        return []


def generer_programme_complet(nom_formation, description_formation="", niveau="debutant"):
    """Génère un programme complet (modules + leçons) pour une formation."""
    try:
        client = initialiser_ia()
        prompt = (
            f"Tu es un concepteur pédagogique expert pour Blessy Tech Academy, "
            f"une école de technologie professionnelle en Haïti.\n\n"
            f'Crée un programme de cours complet et structuré pour la formation : "{nom_formation}"\n\n'
            f"Contexte : {description_formation}\n"
            f"Niveau : {niveau}\n\n"
            "Le programme doit être progressif (du plus simple au plus avancé), "
            "pratique, et orienté vers de vrais résultats professionnels.\n\n"
            "Réponds UNIQUEMENT avec un tableau JSON valide, sans texte avant/après, "
            "sans balises markdown, au format EXACT suivant :\n\n"
            "[\n"
            "    {\n"
            '        "titre": "Titre du Module 1",\n'
            '        "description": "Brève description de ce que couvre ce module",\n'
            '        "lecons": [\n'
            "            {\n"
            '                "titre": "Titre de la leçon",\n'
            '                "resume": "Résumé en 1 phrase de ce qu\'on apprend",\n'
            '                "duree_minutes": 20\n'
            "            }\n"
            "        ]\n"
            "    }\n"
            "]\n\n"
            "Crée entre 4 et 6 modules, avec 3 à 5 leçons par module. "
            "Tout doit être en français, professionnel et pédagogique."
        )
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        # Utilisation du parsing robuste
        return parser_json_robuste(response.text, valeur_defaut=[])
    except Exception:
        logger.exception("Erreur génération programme")
        return []

def generer_contenu_lecon(titre_lecon, resume_lecon="", contexte_formation="", contexte_module=""):
    """Génère le contenu complet d'une leçon individuelle."""
    try:
        client = initialiser_ia()
        prompt = (
            f"Tu es un formateur expert de Blessy Tech Academy, une école de technologie professionnelle en Haïti.\n\n"
            f"Rédige le contenu COMPLET d'une leçon de cours pour :\n\n"
            f"Formation : {contexte_formation}\n"
            f"Module : {contexte_module}\n"
            f'Leçon : "{titre_lecon}"\n'
            f"{'Résumé prévu : ' + resume_lecon if resume_lecon else ''}\n\n"
            "Structure obligatoire du contenu (utilise ces titres exacts) :\n\n"
            "## Explication\n"
            "[Explique le concept clairement, avec des mots simples, adapté à un débutant motivé. 2-4 paragraphes.]\n\n"
            "## Exemple concret\n"
            "[Donne un exemple pratique et réaliste. Si c'est un sujet technique/code, inclus un bloc de code avec "
            "des commentaires. Si c'est un sujet non-technique, donne un cas d'usage réel.]\n\n"
            "## Mini-exercice\n"
            "[Propose un petit exercice pratique que l'étudiant peut faire immédiatement pour appliquer ce qu'il vient "
            "d'apprendre. Donne aussi la solution ou la démarche attendue.]\n\n"
            "Réponds uniquement avec le contenu de la leçon en français, en utilisant le format Markdown "
            "(## pour les titres, ```code``` pour le code si nécessaire, **gras** pour les points clés). "
            "Sois pédagogique, concret, et engageant. Ne mets pas de texte d'introduction ou de conclusion "
            "en dehors de cette structure."
        )
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        return response.text.strip()
    except Exception as e:
        logger.exception("Erreur génération leçon")
        return f"Erreur lors de la génération : {str(e)}"


def generer_parcours_oriente(profil, objectif, disponibilite, details, formations_disponibles):
    """Génère un parcours personnalisé basé sur le profil de l'étudiant."""
    try:
        client = initialiser_ia()
        formations_texte = "\n".join(
            [
                f"- ID:{f.id} | {f.nom} ({f.duree_mois} mois, {f.prix} USD) | Niveau: {f.niveau} | École: {f.ecole}"
                for f in formations_disponibles
            ]
        )
        prompt = (
            f"Tu es Blessy AI, conseiller pédagogique expert de Blessy Tech Academy en Haïti.\n\n"
            f"Un étudiant a rempli son profil :\n"
            f"- Profil : {profil}\n"
            f"- Objectif principal : {objectif}\n"
            f"- Disponibilité : {disponibilite}\n"
            f'- Détails personnels : "{details}"\n\n'
            f"Formations disponibles à BTA :\n{formations_texte}\n\n"
            "Crée un parcours personnalisé et progressif pour cet étudiant.\n\n"
            "Réponds UNIQUEMENT en JSON valide, sans markdown, au format EXACT :\n\n"
            "{\n"
            '    "message_personnel": "Message d\'encouragement personnalisé (2-3 phrases, chaleureux)",\n'
            '    "duree_totale": 12,\n'
            '    "budget_total": 650,\n'
            '    "etapes": [\n'
            "        {\n"
            '            "ordre": 1,\n'
            '            "formation_id": 5,\n'
            '            "formation_nom": "Bureautique Professionnelle",\n'
            '            "formation_icone": "📊",\n'
            '            "raison": "Pourquoi cette formation en premier (1 phrase)",\n'
            '            "duree_mois": 3,\n'
            '            "prix": 150\n'
            "        }\n"
            "    ]\n"
            "}\n\n"
            "Règles :\n"
            "- Choisis entre 2 et 5 formations dans l'ordre logique de progression\n"
            "- Utilise UNIQUEMENT les formations disponibles (avec leur ID exact)\n"
            "- Adapte le parcours à la disponibilité (moins de temps = moins de formations)\n"
            "- Sois précis et encourageant\n"
            "- Réponds en français"
        )
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        # Utilisation du parsing robuste au lieu du json.loads() fragile
        resultat = parser_json_robuste(response.text, valeur_defaut={'erreur': 'Format de réponse IA invalide'})
        return resultat
    except Exception as e:
        logger.exception("Erreur parcours orienté")
        return {"erreur": str(e)}
    


# ================================================
# Badges
# ================================================
def attribuer_badges(utilisateur):
    """Vérifie et attribue automatiquement TOUS les badges, et notifie par email (asynchrone)."""
    from ..models import (
        BadgeForum,
        Formation,
        ProgressionLecon,
        Reaction,
        Reponse,
        ResultatQuiz,
        Sujet,
    )

    nouveaux_badges = []
    badges_existants = set(
        BadgeForum.objects.filter(utilisateur=utilisateur).values_list("type_badge", flat=True)
    )

    nb_sujets = Sujet.objects.filter(auteur=utilisateur).count()
    nb_reponses = Reponse.objects.filter(auteur=utilisateur).count()
    nb_solutions = Reponse.objects.filter(auteur=utilisateur, acceptee=True).count()
    nb_likes_recus = Reaction.objects.filter(reponse__auteur=utilisateur).count()

    forum_badges = [
        ("premier_post", nb_sujets >= 1),
        ("premiere_reponse", nb_reponses >= 1),
        ("solution_acceptee", nb_solutions >= 1),
        ("dix_reponses", nb_reponses >= 10),
        ("cinquante_reponses", nb_reponses >= 50),
        ("cent_likes", nb_likes_recus >= 100),
        ("sujet_populaire", Sujet.objects.filter(auteur=utilisateur, vues__gte=500).exists()),
        ("membre_actif_forum", nb_sujets >= 3 or nb_reponses >= 5),
    ]

    quiz_reussis = ResultatQuiz.objects.filter(utilisateur=utilisateur)
    nb_quiz_reussis = sum(1 for q in quiz_reussis if q.pourcentage() >= 70)

    lecons_terminees = ProgressionLecon.objects.filter(utilisateur=utilisateur, terminee=True)
    nb_lecons = lecons_terminees.count()
    heures_apprentissage = nb_lecons * 0.5

    formations_completees = []
    for formation in Formation.objects.filter(actif=True):
        if formation.progression_pour(utilisateur) == 100:
            formations_completees.append(formation)
    nb_formations = len(formations_completees)

    apprentissage_badges = [
        ("premier_quiz", nb_quiz_reussis >= 1),
        ("cinq_quiz", nb_quiz_reussis >= 5),
        ("dix_heures", heures_apprentissage >= 10),
        ("cinquante_heures", heures_apprentissage >= 50),
        ("premiere_formation", nb_formations >= 1),
        ("trois_formations", nb_formations >= 3),
        ("premier_cours_termine", nb_formations >= 1),
        ("cinq_lecons", nb_lecons >= 5),
        ("dix_lecons", nb_lecons >= 10),
        ("cinquante_lecons", nb_lecons >= 50),
    ]

    formations_noms = [f.nom.lower() for f in formations_completees]
    progression_noms = []
    for p in ProgressionLecon.objects.filter(utilisateur=utilisateur, terminee=True).select_related(
        "lecon__module__formation"
    ):
        nom = p.lecon.module.formation.nom.lower()
        if nom not in progression_noms:
            progression_noms.append(nom)

    competences_badges = [
        ("expert_python", "python" in progression_noms),
        (
            "expert_web",
            any(m in " ".join(formations_noms) for m in ["web", "html", "css", "javascript"]),
        ),
        ("expert_data", any(m in " ".join(formations_noms) for m in ["donnée", "data", "analyse"])),
        ("expert_cyber", "cybersécurité" in " ".join(formations_noms)),
        (
            "expert_design",
            any(m in " ".join(formations_noms) for m in ["design", "graphique", "création"]),
        ),
        ("expert_excel", any(m in " ".join(formations_noms) for m in ["excel", "bureautique"])),
        (
            "expert_ia",
            any(
                m in " ".join(formations_noms)
                for m in ["ia", "intelligence artificielle", "prompt"]
            ),
        ),
    ]

    projets_badges = [
        ("projet_termine", nb_formations >= 1),
        ("trois_projets", nb_formations >= 3),
    ]

    profile_complet = all([utilisateur.first_name, utilisateur.last_name, utilisateur.email])
    social_badges = [
        ("profile_complet", profile_complet),
        ("premier_certificat", nb_formations >= 1),
        ("membre_actif", nb_reponses >= 5 or nb_sujets >= 3 or nb_quiz_reussis >= 3),
    ]

    tous_badges = (
        forum_badges + apprentissage_badges + competences_badges + projets_badges + social_badges
    )

    for type_badge, condition in tous_badges:
        if condition and type_badge not in badges_existants:
            BadgeForum.objects.create(utilisateur=utilisateur, type_badge=type_badge)
            nouveaux_badges.append(type_badge)
            badges_existants.add(type_badge)
            # Envoi asynchrone de l'email de badge (les imports sont en haut du fichier)
            executer_en_arriere_plan(send_badge_email, utilisateur, type_badge)

    return nouveaux_badges



# ================================================
# FONCTIONS IA POUR LE BOUTON IA (6 fonctionnalités)
# ================================================
def assistant_code(code, langage="python", question=""):
    """Fonction 1 : Assistant Code - Analyse et corrige le code."""
    try:
        client = initialiser_ia()
        prompt = (
            f"Tu es un assistant de code expert pour Blessy Tech Academy.\n"
            f"Un étudiant te soumet du code {langage} à analyser.\n\n"
            f"```{langage}\n{code}\n```\n\n"
        )
        if question:
            prompt += f"Question complémentaire de l'étudiant : {question}\n\n"
        prompt += (
            "Tu dois :\n"
            "1. Analyser le code et identifier les erreurs éventuelles\n"
            "2. Expliquer les erreurs de façon pédagogique, adaptée à un apprenant\n"
            "3. Proposer une version corrigée avec des commentaires explicatifs\n"
            "4. Suggérer des bonnes pratiques si pertinent\n"
            "5. Encourager l'étudiant dans son apprentissage\n\n"
            "Réponds en français, en Markdown structuré "
            "(## Analyse, ## Erreurs trouvées, ## Code corrigé, ## Bonnes pratiques, ## Conseil). "
            "Sois pédagogue, bienveillant et encourageant."
        )
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        return (response.text or "").strip()
    except Exception as e:
        logger.exception("Erreur assistant code")
        return f"❌ Erreur lors de l'analyse : {str(e)}"


def generateur_exercices(sujet, niveau="debutant", format_exercice="code"):
    """Fonction 2 : Générateur d'exercices personnalisés."""
    try:
        client = initialiser_ia()
        prompt = (
            f"Tu es un générateur d'exercices pour Blessy Tech Academy.\n"
            f"Crée un exercice personnalisé avec les critères suivants :\n\n"
            f"- Sujet : {sujet}\n- Niveau : {niveau}\n- Format : {format_exercice}\n\n"
            "Structure ta réponse en Markdown :\n"
            "## 🎯 Exercice : [Titre]\n## 📋 Consignes\n## 💡 Indices\n"
            "## ✅ Résultat attendu\n## 📝 Corrigé type\n\n"
            "Adapte la difficulté au niveau (débutant = très guidé, intermédiaire = moyennement guidé, avancé = autonome). "
            "Si format = 'qcm', génère un QCM avec 4 choix et la bonne réponse. Sois pédagogue et encourageant. Réponds en français."
        )
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        return (response.text or "").strip()
    except Exception as e:
        logger.exception("Erreur générateur exercices")
        return f"❌ Erreur lors de la génération : {str(e)}"


def explication_concept(question, niveau_eleve="debutant"):
    """Fonction 3 : Explication de concept avec exemples."""
    try:
        client = initialiser_ia()
        prompt = (
            f"Tu es un tuteur expert de Blessy Tech Academy.\n"
            f'Un étudiant de niveau {niveau_eleve} demande : "{question}"\n\n'
            "Structure ta réponse en Markdown :\n"
            "## 📖 Définition\n## 💻 Exemple concret\n## 🎯 Cas d'usage\n"
            "## ⚠️ Erreurs à éviter\n## 💡 Pour aller plus loin\n\n"
            "Adapte ton langage au niveau de l'étudiant. Sois pédagogue, clair et encourageant. Réponds en français."
        )
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        return (response.text or "").strip()
    except Exception as e:
        logger.exception("Erreur explication concept")
        return f"❌ Erreur lors de l'explication : {str(e)}"


def correction_automatique(enonce, reponse_eleve, bareme=""):
    """Fonction 4 : Correction automatique d'exercice."""
    try:
        client = initialiser_ia()
        prompt = (
            f"Tu es un correcteur pédagogique de Blessy Tech Academy.\n\n"
            f"## Énoncé :\n{enonce}\n\n## Réponse de l'étudiant :\n{reponse_eleve}\n\n"
        )
        if bareme:
            prompt += f"Barème : {bareme}\n\n"
        prompt += (
            "Évalue la réponse sur 20. Structure en Markdown :\n"
            "## 📊 Note : [X]/20\n## ✅ Points positifs\n## 🔧 À améliorer\n## 💬 Feedback\n## 📚 À réviser\n\n"
            "Sois juste, constructif et encourageant. L'objectif est d'aider l'étudiant à progresser. Réponds en français."
        )
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        return (response.text or "").strip()
    except Exception as e:
        logger.exception("Erreur correction")
        return f"❌ Erreur lors de la correction : {str(e)}"


def parcours_adaptatif(profil_scores, parcours_actuel="", objectif=""):
    """Fonction 5 : Recommandation de parcours adaptatif."""
    try:
        client = initialiser_ia()
        profil_texte = "\n".join([f"- {s} : {sc}%" for s, sc in profil_scores.items()])
        prompt = (
            f"Tu es un conseiller pédagogique IA de Blessy Tech Academy.\n\n"
            f"## Profil (scores par sujet) :\n{profil_texte}\n\n"
            f"Parcours actuel : {parcours_actuel or 'Non spécifié'}\n"
            f"Objectif : {objectif or 'Non spécifié'}\n\n"
            "Structure en Markdown :\n## 📊 Analyse du profil\n## 🎯 Recommandations (3 leçons)\n"
            "## 📝 Plan d'action\n## 💪 Conseil de motivation\n\n"
            "Sois précis et encourageant. Réponds en français."
        )
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        return (response.text or "").strip()
    except Exception as e:
        logger.exception("Erreur parcours adaptatif")
        return f"❌ Erreur lors de l'analyse : {str(e)}"


def chatbot_tuteur(message, historique=None, niveau_eleve="debutant"):
    """Fonction 6 : Chatbot tuteur conversationnel."""
    try:
        client = initialiser_ia()
        prompt = (
            "Tu es Blessy AI, tuteur bienveillant de Blessy Tech Academy.\n"
            "Guide l'élève sans donner directement les réponses.\n"
            f"Niveau : {niveau_eleve}\n\n"
        )
        if historique:
            prompt += "Historique récent :\n"
            for m in historique[-5:]:
                role = "Étudiant" if m.get("role") == "user" else "Blessy AI"
                prompt += f"- {role} : {m.get('content', '')[:200]}\n"
            prompt += "\n"
        prompt += f"Message de l'élève : {message}\n\nRéponds en français, en Markdown. Sois concis mais complet."
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        return (response.text or "").strip()
    except Exception as e:
        logger.exception("Erreur chatbot tuteur")
        return f"❌ Erreur : {str(e)}"


def simuler_carriere(metier):
    """Simule une carrière : salaire, compétences, formations recommandées."""
    try:
        client = initialiser_ia()
        prompt = (
            f"Tu es un expert en orientation professionnelle pour Blessy Tech Academy.\n\n"
            f"Un étudiant s'intéresse au métier : **{metier}**\n\n"
            "Fournis une analyse complète en français. Structure TA réponse EXACTEMENT comme ceci :\n\n"
            "## 💼 Présentation du métier\n[Description du métier en 2-3 phrases]\n\n"
            "## 💰 Salaire moyen\n- Junior (0-2 ans) : [montant en USD]\n"
            "- Confirmé (3-5 ans) : [montant en USD]\n"
            "- Senior (5+ ans) : [montant en USD]\n"
            "- En Haïti : [estimation locale]\n\n"
            "## 🛠️ Compétences requises\n- Compétence 1 : description courte\n"
            "- Compétence 2 : description courte\n- Compétence 3 : description courte\n"
            "- Compétence 4 : description courte\n- Compétence 5 : description courte\n\n"
            "## 🎓 Formations recommandées à BTA\n"
            "[Suggère 2-3 formations pertinentes parmi : Développement Web, Python Fondamental, Cybersécurité, "
            "Bureautique, Design Graphique, Analyse de Données, IA & Machine Learning, Réseaux Informatiques]\n\n"
            "## 🚀 Évolution de carrière\n[Parcours type sur 5-10 ans]\n\n"
            "## 🌍 Débouchés\n[Secteurs qui recrutent, types d'entreprises]\n\n"
            "Sois réaliste, motivant et orienté vers le marché du travail en Haïti et à l'international."
        )
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        return (response.text or "").strip()
    except Exception as e:
        logger.exception("Erreur simulateur carrière")
        return f"❌ Erreur : {str(e)}"


# ================================================
# IA.PY — Analyse intelligente de la plateforme (Dashboard IA Admin)
# ================================================


def analyser_plateforme_ia(donnees_contexte):
    """
    Analyse les données réelles de BTA avec Gemini et produit des
    recommandations décisionnelles concrètes.
    """
    try:
        client = initialiser_ia()

        prompt = f"""Tu es un analyste business EdTech expert pour Blessy Tech Academy.

Voici les données réelles de la plateforme :
{donnees_contexte}

Analyse ces données et produis un rapport structuré en Markdown :

## 🔍 Constats principaux
[3-4 observations factuelles basées sur les chiffres]

## ⚠️ Alertes
[Points nécessitant une attention urgente]

## 💡 Recommandations prioritaires
[3 actions concrètes à entreprendre, classées par impact]

## 📈 Opportunités identifiées
[Ce qui fonctionne bien et pourrait être amplifié]

Sois précis, orienté action, et base-toi UNIQUEMENT sur les chiffres fournis. Réponds en français."""

        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        return response.text
    except Exception as e:
        return f"❌ Analyse indisponible : {str(e)}"


# ================================================
# Stats étudiant (utilisé par le dashboard)
# ================================================
def calculer_stats_etudiant(utilisateur):
    """Calcule les statistiques globales d'un étudiant."""
    from django.db.models import Avg, Sum

    from ..models import BadgeForum, Formation, Lecon, ProgressionLecon, ResultatQuiz

    total_lecons = Lecon.objects.count()
    lecons_terminees = ProgressionLecon.objects.filter(
        utilisateur=utilisateur, terminee=True
    ).count()
    progression_globale = round((lecons_terminees / total_lecons) * 100) if total_lecons > 0 else 0

    formations_avec_progression = []
    for formation in Formation.objects.filter(actif=True):
        pourcentage = formation.progression_pour(utilisateur)
        if pourcentage > 0:
            formations_avec_progression.append(
                {
                    "id": formation.id,
                    "nom": formation.nom,
                    "icone": formation.icone,
                    "pourcentage": pourcentage,
                    "niveau": formation.get_niveau_display(),
                }
            )

    formations_completees = [f for f in formations_avec_progression if f["pourcentage"] == 100]

    resultats_quiz = ResultatQuiz.objects.filter(utilisateur=utilisateur)
    quiz_passes = resultats_quiz.count()
    score_moyen_quiz = round(resultats_quiz.aggregate(Avg("score"))["score__avg"] or 0, 1)
    total_questions_reussies = resultats_quiz.aggregate(Sum("score"))["score__sum"] or 0
    total_questions = resultats_quiz.aggregate(Sum("total_questions"))["total_questions__sum"] or 0

    badges = list(
        BadgeForum.objects.filter(utilisateur=utilisateur).values("type_badge", "date_obtention")
    )

    en_cours = [f for f in formations_avec_progression if f["pourcentage"] < 100]

    return {
        "progression_globale": progression_globale,
        "lecons_terminees": lecons_terminees,
        "total_lecons": total_lecons,
        "formations_avec_progression": formations_avec_progression,
        "formations_completees": formations_completees,
        "en_cours": en_cours,
        "quiz_passes": quiz_passes,
        "score_moyen_quiz": score_moyen_quiz,
        "total_questions_reussies": total_questions_reussies,
        "total_questions": total_questions,
        "badges": badges,
        "certificats_disponibles": len(formations_completees),
    }


def generer_article(sujet, mots_cles=""):
    """
    Génère un article de blog pédagogique via l'IA.

    Args:
        sujet: Le sujet principal de l'article
        mots_cles: Mots-clés supplémentaires (optionnel)

    Returns:
        dict: {titre, resume, contenu, tags}
    """
    try:
        client = initialiser_ia()

        prompt = f"""
Tu es un rédacteur expert pour Blessy Tech Academy, une école de technologie en Haïti.
Rédige un article de blog pédagogique complet sur le sujet suivant : "{sujet}".
{"Mots-clés à intégrer : " + mots_cles if mots_cles else ""}

Structure TA réponse UNIQUEMENT au format JSON suivant, sans texte avant/après, sans markdown :

{{
    "titre": "Titre accrocheur et SEO-friendly",
    "resume": "Résumé de 2-3 phrases qui donne envie de lire",
    "contenu": "Contenu complet en Markdown avec ## pour les titres, **gras**, listes, etc. Minimum 500 mots.",
    "tags": "mot-clé1, mot-clé2, mot-clé3"
}}

Le contenu doit être en français, pédagogique, professionnel, et adapté au contexte haïtien et international.
Utilise un ton engageant et inclusif. Structure avec introduction, corps (2-3 sections), et conclusion.
"""
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        texte = response.text.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(texte)
    except Exception as e:
        logger.exception("Erreur génération article")
        return {"titre": "", "resume": "", "contenu": "", "tags": "", "erreur": str(e)}


# ================================================
# IA.PY — Assistant IA intégré au Back Office (aide administrateur)
# ================================================


def assistant_backoffice_ia(question, contexte_utilisateur):
    """
    Assistant conversationnel pour l'administration — aide à naviguer
    et comprendre le Back Office, différent de Blessy AI (étudiant).
    """
    try:
        client = initialiser_ia()

        prompt = f"""Tu es l'Assistant Back Office de Blessy Tech Academy — 
un copilote pour l'équipe administrative (formateurs, comptables, marketing, admin).

Contexte de l'utilisateur : {contexte_utilisateur}

Question : {question}

Tu connais l'architecture de la plateforme :
- Workflow Formation : brouillon → en_revision → validee → publiee (ou suspendue/archivee)
- Dashboards disponibles : Business (finances), Éditorial (contenu), CRM (leads), 
  IA (analyses), Gestion des cours (workspace pédagogique)
- Rôles : étudiant, formateur, modérateur, support, comptable, marketing, admin

Réponds de façon concise, actionnable, en français, avec des étapes claires 
si c'est une question "comment faire". Si tu ne connais pas la réponse exacte, 
oriente vers le bon dashboard plutôt que d'inventer."""

        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        return response.text
    except Exception as e:
        return f"❌ Assistant indisponible : {str(e)}"
