# ================================================
# BLESSY TECH ACADEMY
# Gestion étudiants
# ================================================


etudiants = [
    {
        "nom": "Marie Joseph",
        "age": 19,
        "formation": "Python & Django",
        "notes": {
            "Python": 16.5,
            "HTML": 14.0,
            "CSS": 17.5,
            "JS": 15.0
        },
        "paye": True
    },

    {
        "nom": "Lucas Pierre",
        "age": 22,
        "formation": "HTML & CSS",
        "notes": {
            "Python": 9.0,
            "HTML": 11.0,
            "CSS": 8.5,
            "JS": 10.5
        },
        "paye": False
    },

    {
        "nom": "Sarah Charles",
        "age": 20,
        "formation": "Python & Django",
        "notes": {
            "Python": 19.0,
            "HTML": 17.0,
            "CSS": 18.5,
            "JS": 16.0
        },
        "paye": True
    },

    {
        "nom": "Marc Antoine",
        "age": 25,
        "formation": "Intelligence Artificielle",
        "notes": {
            "Python": 14.0,
            "HTML": 8.0,
            "CSS": 9.5,
            "JS": 11.0
        },
        "paye": True
    }
]


# Fonctions réutilisées

def calculer_moyenne(notes):
    return sum(notes.values()) / len(notes)



def mention(moyenne):

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



def decision(moyenne):

    if moyenne >= 10:
        return "✅ ADMIS"

    else:
        return "❌ AJOURNÉ"



resultats = []

formations = {}

non_payes = []


# Traitement des étudiants

for etudiant in etudiants:

    moyenne = calculer_moyenne(
        etudiant["notes"]
    )


    print("=" * 45)

    print("FICHE ÉTUDIANT")

    print("Nom :", etudiant["nom"])

    print("Âge :", etudiant["age"])

    print("Formation :", etudiant["formation"])

    print(f"Moyenne : {moyenne:.2f}/20")

    print("Mention :", mention(moyenne))

    print("Décision :", decision(moyenne))


    if etudiant["paye"]:
        print("Paiement : ✅ Payé")

    else:
        print("Paiement : ❌ Non payé")
        non_payes.append(etudiant["nom"])



    # Compteur formations

    formation = etudiant["formation"]

    formations[formation] = formations.get(
        formation, 0
    ) + 1



    # Pour classement

    resultats.append(
        (
            etudiant["nom"],
            moyenne
        )
    )



# Classement général

classement = sorted(
    resultats,
    key=lambda x: x[1],
    reverse=True
)



print("\n===== FORMATIONS =====")

print(formations)


print("\n===== ÉTUDIANTS NON PAYÉS =====")

print(non_payes)


print("\n===== CLASSEMENT =====")

for position, (nom, moyenne) in enumerate(classement, 1):

    print(
        f"{position}. {nom} : {moyenne:.2f}/20"
    )