# ================================================
# BILLING/ADMIN.PY — Administration Commerce/Paiement
# Retire ces classes de academie/admin.py, colle-les ici
# ================================================

from django.contrib import admin
from django.db.models import Sum
from .models import (
    MoyenPaiement, Coupon, Promotion, Order, OrderItem, Invoice,
    Transaction, Refund, AccesFormationDebloque, PlanAbonnement,
    Subscription, Affilie, CommissionAffiliation,
)
from users.admin import RolePermissionMixin


# ================================================
# ADMIN.PY — Payment Center (Finance, Admin, SuperAdmin)
# ================================================
@admin.register(MoyenPaiement)
class MoyenPaiementAdmin(admin.ModelAdmin):
    list_display = ["icone", "nom_affiche", "code", "actif", "ordre"]
    list_editable = ["actif", "ordre"]

    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        try:
            return request.user.profil.role in ["finance", "admin"]
        except Exception:
            return False

    # === RBAC : permissions de modification/suppression ===
    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        try:
            return request.user.profil.role in ["admin"]
        except Exception:
            return False

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        try:
            return request.user.profil.role in ["admin"]
        except Exception:
            return False



# ================================================
# ADMIN.PY — CouponAdmin (gestion des coupons)
# Rôle : Finance (consultation) et Admin (tous droits)
# ================================================
@admin.register(Coupon)
class CouponAdmin(RolePermissionMixin, admin.ModelAdmin):
    roles_autorises = ['finance', 'admin']  # pour voir le module et les objets
    list_display = [
        "code",
        "type_reduction",
        "valeur",
        "utilisations_actuelles",
        "utilisations_max",
        "actif",
    ]
    list_editable = ["actif"]
    search_fields = ["code"]

    # Seul l'admin peut modifier ou supprimer
    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        profil = getattr(request.user, 'profil', None)
        return profil and profil.role == 'admin'

    def has_delete_permission(self, request, obj=None):
        return self.has_change_permission(request, obj)



# ================================================
# ADMIN.PY — PromotionAdmin (gestion des promotions)
# Rôle : Finance (consultation) et Admin (tous droits)
# ================================================
@admin.register(Promotion)
class PromotionAdmin(RolePermissionMixin, admin.ModelAdmin):
    roles_autorises = ['finance', 'admin']
    list_display = ["nom", "pourcentage_reduction", "date_debut", "date_fin", "actif"]
    list_editable = ["actif"]
    filter_horizontal = ["ecoles_concernees", "formations_concernees"]

    # Seul l'admin peut modifier ou supprimer
    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        profil = getattr(request.user, 'profil', None)
        return profil and profil.role == 'admin'

    def has_delete_permission(self, request, obj=None):
        return self.has_change_permission(request, obj)
    


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['formation', 'nom_produit_snapshot', 'prix_unitaire']


# ================================================
# ADMIN.PY — OrderAdmin (gestion des commandes)
# Rôle : Finance et Admin uniquement
# ================================================
@admin.register(Order)
class OrderAdmin(RolePermissionMixin, admin.ModelAdmin):
    roles_autorises = ['admin', 'comptable']
    list_display = ['reference', 'utilisateur', 'total', 'statut', 'date_creation']
    list_filter = ['statut', 'devise']
    search_fields = ['reference', 'utilisateur__username']
    inlines = [OrderItemInline]
    readonly_fields = ['reference', 'sous_total', 'reduction_totale', 'total']



# ================================================
# ADMIN.PY — TransactionAdmin (validation des paiements)
# Rôle : Finance et Admin uniquement
# ================================================
@admin.register(Transaction)
class TransactionAdmin(RolePermissionMixin, admin.ModelAdmin):
    roles_autorises = ['admin', 'comptable']
    list_display = ['commande', 'moyen_paiement', 'montant', 'statut', 'date_creation', 'bouton_valider']
    list_filter = ['statut', 'moyen_paiement']

    def bouton_valider(self, obj):
        from django.utils.html import format_html
        if obj.statut == 'en_verification':
            return format_html(
                '<a href="/admin/valider-transaction/{}/" style="background:#22c55e; color:white; padding:4px 12px; border-radius:6px; text-decoration:none; font-size:11px; font-weight:700;">✅ Valider le paiement</a>',
                obj.id
            )
        return "—"
    bouton_valider.short_description = 'Action'


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ["numero_facture", "commande", "date_emission"]
    search_fields = ["numero_facture"]

    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        try:
            return request.user.profil.role in ["finance", "admin"]
        except Exception:
            return False

    # === RBAC : factures non modifiables ===
    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        try:
            return request.user.profil.role in ["admin"]
        except Exception:
            return False



# ================================================
# ADMIN.PY — RefundAdmin (gestion des remboursements)
# Rôle : Finance et Admin uniquement
# ================================================
@admin.register(Refund)
class RefundAdmin(RolePermissionMixin, admin.ModelAdmin):
    roles_autorises = ['admin', 'comptable']
    list_display = ['commande', 'montant', 'statut', 'date_demande']
    list_editable = ['statut']


@admin.register(AccesFormationDebloque)
class AccesFormationDebloqueAdmin(admin.ModelAdmin):
    list_display = ["utilisateur", "nom_formation_snapshot", "date_deblocage"]
    search_fields = ["utilisateur__username", "nom_formation_snapshot"]

    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        try:
            return request.user.profil.role in ["finance", "admin"]
        except Exception:
            return False

    # === RBAC : lecture seule ===
    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        try:
            return request.user.profil.role in ["admin"]
        except Exception:
            return False


# ================================================
# ADMIN.PY — Administration abonnements
# ================================================
@admin.register(PlanAbonnement)
class PlanAbonnementAdmin(RolePermissionMixin, admin.ModelAdmin):
    roles_autorises = ['admin', 'comptable']
    list_display = ['nom', 'prix', 'periodicite', 'actif']
    list_editable = ['actif']


@admin.register(Subscription)
class SubscriptionAdmin(RolePermissionMixin, admin.ModelAdmin):
    roles_autorises = ['admin', 'comptable']
    list_display = ['utilisateur', 'plan_nom_snapshot', 'statut', 'date_prochain_renouvellement']
    list_filter = ['statut']


@admin.register(Affilie)
class AffilieAdmin(RolePermissionMixin, admin.ModelAdmin):
    roles_autorises = ['admin', 'comptable', 'marketing']
    list_display = ['utilisateur', 'code_affiliation', 'taux_commission', 'commission_totale_affichee', 'actif']
    list_editable = ['actif']

    def commission_totale_affichee(self, obj):
        return f"{obj.commission_totale()} $"
    commission_totale_affichee.short_description = 'Commissions'


@admin.register(CommissionAffiliation)
class CommissionAffiliationAdmin(RolePermissionMixin, admin.ModelAdmin):
    roles_autorises = ['admin', 'comptable']
    list_display = ['affilie', 'commande', 'montant', 'statut', 'date_creation']
    list_editable = ['statut']