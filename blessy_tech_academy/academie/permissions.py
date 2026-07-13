# ================================================
# PERMISSIONS.PY — Décorateurs RBAC
# ================================================

from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied


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
    return user_passes_test(check_role, login_url='/connexion/')


def admin_required(view_func):
    """Accès réservé aux administrateurs et super admins."""
    return role_required('admin', 'super_admin')(view_func)


def formateur_required(view_func):
    """Accès réservé aux formateurs et rôles supérieurs."""
    return role_required('formateur', 'resp_academique', 'admin', 'super_admin')(view_func)


def finance_required(view_func):
    """Accès réservé à la finance et aux rôles supérieurs."""
    return role_required('finance', 'direction', 'admin', 'super_admin')(view_func)