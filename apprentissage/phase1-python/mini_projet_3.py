# ================================================
# BLESSY TECH ACADEMY — Bulletin de Notes
# ================================================

# Données d'un étudiant
nom = "Jean Pierre"
note_python = 15.5
note_html = 12.0
note_css = 17.0
note_javascript = 9.5
a_paye_frais = True

# 1. Calcul de la moyenne
moyenne = (note_python + note_html + note_css + note_javascript) / 4

# 2. Attribution de la mention
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

# 3. Décision d'admission
if moyenne >= 10:
    decision = "✅ ADMIS"
else:
    decision = "❌ AJOURNÉ"

# 4. Recherche de la meilleure et de la plus faible note
notes = {
    "Python": note_python,
    "HTML": note_html,
    "CSS": note_css,
    "JavaScript": note_javascript
}

matiere_meilleure = max(notes, key=notes.get)
meilleure_note = notes[matiere_meilleure]

matiere_faible = min(notes, key=notes.get)
plus_faible_note = notes[matiere_faible]

# 5. Affichage du bulletin
print("=" * 48)
print("         BLESSY TECH ACADEMY")
print("         Bulletin de Notes — 2025")
print("=" * 48)

print(f"Étudiant     : {nom}")

print("-" * 48)
print(f"Python       : {note_python:.2f}/20")
print(f"HTML         : {note_html:.2f}/20")
print(f"CSS          : {note_css:.2f}/20")
print(f"JavaScript   : {note_javascript:.2f}/20")

print("-" * 48)
print(f"Moyenne      : {moyenne:.2f}/20")
print(f"Mention      : {mention}")
print(f"Meilleure    : {matiere_meilleure} ({meilleure_note:.2f})")
print(f"Plus faible  : {matiere_faible} ({plus_faible_note:.2f})")

print("=" * 48)
print(f"DÉCISION     : {decision}")
print("=" * 48)

# 6. Vérification du paiement
if not a_paye_frais:
    print("⚠ AVERTISSEMENT : Les frais scolaires ne sont pas payés.")