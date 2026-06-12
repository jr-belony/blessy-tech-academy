import etudiants
import stockage

classe = stockage.charger("classe.json")

for etudiant in classe:
    moyenne = etudiants.calculer_moyenne(etudiant["notes"])
    print(f"{etudiant['nom']} : {moyenne:.2f}/20 — {etudiants.mention(moyenne)}")