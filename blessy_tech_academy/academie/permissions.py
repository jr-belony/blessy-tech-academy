# ================================================
# PERMISSIONS.PY — Décorateurs RBAC + Matrice explicite (CORRECTIF #1)
# ================================================

from functools import wraps
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect
from django.contrib import messages

# ================================================
# CORRECTIF #1 — Matrice RBAC explicite
# Centralise TOUTES les règles d'autorisation en un seul endroit lisible
# ================================================

MATRICE_RBAC = {
    # --- Catalogue / Pédagogie ---
    'formation.creer': ['admin', 'formateur'],
    'formation.publier': ['admin'],  # seul admin peut PUBLIER (formateur peut créer/proposer)
    'formation.supprimer': ['admin'],
    'module.gerer': ['admin', 'formateur'],
    'lecon.gerer': ['admin', 'formateur'],
    'quiz.gerer': ['admin', 'formateur'],
    'examen.gerer': ['admin', 'formateur'],
    'examen.corriger_manuellement': ['admin', 'formateur'],

    # --- Certification (verrouillage strict — sensible institutionnellement) ---
    'certificat.emettre': ['admin'],
    'certificat.revoquer': ['admin'],
    'certificat.consulter_registre': ['admin', 'comptable'],
    # ================================================
    # NOUVEAU — Validation paiement cohorte (superadmin uniquement)
    # ================================================
    'certificat_cohorte.valider_paiement': ['admin'],  # 'admin' = rôle superadmin

    # --- Commerce ---
    'paiement.valider': ['admin', 'comptable'],
    'paiement.rembourser': ['admin', 'comptable'],
    'coupon.creer': ['admin', 'comptable', 'marketing'],
    'affiliation.gerer': ['admin', 'comptable'],

    # --- CRM / Marketing ---
    'lead.gerer': ['admin', 'marketing', 'support'],
    'article.publier': ['admin', 'marketing'],

    # --- Forum ---
    'forum.moderer': ['admin', 'moderateur'],

    # --- Gouvernance ---
    'role.modifier': ['admin'],
    'logs_audit.consulter': ['admin'],
    'partenaire_api.gerer': ['admin'],
}


def peut(utilisateur, action, objet=None, academie=None):
    """
    Point d'entrée UNIQUE pour toute vérification de permission métier.
    Usage : if peut(request.user, 'formation.publier'): ...

    Scope académie : si un objet/académie est fourni, vérifie EN PLUS 
    que l'utilisateur appartient bien à cette académie (isolation multi-tenant).
    """
    if not utilisateur.is_authenticated:
        return False
    if utilisateur.is_superuser:
        return True

    profil = getattr(utilisateur, 'profil', None)
    if not profil:
        return False

    roles_autorises = MATRICE_RBAC.get(action, [])
    if profil.role not in roles_autorises:
        return False

    # Scope académie (isolation multi-tenant stricte)
    if academie and profil.role != 'admin':
        if not profil.academies.filter(id=academie.id).exists():
            return False

    # Scope objet (ex: un formateur ne modifie QUE ses formations attribuées)
    if objet is not None and profil.role == 'formateur':
        enseignant = getattr(profil, 'enseignant', None)
        if enseignant and hasattr(objet, 'id'):
            if not enseignant.formations_attribuees.filter(id=objet.id).exists():
                return False

    return True


def exiger_permission(action):
    """
    Décorateur de vue basé sur la matrice RBAC — remplace progressivement 
    role_required() pour les actions listées dans MATRICE_RBAC.
    Usage : @exiger_permission('formation.publier')
    """
    def decorateur(vue_func):
        @wraps(vue_func)
        def wrapper(request, *args, **kwargs):
            if not peut(request.user, action):
                messages.error(request, "🔒 Action non autorisée pour ton rôle.")
                return redirect('dashboard')
            return vue_func(request, *args, **kwargs)
        return wrapper
    return decorateur


# ================================================
# ANCIENS DÉCORATEURS (conservés intacts pour ne rien casser)
# ================================================

def role_required(*roles):
    """
    Décorateur qui vérifie que l'utilisateur a l'un des rôles spécifiés.
    Usage : @role_required('admin', 'super_admin')
    """

    def check_role(user):
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        try:
            return user.profil.role in roles
        except Exception:
            return False

    return user_passes_test(check_role, login_url="/connexion/")


def admin_required(view_func):
    """Accès réservé aux administrateurs et super admins."""
    return role_required("admin", "super_admin")(view_func)


def formateur_required(view_func):
    """Accès réservé aux formateurs et rôles supérieurs."""
    return role_required("formateur", "resp_academique", "admin", "super_admin")(view_func)


def finance_required(view_func):
    """Accès réservé à la finance et aux rôles supérieurs."""
    return role_required("finance", "direction", "admin", "super_admin")(view_func)


# ================================================
# FONCTION UTILITAIRE — Enregistrement des logs d'audit
# ================================================
def enregistrer_log(request, action, description, objet_type="", objet_id=None):
    """
    Enregistre une action sensible dans LogAudit.
    Usage : enregistrer_log(request, 'validation_paiement', f"Transaction {t.id} validée", 'Transaction', t.id)
    """
    from .models import LogAudit

    ip = request.META.get("HTTP_X_FORWARDED_FOR", request.META.get("REMOTE_ADDR"))
    LogAudit.objects.create(
        utilisateur=request.user if request.user.is_authenticated else None,
        action=action,
        description=description,
        objet_type=objet_type,
        objet_id=objet_id,
        adresse_ip=ip.split(",")[0] if ip else None,
    )