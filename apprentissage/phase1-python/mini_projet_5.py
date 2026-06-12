
# ================================================
# BLESSY TECH ACADEMY — Fonctions de bulletin
# ================================================

def calculer_moyenne(notes):
    """Calcule la moyenne d'une liste de notes."""
    return sum(notes) / len(notes)


def attribuer_mention(moyenne):
    """Retourne la mention selon la moyenne."""
    if moyenne >= 16:
        return "Très Bien"
    elif moyenne >= 14:
        return "Bien"
    elif moyenne >= 12:
        return "Assez Bien"
    elif moyenne >= 10:
        return "Passable"
    else:
        return "Insuffisant"


def determiner_decision(moyenne):
    """Retourne ADMIS ou AJOURNÉ selon la moyenne."""
    return "✅ ADMIS" if moyenne >= 10 else "❌ AJOURNÉ"


def generer_bulletin(nom, notes):
    """Affiche le bulletin complet d'un étudiant."""
    moyenne = calculer_moyenne(notes)
    mention = attribuer_mention(moyenne)
    decision = determiner_decision(moyenne)

    print("=" * 40)
    print("           BULLETIN BTA")
    print("=" * 40)
    print(f"  Étudiant     : {nom}")
    print("-" * 40)
    for i, note in enumerate(notes, start=1):
        print(f"  Matière {i}    : {note:.2f}/20")
    print("-" * 40)
    print(f"  Moyenne      : {moyenne:.2f}/20")
    print(f"  Mention      : {mention}")
    print(f"  Décision     : {decision}")
    print()

    return moyenne   # On renvoie la moyenne pour les stats globales


# --- Programme principal ---
classe = [
    {"nom": "Pierre Louis", "notes": [14, 13, 16, 12]},
    {"nom": "Anna Michel",  "notes": [18, 19, 17, 20]},
]

for etudiant in classe:
    moyenne = generer_bulletin(etudiant["nom"], etudiant["notes"])
    print(f"(Moyenne enregistrée pour les stats : {moyenne:.2f})")