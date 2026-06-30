import google.generativeai as genai
from django.conf import settings
import json


def initialiser_ia():
    """Configure le SDK Gemini avec la clé API."""
    genai.configure(api_key=settings.GEMINI_API_KEY)
    return genai.GenerativeModel('gemini-2.5-flash')


def construire_prompt_chat(question, historique=None, contexte_utilisateur=None, formations_disponibles=None):
    """Construit un prompt contextualisé pour Blessy AI."""
    prompt = """
Tu es Blessy AI, l'assistant intelligent de Blessy Tech Academy.
Tu aides les étudiants à choisir leurs formations et à progresser.
Tu réponds toujours en français, avec bienveillance et professionnalisme.
Sois concis, clair et orienté vers l'action.
"""

    if contexte_utilisateur:
        prompt += f"\nContexte utilisateur :\n- Prénom : {contexte_utilisateur.get('prenom', '')}\n"
        formations_suivies = contexte_utilisateur.get('formations_suivies', [])
        if formations_suivies:
            prompt += "- Formations déjà suivies : " + ", ".join(formations_suivies) + "\n"

    if historique:
        prompt += "\nHistorique de conversation :\n"
        for message in historique[-8:]:
            role = "Étudiant" if message.get('role') == 'user' else "Blessy AI"
            prompt += f"- {role} : {message.get('content', '')}\n"

    if formations_disponibles:
        prompt += "\nFormations disponibles :\n"
        for formation in formations_disponibles[:5]:
            prompt += f"- {formation.nom} ({formation.duree_mois} mois, {formation.prix} USD)\n"

    prompt += f"\nQuestion actuelle de l'étudiant : {question}"
    return prompt


def repondre_chat_ia(question, historique=None, contexte_utilisateur=None, formations_disponibles=None):
    """Répond à une question avec contexte et historique de conversation."""
    try:
        model = initialiser_ia()
        prompt = construire_prompt_chat(
            question=question,
            historique=historique,
            contexte_utilisateur=contexte_utilisateur,
            formations_disponibles=formations_disponibles,
        )
        reponse = model.generate_content(prompt)
        texte = (reponse.text or "").strip()
        return texte or "Je n'ai pas pu générer une réponse précise pour le moment. Réessaie dans quelques secondes."
    except Exception:
        return "Désolé, le chatbot est temporairement indisponible. Vous pouvez nous contacter sur contact@blessyconnect.com."


def blessy_ai_repondre(question, contexte_formations=None, historique=None, contexte_utilisateur=None):
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

    except Exception:
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


def generer_contenu_lecon(titre_lecon, resume_lecon="", contexte_formation="", contexte_module=""):
    """
    Génère le contenu complet d'une leçon individuelle.

    Args:
        titre_lecon: Titre de la leçon
        resume_lecon: Résumé existant (contexte)
        contexte_formation: Nom de la formation parente
        contexte_module: Nom du module parent

    Returns:
        str: Contenu complet de la leçon (texte structuré)
    """
    try:
        model = initialiser_ia()

        prompt = f"""
Tu es un formateur expert de Blessy Tech Academy, une école de
technologie professionnelle en Haïti.

Rédige le contenu COMPLET d'une leçon de cours pour :

Formation : {contexte_formation}
Module : {contexte_module}
Leçon : "{titre_lecon}"
{f'Résumé prévu : {resume_lecon}' if resume_lecon else ''}

Structure obligatoire du contenu (utilise ces titres exacts) :

## Explication
[Explique le concept clairement, avec des mots simples,
adapté à un débutant motivé. 2-4 paragraphes.]

## Exemple concret
[Donne un exemple pratique et réaliste. Si c'est un sujet
technique/code, inclus un bloc de code avec des commentaires.
Si c'est un sujet non-technique, donne un cas d'usage réel.]

## Mini-exercice
[Propose un petit exercice pratique que l'étudiant peut faire
immédiatement pour appliquer ce qu'il vient d'apprendre.
Donne aussi la solution ou la démarche attendue.]

Réponds uniquement avec le contenu de la leçon en français,
en utilisant le format Markdown (## pour les titres,
```code``` pour le code si nécessaire, **gras** pour les points clés).
Sois pédagogique, concret, et engageant. Ne mets pas de texte
d'introduction ou de conclusion en dehors de cette structure.
"""
        reponse = model.generate_content(prompt)
        return reponse.text.strip()

    except Exception as e:
        return f"Erreur lors de la génération : {str(e)}"


