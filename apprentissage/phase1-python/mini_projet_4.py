
# ================================================
# BLESSY TECH ACADEMY — Générateur de Bulletins
# Auteur  : Jean Raymond BELONY
# Version : 2.0
# ================================================

classe = [
    {"nom": "Pierre Louis", "notes": [14, 13, 16, 12]},
    {"nom": "Anna Michel",  "notes": [18, 19, 17, 20]},
    {"nom": "Marc Antoine", "notes": [7,  9,  6,  8]},
    {"nom": "Diana Joseph", "notes": [11, 10, 13, 12]},
]

# --- Variables d'accumulation ---
total_moyennes = 0
admis = 0
ajournes = 0
meilleur_nom = None
meilleure_moyenne = None

# ================================================
# Bulletins individuels
# ================================================
for etudiant in classe:
    nom = etudiant["nom"]
    notes = etudiant["notes"]
    moyenne = sum(notes) / len(notes)
    total_moyennes += moyenne

    # --- Mention ---
    if moyenne >= 16:
        mention = "Très Bien"
    elif moyenne >= 14:
        mention = "Bien"
    elif moyenne >= 12:
        mention = "Assez Bien"
    elif moyenne >= 10:
        mention = "Passable"
    else:
        mention = "Insuffisant"

    # --- Décision ---
    if moyenne >= 10:
        decision = "✅ ADMIS"
        admis += 1
    else:
        decision = "❌ AJOURNÉ"
        ajournes += 1

    # --- Suivi du meilleur étudiant ---
    if meilleure_moyenne is None or moyenne > meilleure_moyenne:
        meilleure_moyenne = moyenne
        meilleur_nom = nom

    # --- Affichage du bulletin ---
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

# ================================================
# Résultats globaux de la classe
# ================================================
moyenne_classe = total_moyennes / len(classe)

print("=" * 40)
print("       RÉSULTATS DE LA CLASSE")
print("=" * 40)
print(f"  Moyenne générale  : {moyenne_classe:.2f}/20")
print(f"  Admis             : {admis}/{len(classe)}")
print(f"  Ajournés          : {ajournes}/{len(classe)}")
print(f"  Meilleur étudiant : {meilleur_nom}")
print(f"  Meilleure moyenne : {meilleure_moyenne:.2f}/20")
print("=" * 40)