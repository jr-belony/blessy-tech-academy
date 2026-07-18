"""Utilitaires pour la gestion des XP et niveaux."""

from datetime import date

from .models import ProfilUtilisateur

XP_ACTIONS = {
    "lecon_terminee": 10,
    "module_termine": 50,  # sera déclenché manuellement ou par logique
    "formation_terminee": 200,
    "certificat_obtenu": 500,
    "sujet_forum": 20,
    "reponse_forum": 10,
    "reponse_acceptee": 50,
}


def get_profil(utilisateur):
    """Retourne le profil utilisateur, le crée si nécessaire."""
    profil, _ = ProfilUtilisateur.objects.get_or_create(utilisateur=utilisateur)
    return profil


def ajouter_xp(utilisateur, action, montant=None):
    """
    Ajoute de l'XP pour une action donnée.
    Si le montant n'est pas précisé, il est pris dans XP_ACTIONS.
    Met aussi à jour le streak journalier.
    Retourne le profil mis à jour.
    """
    if montant is None:
        montant = XP_ACTIONS.get(action, 0)

    profil = get_profil(utilisateur)
    profil.xp += montant

    # Streak : jours consécutifs
    aujourdhui = date.today()
    if profil.derniere_activite == aujourdhui:
        pass  # déjà actif aujourd'hui
    elif profil.derniere_activite == aujourdhui - date.resolution:
        profil.streak += 1
    else:
        profil.streak = 1  # reset

    profil.derniere_activite = aujourdhui
    profil.save()
    return profil
