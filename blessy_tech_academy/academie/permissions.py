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

# ================================================
# FONCTION UTILITAIRE — Enregistrement des logs d'audit
# ================================================
def enregistrer_log(request, action, description, objet_type='', objet_id=None):
    """
    Enregistre une action sensible dans LogAudit.
    Usage : enregistrer_log(request, 'validation_paiement', f"Transaction {t.id} validée", 'Transaction', t.id)
    """
    from .models import LogAudit
    ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR'))
    LogAudit.objects.create(
        utilisateur=request.user if request.user.is_authenticated else None,
        action=action, description=description,
        objet_type=objet_type, objet_id=objet_id,
        adresse_ip=ip.split(',')[0] if ip else None,
    )