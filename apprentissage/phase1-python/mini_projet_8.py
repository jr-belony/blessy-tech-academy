
import json
import csv
import os

FICHIER_JSON = "inscriptions.json"
FICHIER_CSV = "inscriptions.csv"


# ================================================
# Fonctions JSON
# ================================================

def charger_inscriptions():
    """Charge les inscriptions depuis le fichier, ou liste vide si absent."""
    if os.path.exists(FICHIER_JSON):
        with open(FICHIER_JSON, "r", encoding="utf-8") as fichier:
            return json.load(fichier)
    return []


def sauvegarder_inscriptions(liste):
    """Sauvegarde la liste complète dans le fichier JSON."""
    with open(FICHIER_JSON, "w", encoding="utf-8") as fichier:
        json.dump(liste, fichier, indent=4, ensure_ascii=False)


def inscription_existe(liste, nom, formation):
    """Vérifie si cette personne est déjà inscrite à cette formation."""
    for inscription in liste:
        if inscription["nom"] == nom and inscription["formation"] == formation:
            return True
    return False


def ajouter_inscription(liste, nom, formation, montant_paye):
    """Ajoute une inscription si elle n'existe pas déjà, puis sauvegarde."""
    if inscription_existe(liste, nom, formation):
        print(f"⚠️  {nom} est déjà inscrit à '{formation}' — ignoré.")
        return

    inscription = {"nom": nom, "formation": formation, "montant_paye": montant_paye}
    liste.append(inscription)
    sauvegarder_inscriptions(liste)
    print(f"✅ {nom} ajouté et sauvegardé.")


def afficher_toutes_inscriptions(liste):
    print("\n===== INSCRIPTIONS BTA =====")
    for inscription in liste:
        print(f"{inscription['nom']} - {inscription['formation']} - {inscription['montant_paye']} USD")


# ================================================
# Export CSV
# ================================================

def exporter_csv(liste):
    with open(FICHIER_CSV, "w", newline="", encoding="utf-8") as fichier:
        colonnes = ["nom", "formation", "montant_paye"]
        writer = csv.DictWriter(fichier, fieldnames=colonnes)
        writer.writeheader()
        writer.writerows(liste)


# ================================================
# Programme principal
# ================================================

inscriptions = charger_inscriptions()
print(f"Inscriptions déjà enregistrées : {len(inscriptions)}")

nouveaux = [
    ("Pierre Louis", "Python & Django", 300),
    ("Anna Michel", "Intelligence Artificielle", 350),
    ("Tom Bernard", "HTML & CSS", 200),
]

for nom, formation, montant in nouveaux:
    ajouter_inscription(inscriptions, nom, formation, montant)

afficher_toutes_inscriptions(inscriptions)

# --- Statistiques ---
total_inscriptions = len(inscriptions)
montant_total = sum(i["montant_paye"] for i in inscriptions)

print(f"\nNombre total : {total_inscriptions}")
print(f"Montant total collecté : {montant_total} USD")

# --- Export CSV ---
exporter_csv(inscriptions)