def generer_parcours_oriente(profil, objectif, disponibilite, details, formations_disponibles):
    """
    Génère un parcours personnalisé basé sur le profil de l'étudiant.
    """
    try:
        model = initialiser_ia()

        formations_texte = "\n".join([
            f"- ID:{f.id} | {f.nom} ({f.duree_mois} mois, {f.prix} USD) | "
            f"Niveau: {f.niveau} | École: {f.ecole}"
            for f in formations_disponibles
        ])

        prompt = f"""
Tu es Blessy AI, conseiller pédagogique expert de Blessy Tech Academy en Haïti.

Un étudiant a rempli son profil :
- Profil : {profil}
- Objectif principal : {objectif}
- Disponibilité : {disponibilite}
- Détails personnels : "{details}"

Formations disponibles à BTA :
{formations_texte}

Crée un parcours personnalisé et progressif pour cet étudiant.

Réponds UNIQUEMENT en JSON valide, sans markdown, au format EXACT :

{{
    "message_personnel": "Message d'encouragement personnalisé (2-3 phrases, chaleureux)",
    "duree_totale": 12,
    "budget_total": 650,
    "etapes": [
        {{
            "ordre": 1,
            "formation_id": 5,
            "formation_nom": "Bureautique Professionnelle",
            "formation_icone": "📊",
            "raison": "Pourquoi cette formation en premier (1 phrase)",
            "duree_mois": 3,
            "prix": 150
        }}
    ]
}}

Règles :
- Choisis entre 2 et 5 formations dans l'ordre logique de progression
- Utilise UNIQUEMENT les formations disponibles (avec leur ID exact)
- Adapte le parcours à la disponibilité (moins de temps = moins de formations)
- Sois précis et encourageant
- Réponds en français
"""
        reponse = model.generate_content(prompt)
        texte = reponse.text.strip()
        texte = texte.replace('```json', '').replace('```', '').strip()

        resultat = json.loads(texte)
        return resultat

    except Exception as e:
        return {'erreur': str(e)}


