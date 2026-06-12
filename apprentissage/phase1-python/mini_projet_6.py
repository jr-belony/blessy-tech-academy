
# ================================================
# BLESSY TECH ACADEMY
# Mini Projet 6 — Classement des étudiants
# ================================================

classe = [
    {"nom": "Pierre Louis", "notes": [14, 13, 16, 12]},
    {"nom": "Anna Michel",  "notes": [18, 19, 17, 20]},
    {"nom": "Marc Antoine", "notes": [7,  9,  6,  8]},
    {"nom": "Diana Joseph", "notes": [11, 10, 13, 12]},
    {"nom": "Tom Bernard",  "notes": [15, 14, 13, 16]},
]

# --- 1 et 2. Moyennes + liste de tuples ---
resultats = []
for etudiant in classe:
    nom = etudiant["nom"]
    notes = etudiant["notes"]
    moyenne = sum(notes) / len(notes)
    resultats.append((nom, moyenne))

# --- 3. Tri décroissant ---
classement = sorted(resultats, key=lambda x: x[1], reverse=True)

# --- 4. Classement complet ---
print("=" * 45)
print("       CLASSEMENT BLESSY TECH ACADEMY")
print("=" * 45)
for position, (nom, moyenne) in enumerate(classement, start=1):
    print(f"{position}. {nom} - {moyenne:.2f}/20")

# --- 5. Admis / Ajournés ---
admis = [nom for nom, moyenne in classement if moyenne >= 10]
ajournes = [nom for nom, moyenne in classement if moyenne < 10]

print("\n===== ÉTUDIANTS ADMIS =====")
print(", ".join(admis) if admis else "Aucun")

print("\n===== ÉTUDIANTS AJOURNÉS =====")
print(", ".join(ajournes) if ajournes else "Aucun")

# --- 6. Podium (robuste) ---
print("\n===== PODIUM =====")
medailles = ["🥇", "🥈", "🥉"]
nombre_podium = min(3, len(classement))

for index in range(nombre_podium):
    nom, moyenne = classement[index]
    print(f"{medailles[index]} {nom} - {moyenne:.2f}/20")