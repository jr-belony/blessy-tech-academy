# ================================================
# BLESSY TECH ACADEMY — Fiche d'Inscription 2025
# Auteur  : Jean Raymond BELONY
# Version : 1.0
# ================================================

# --- Informations personnelles ---
nom_complet = "Jean Dupont"
age = 30
ville = "Paris"

# --- Formation choisie ---
formation = "Développement Web Full-Stack"
duree = "6 mois"
prix = 300
reduction = 0.15

# --- Calculs automatiques ---
montant_reduction = prix * reduction
prix_final = prix - montant_reduction

# --- Affichage de la fiche ---
print("=" * 48)
print("         BLESSY TECH ACADEMY")
print("         Fiche d'Inscription 2025")
print("=" * 48)
print("  INFORMATIONS PERSONNELLES")
print("-" * 48)
print(f"  Nom complet  : {nom_complet}")
print(f"  Âge          : {age} ans")
print(f"  Ville        : {ville}")
print("=" * 48)
print("  FORMATION CHOISIE")
print("-" * 48)
print(f"  Intitulé     : {formation}")
print(f"  Durée        : {duree}")
print(f"  Prix         : {prix:.2f} USD")
print(f"  Réduction    : {reduction * 100:.0f}%")
print(f"  Prix final   : {prix_final:.2f} USD")
print("=" * 48)
print("  STATUT       : ✅ Inscription confirmée")
print("=" * 48)