def attribuer_badges(utilisateur):
    """
    Vérifie et attribue automatiquement TOUS les badges (forum + apprentissage).
    Retourne la liste des nouveaux badges attribués.
    """
    from .models import BadgeForum, Sujet, Reponse, Reaction, ResultatQuiz, ProgressionLecon, Lecon, Formation

    nouveaux_badges = []
    badges_existants = set(BadgeForum.objects.filter(utilisateur=utilisateur).values_list('type_badge', flat=True))

    # --- Badges Forum ---
    nb_sujets = Sujet.objects.filter(auteur=utilisateur).count()
    nb_reponses = Reponse.objects.filter(auteur=utilisateur).count()
    nb_solutions = Reponse.objects.filter(auteur=utilisateur, acceptee=True).count()
    nb_likes_recus = Reaction.objects.filter(reponse__auteur=utilisateur).count()

    forum_badges = [
        ('premier_post', nb_sujets >= 1),
        ('premiere_reponse', nb_reponses >= 1),
        ('solution_acceptee', nb_solutions >= 1),
        ('dix_reponses', nb_reponses >= 10),
        ('cinquante_reponses', nb_reponses >= 50),
        ('cent_likes', nb_likes_recus >= 100),
        ('sujet_populaire', Sujet.objects.filter(auteur=utilisateur, vues__gte=500).exists()),
    ]

    # --- Badges Apprentissage ---
    quiz_reussis = ResultatQuiz.objects.filter(utilisateur=utilisateur)
    nb_quiz_reussis = sum(1 for q in quiz_reussis if q.pourcentage() >= 70)

    lecons_terminees = ProgressionLecon.objects.filter(utilisateur=utilisateur, terminee=True)
    nb_lecons = lecons_terminees.count()
    heures_apprentissage = nb_lecons * 0.5  # ~30 min par leçon

    formations_completees = []
    for formation in Formation.objects.filter(actif=True):
        if formation.progression_pour(utilisateur) == 100:
            formations_completees.append(formation)

    nb_formations = len(formations_completees)

    apprentissage_badges = [
        ('premier_quiz', nb_quiz_reussis >= 1),
        ('cinq_quiz', nb_quiz_reussis >= 5),
        ('dix_heures', heures_apprentissage >= 10),
        ('cinquante_heures', heures_apprentissage >= 50),
        ('premiere_formation', nb_formations >= 1),
        ('trois_formations', nb_formations >= 3),
    ]

    # --- Badges Compétences ---
    formations_noms = [f.nom.lower() for f in formations_completees]
    progression_noms = []
    for p in ProgressionLecon.objects.filter(utilisateur=utilisateur, terminee=True).select_related('lecon__module__formation'):
        nom = p.lecon.module.formation.nom.lower()
        if nom not in progression_noms:
            progression_noms.append(nom)

    competences_badges = [
        ('expert_python', 'python' in progression_noms),
        ('expert_web', any(m in ' '.join(formations_noms) for m in ['web', 'html', 'css', 'javascript'])),
        ('expert_data', any(m in ' '.join(formations_noms) for m in ['donnée', 'data', 'analyse'])),
        ('expert_cyber', 'cybersécurité' in ' '.join(formations_noms)),
        ('expert_design', any(m in ' '.join(formations_noms) for m in ['design', 'graphique', 'création'])),
    ]

    # --- Badges Projet ---
    # Basé sur les formations complétées (une formation = un projet)
    projets_badges = [
        ('projet_termine', nb_formations >= 1),
        ('trois_projets', nb_formations >= 3),
    ]

    # --- Badges Social ---
    profile_complet = all([
        utilisateur.first_name,
        utilisateur.last_name,
        utilisateur.email,
    ])

    social_badges = [
        ('profile_complet', profile_complet),
        ('premier_certificat', nb_formations >= 1),
        ('membre_actif', nb_reponses >= 5 or nb_sujets >= 3 or nb_quiz_reussis >= 3),
    ]

    # Attribuer tous les badges mérités
    tous_badges = forum_badges + apprentissage_badges + competences_badges + projets_badges + social_badges

    for type_badge, condition in tous_badges:
        if condition and type_badge not in badges_existants:
            BadgeForum.objects.create(utilisateur=utilisateur, type_badge=type_badge)
            nouveaux_badges.append(type_badge)
            badges_existants.add(type_badge)

    return nouveaux_badges


# Garder l'ancienne fonction pour rétrocompatibilité
def attribuer_badges_forum(utilisateur):
    """Ancienne fonction - appelle la nouvelle."""
    return attribuer_badges(utilisateur)



# ================================================
# FONCTIONS IA POUR LE BOUTON IA (6 fonctionnalités)
# ================================================

def assistant_code(code, langage="python", question=""):
    """
    Fonction 1 : Assistant Code
    L'élève colle son code, l'IA analyse, corrige et explique.
    """
    try:
        model = initialiser_ia()

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
            "(## Analyse, ## Erreurs trouvées, ## Code corrigé, "
            "## Bonnes pratiques, ## Conseil).\n"
            "Sois pédagogue, bienveillant et encourageant."
        )

        reponse = model.generate_content(prompt)
        return (reponse.text or "").strip()
    except Exception as e:
        return f"❌ Erreur lors de l'analyse : {str(e)}"


