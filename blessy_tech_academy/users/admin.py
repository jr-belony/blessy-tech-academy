from django.contrib import admin

# Register y# ================================================
# USERS/ADMIN.PY — Administration des modèles utilisateur
# Retire ces classes de academie/admin.py, colle-les ici telles quelles
# ================================================

from django.contrib import admin
from .models import ProfilUtilisateur, LogAudit, Enseignant, HistoriqueConversationIA, PushSubscription, NotificationPushEnvoyee


class RolePermissionMixin:
    """Copie du mixin — sera centralisé dans un package commun au Sprint E."""
    roles_autorises = ['admin']

    def _verifier_role(self, request):
        if request.user.is_superuser:
            return True
        profil = getattr(request.user, 'profil', None)
        return profil and profil.role in self.roles_autorises

    def has_module_permission(self, request):
        return self._verifier_role(request)

    def has_view_permission(self, request, obj=None):
        return self._verifier_role(request)

    def has_add_permission(self, request):
        return self._verifier_role(request)

    def has_change_permission(self, request, obj=None):
        return self._verifier_role(request)

    def has_delete_permission(self, request, obj=None):
        return self._verifier_role(request)


# ================================================
# ADMIN — ProfilUtilisateur & LogAudit
# ================================================
@admin.register(ProfilUtilisateur)
class ProfilUtilisateurAdmin(admin.ModelAdmin):
    list_display = ['utilisateur', 'role', 'telephone', 'date_creation']
    list_filter = ['role']
    list_editable = ['role']
    search_fields = ['utilisateur__username', 'utilisateur__email']


@admin.register(LogAudit)
class LogAuditAdmin(admin.ModelAdmin):
    list_display = ["action", "utilisateur", "description_courte", "adresse_ip", "date_creation"]
    list_filter = ["action"]
    readonly_fields = [
        "utilisateur",
        "action",
        "description",
        "objet_type",
        "objet_id",
        "adresse_ip",
        "date_creation",
    ]
    search_fields = ["description", "utilisateur__username"]

    def description_courte(self, obj):
        return obj.description[:80]

    description_courte.short_description = "Description"

    def has_add_permission(self, request):
        return False


# ================================================
# ADMIN — Enseignants (Admin, SuperAdmin)
# ================================================

@admin.register(Enseignant)
class EnseignantAdmin(admin.ModelAdmin):
    list_display = ['profil', 'statut', 'nb_formations', 'revenus_generes_affiche', 'nb_etudiants_formes']
    list_filter = ['statut']
    filter_horizontal = ['formations_attribuees']
    list_editable = ['statut']

    def nb_formations(self, obj):
        return obj.formations_attribuees.count()
    nb_formations.short_description = 'Formations'

    def revenus_generes_affiche(self, obj):
        return f"{obj.revenus_generes()} $"
    revenus_generes_affiche.short_description = 'Revenus générés'



# ================================================
# ADMIN.PY — Administration Historique IA
# ================================================
@admin.register(HistoriqueConversationIA)
class HistoriqueConversationIAAdmin(admin.ModelAdmin):
    list_display = ['utilisateur', 'role', 'contenu_court', 'date_creation']
    list_filter = ['role']
    search_fields = ['utilisateur__username', 'contenu']

    def contenu_court(self, obj):
        return obj.contenu[:80]
    contenu_court.short_description = 'Contenu'

    def has_add_permission(self, request):
        return False


@admin.register(PushSubscription)
class PushSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['utilisateur', 'navigateur', 'actif', 'date_creation']
    list_filter = ['actif']


@admin.register(NotificationPushEnvoyee)
class NotificationPushEnvoyeeAdmin(admin.ModelAdmin):
    list_display = ['utilisateur', 'type_notification', 'titre', 'envoyee_avec_succes', 'date_envoi']
    list_filter = ['type_notification', 'envoyee_avec_succes']
