# ================================================
# _HELPER_SEED_IDEMPOTENT.PY — Fonction de création sécurisée réutilisable
# Empêche tout doublon même si un script est relancé plusieurs fois 
# ou s'était arrêté en cours de route
# ================================================

from academie.models_banque import QuestionBanque


def creer_question_si_absente(module, categorie, q, stdout_style=None):
    """
    Crée la question UNIQUEMENT si aucune question avec le même 
    énoncé exact n'existe déjà dans cette catégorie — évite les 
    doublons sur relance, comble automatiquement les trous.
    Retourne True si créée, False si déjà existante (ignorée).
    """
    existe_deja = QuestionBanque.objects.filter(
        module=module, categorie=categorie, enonce=q['enonce']
    ).exists()

    if existe_deja:
        return False

    QuestionBanque.objects.create(
        module=module, categorie=categorie, niveau=q['niveau'], type_question=q['type'],
        enonce=q['enonce'], reponses_possibles=q.get('reponses', []),
        reponse_texte_courte=q.get('reponse_texte_courte', ''),
        explication_pedagogique=q['explication'], mots_cles=q.get('mots_cles', ''),
        statut='active',
    )
    return True