def generateur_exercices(sujet, niveau="debutant", format_exercice="code"):
    """
    Fonction 2 : Générateur d'exercices personnalisés
    Crée un exercice selon le niveau et le sujet.
    """
    try:
        model = initialiser_ia()

        prompt = (
            f"Tu es un générateur d'exercices pour Blessy Tech Academy.\n"
            f"Crée un exercice personnalisé avec les critères suivants :\n\n"
            f"- Sujet : {sujet}\n"
            f"- Niveau : {niveau}\n"
            f"- Format : {format_exercice}\n\n"
            "Structure ta réponse en Markdown :\n"
            "## 🎯 Exercice : [Titre]\n"
            "## 📋 Consignes\n"
            "[Consignes claires et détaillées]\n"
            "## 💡 Indices (optionnel pour niveau débutant/intermédiaire)\n"
            "[1-2 indices sans donner la solution]\n"
            "## ✅ Résultat attendu\n"
            "[Description du résultat ou exemple de sortie]\n"
            "## 📝 Corrigé type\n"
            "[Solution complète et commentée]\n\n"
            "Adapte la difficulté au niveau (débutant = très guidé, "
            "intermédiaire = moyennement guidé, avancé = autonome).\n"
            "Si format = 'qcm', génère un QCM avec 4 choix et la bonne réponse.\n"
            "Sois pédagogue et encourageant. Réponds en français."
        )

        reponse = model.generate_content(prompt)
        return (reponse.text or "").strip()
    except Exception as e:
        return f"❌ Erreur lors de la génération : {str(e)}"


def explication_concept(question, niveau_eleve="debutant"):
    """
    Fonction 3 : Explication de concept
    L'élève pose une question, l'IA explique avec des exemples.
    """
    try:
        model = initialiser_ia()

        prompt = (
            f"Tu es un tuteur expert de Blessy Tech Academy.\n"
            f"Un étudiant de niveau {niveau_eleve} te demande :\n"
            f'"{question}"\n\n'
            "Tu dois :\n"
            "1. Donner une définition simple et claire du concept\n"
            "2. Fournir un exemple concret (code si pertinent)\n"
            "3. Expliquer quand et pourquoi on utilise ce concept\n"
            "4. Mentionner les erreurs fréquentes à éviter\n"
            "5. Proposer une analogie si possible pour faciliter la compréhension\n\n"
            "Structure ta réponse en Markdown :\n"
            "## 📖 Définition\n"
            "## 💻 Exemple concret\n"
            "## 🎯 Cas d'usage\n"
            "## ⚠️ Erreurs à éviter\n"
            "## 💡 Pour aller plus loin\n\n"
            "Adapte ton langage au niveau de l'étudiant.\n"
            "Sois pédagogue, clair et encourageant. Réponds en français."
        )

        reponse = model.generate_content(prompt)
        return (reponse.text or "").strip()
    except Exception as e:
        return f"❌ Erreur lors de l'explication : {str(e)}"


def correction_automatique(enonce, reponse_eleve, bareme=""):
    """
    Fonction 4 : Correction automatique
    Évalue la réponse d'un élève à un exercice.
    """
    try:
        model = initialiser_ia()

        prompt = (
            f"Tu es un correcteur pédagogique de Blessy Tech Academy.\n\n"
            f"## Énoncé de l'exercice :\n{enonce}\n\n"
            f"## Réponse de l'étudiant :\n{reponse_eleve}\n\n"
        )
        if bareme:
            prompt += f"## Barème suggéré : {bareme}\n\n"

        prompt += (
            "Tu dois :\n"
            "1. Évaluer la réponse avec une note sur 20\n"
            "2. Lister les points positifs (ce qui est bien fait)\n"
            "3. Identifier les erreurs et axes d'amélioration\n"
            "4. Donner un feedback constructif et encourageant\n"
            "5. Suggérer ce qu'il faut réviser si la note < 12\n\n"
            "Structure ta réponse en Markdown :\n"
            "## 📊 Note : [X]/20\n"
            "## ✅ Points positifs\n"
            "## 🔧 À améliorer\n"
            "## 💬 Feedback personnalisé\n"
            "## 📚 À réviser (si nécessaire)\n\n"
            "Sois juste, constructif et encourageant. "
            "L'objectif est d'aider l'étudiant à progresser.\n"
            "Réponds en français."
        )

        reponse = model.generate_content(prompt)
        return (reponse.text or "").strip()
    except Exception as e:
        return f"❌ Erreur lors de la correction : {str(e)}"


