import json
import os

def charger(fichier):
    if os.path.exists(fichier):
        with open(fichier, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def sauvegarder(fichier, donnees):
    with open(fichier, "w", encoding="utf-8") as f:
        json.dump(donnees, f, indent=4, ensure_ascii=False)