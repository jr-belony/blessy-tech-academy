# Fonctionnalite developpee sur une branche dediee
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
    return "✅ ADMIS" if moyenne >= 10 else "❌ AJOURNÉ"