def parcours_adaptatif(profil_scores, parcours_actuel="", objectif=""):
    """
    Fonction 5 : Parcours adaptatif
    Recommande les prochaines leçons selon les résultats.
    """
    try:
        model = initialiser_ia()

        profil_texte = "\n".join([
            f"- {sujet} : {score}%" for sujet, score in profil_scores.items()
        ])

        prompt = (
            f"Tu es un conseiller pédagogique IA de Blessy Tech Academy.\n\n"
            f"## Profil de l'étudiant (scores par sujet) :\n"
            f"{profil_texte}\n\n"
            f"## Parcours actuel : "
            f"{parcours_actuel if parcours_actuel else 'Non spécifié'}\n"
            f"## Objectif : {objectif if objectif else 'Non spécifié'}\n\n"
            "Analyse les forces et faiblesses, puis recommande un plan "
            "d'action personnalisé.\n\n"
            "Structure ta réponse en Markdown :\n"
            "## 📊 Analyse du profil\n"
            "[Forces identifiées, points à renforcer]\n\n"
            "## 🎯 Recommandations\n"
            "[3 leçons ou sujets recommandés avec justification pour chacun]\n\n"
            "## 📝 Plan d'action\n"
            "[Progression suggérée sur les 2-4 prochaines semaines]\n\n"
            "## 💪 Conseil de motivation\n"
            "[Un message encourageant personnalisé]\n\n"
            "Sois précis, data-driven et encourageant. Réponds en français."
        )

        reponse = model.generate_content(prompt)
        return (reponse.text or "").strip()
    except Exception as e:
        return f"❌ Erreur lors de l'analyse : {str(e)}"


def chatbot_tuteur(message, historique=None, niveau_eleve="debutant"):
    """
    Fonction 6 : Chatbot tuteur conversationnel
    Guide l'élève dans son apprentissage de manière interactive.
    """
    try:
        model = initialiser_ia()

        prompt = (
            "Tu es Blessy AI, tuteur IA bienveillant de Blessy Tech Academy.\n"
            "Ton rôle est d'accompagner les étudiants dans leur apprentissage.\n\n"
            f"## Contexte :\n"
            f"- Niveau de l'étudiant : {niveau_eleve}\n"
            "- Tu es un guide, pas un faiseur de devoirs\n"
            "- Encourage la réflexion plutôt que donner directement les réponses\n\n"
            "## Directives :\n"
            "1. Sois chaleureux, patient et encourageant\n"
            "2. Pose des questions pour guider la réflexion\n"
            "3. Donne des indices plutôt que des solutions complètes\n"
            "4. Félicite les efforts et les progrès\n"
            "5. Suggère des ressources complémentaires si pertinent\n\n"
        )

        if historique:
            prompt += "## Historique récent :\n"
            for m in historique[-5:]:
                role = "Étudiant" if m.get('role') == 'user' else "Blessy AI"
                content = m.get('content', '')[:200]
                prompt += f"- {role} : {content}\n"
            prompt += "\n"
        else:
            prompt += "Nouvelle conversation\n\n"

        prompt += (
            f"## Message de l'étudiant :\n"
            f"{message}\n\n"
            "Réponds en français, en Markdown. Sois concis mais complet."
        )

        reponse = model.generate_content(prompt)
        return (reponse.text or "").strip()
    except Exception as e:
        return f"❌ Erreur : {str(e)}"
    

