"""Base de connaissances locale pour Blessy AI.
Utilisée en secours si l'API Gemini est injoignable.
"""

QUESTIONS_FREQUENTES = [
    {
        "mots_cles": ["parcours", "conseillez", "choisir", "formation"],
        "reponse": (
            "Je te conseille de commencer par le parcours **Développement Web** si tu es débutant, "
            "ou **Python Fondamental** pour te lancer dans la programmation. "
            "Tu peux aussi utiliser notre simulateur de carrière pour une recommandation personnalisée 🚀"
        )
    },
    {
        "mots_cles": ["formations", "demandées", "populaires", "tendance"],
        "reponse": (
            "Les formations les plus demandées en ce moment sont **Développement Web**, "
            "**Cybersécurité** et **Analyse de Données**. "
            "Toutes nos formations sont disponibles sur la page Formations."
        )
    },
    {
        "mots_cles": ["prix", "coût", "tarif", "gratuit"],
        "reponse": (
            "Nos formations varient de 0$ (gratuites) à 500$ selon le niveau. "
            "Nous proposons aussi des facilités de paiement. Contacte-nous pour plus d'infos !"
        )
    },
    {
        "mots_cles": ["certificat", "diplôme", "certification"],
        "reponse": (
            "Oui, toutes nos formations donnent droit à un **certificat PDF** téléchargeable "
            "lorsque tu as terminé 100% du programme. Tu peux le partager sur LinkedIn."
        )
    },
    {
        "mots_cles": ["durée", "temps", "mois"],
        "reponse": (
            "La durée des formations varie de 1 à 6 mois selon le sujet. "
            "Tu peux voir la durée exacte sur la page de chaque formation."
        )
    },
    {
        "mots_cles": ["prérequis", "niveau", "débutant"],
        "reponse": (
            "La plupart de nos formations sont ouvertes aux débutants. "
            "Aucun prérequis technique n'est nécessaire pour commencer."
        )
    },
    {
        "mots_cles": ["compte", "inscription", "connecter"],
        "reponse": (
            "Pour t'inscrire, clique sur 'Créer un compte' en haut de la page. "
            "C'est gratuit et rapide !"
        )
    },
    {
        "mots_cles": ["forum", "communauté", "aide"],
        "reponse": (
            "Nous avons un forum communautaire où tu peux poser tes questions "
            "et aider les autres étudiants. Rejoins-nous !"
        )
    },
    {
        "mots_cles": ["badge", "badges", "récompense"],
        "reponse": (
            "Tu gagnes des badges en progressant dans les formations, "
            "en participant au forum ou en réussissant des quiz. Consulte ton dashboard !"
        )
    },
    {
        "mots_cles": ["quiz", "évaluation", "test"],
        "reponse": (
            "Chaque formation contient des quiz pour tester tes connaissances. "
            "Tu peux les retrouver sur la page de la formation."
        )
    },
    {
        "mots_cles": ["projet", "portfolio"],
        "reponse": (
            "Tu peux ajouter tes projets dans ton portfolio pour attirer les recruteurs. "
            "Va dans 'Mon Portfolio' depuis ton dashboard."
        )
    },
    {
        "mots_cles": ["carrière", "métier", "simulateur"],
        "reponse": (
            "Utilise notre simulateur de carrière pour découvrir les salaires, "
            "compétences et formations nécessaires pour différents métiers IT."
        )
    },
]


def rechercher_reponse_locale(question):
    """Recherche une réponse dans la base de connaissances locale.
    Retourne la meilleure réponse trouvée, ou None si rien ne correspond.
    """
    question = question.lower()
    meilleur_score = 0
    meilleure_reponse = None

    for item in QUESTIONS_FREQUENTES:
        score = 0
        for mot in item["mots_cles"]:
            if mot in question:
                score += 1
        if score > meilleur_score:
            meilleur_score = score
            meilleure_reponse = item["reponse"]

    if meilleur_score > 0:
        return meilleure_reponse
    return None