def calculer_stats_etudiant(utilisateur):
    """
    Calcule les statistiques globales d'un étudiant.
    Retourne un dict avec progression, quiz, badges, score, etc.
    """
    from .models import (
        Formation, ProgressionLecon, ResultatQuiz, 
        BadgeForum, Lecon, Inscription
    )
    from django.db.models import Avg, Sum

    # Progression globale
    total_lecons = Lecon.objects.count()
    lecons_terminees = ProgressionLecon.objects.filter(
        utilisateur=utilisateur, terminee=True
    ).count()
    progression_globale = round((lecons_terminees / total_lecons) * 100) if total_lecons > 0 else 0

    # Formations avec progression
    formations_avec_progression = []
    for formation in Formation.objects.filter(actif=True):
        pourcentage = formation.progression_pour(utilisateur)
        if pourcentage > 0:
            formations_avec_progression.append({
                'id': formation.id,
                'nom': formation.nom,
                'icone': formation.icone,
                'pourcentage': pourcentage,
                'niveau': formation.get_niveau_display(),
            })

    # Formations complétées (100%)
    formations_completees = [f for f in formations_avec_progression if f['pourcentage'] == 100]

    # Quiz
    resultats_quiz = ResultatQuiz.objects.filter(utilisateur=utilisateur)
    quiz_passes = resultats_quiz.count()
    score_moyen_quiz = round(resultats_quiz.aggregate(Avg('score'))['score__avg'] or 0, 1)
    total_questions_reussies = resultats_quiz.aggregate(Sum('score'))['score__sum'] or 0
    total_questions = resultats_quiz.aggregate(Sum('total_questions'))['total_questions__sum'] or 0

    # Badges forum
    badges = list(BadgeForum.objects.filter(utilisateur=utilisateur).values('type_badge', 'date_obtention'))

    # Formations en cours (progression > 0 et < 100)
    en_cours = [f for f in formations_avec_progression if f['pourcentage'] < 100]

    return {
        'progression_globale': progression_globale,
        'lecons_terminees': lecons_terminees,
        'total_lecons': total_lecons,
        'formations_avec_progression': formations_avec_progression,
        'formations_completees': formations_completees,
        'en_cours': en_cours,
        'quiz_passes': quiz_passes,
        'score_moyen_quiz': score_moyen_quiz,
        'total_questions_reussies': total_questions_reussies,
        'total_questions': total_questions,
        'badges': badges,
        'certificats_disponibles': len(formations_completees),
    }


def simuler_carriere(metier):
    """
    Simule une carrière : salaire, compétences, formations recommandées.
    """
    try:
        model = initialiser_ia()

        prompt = (
            f"Tu es un expert en orientation professionnelle pour Blessy Tech Academy.\n\n"
            f"Un étudiant s'intéresse au métier : **{metier}**\n\n"
            "Fournis une analyse complète en français. Structure TA réponse EXACTEMENT comme ceci :\n\n"
            "## 💼 Présentation du métier\n"
            "[Description du métier en 2-3 phrases]\n\n"
            "## 💰 Salaire moyen\n"
            "- Junior (0-2 ans) : [montant en USD]\n"
            "- Confirmé (3-5 ans) : [montant en USD]\n"
            "- Senior (5+ ans) : [montant en USD]\n"
            "- En Haïti : [estimation locale]\n\n"
            "## 🛠️ Compétences requises\n"
            "- Compétence 1 : description courte\n"
            "- Compétence 2 : description courte\n"
            "- Compétence 3 : description courte\n"
            "- Compétence 4 : description courte\n"
            "- Compétence 5 : description courte\n\n"
            "## 🎓 Formations recommandées à BTA\n"
            "[Suggère 2-3 formations pertinentes parmi : Développement Web, "
            "Python Fondamental, Cybersécurité, Bureautique, Design Graphique, "
            "Analyse de Données, IA & Machine Learning, Réseaux Informatiques]\n\n"
            "## 🚀 Évolution de carrière\n"
            "[Parcours type sur 5-10 ans]\n\n"
            "## 🌍 Débouchés\n"
            "[Secteurs qui recrutent, types d'entreprises]\n\n"
            "Sois réaliste, motivant et orienté vers le marché du travail en Haïti et à l'international."
        )

        reponse = model.generate_content(prompt)
        return (reponse.text or "").strip()
    except Exception as e:
        return f"❌ Erreur : {str(e)}"