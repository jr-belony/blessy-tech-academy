from datetime import timedelta

from adminsortable2.admin import SortableAdminBase, SortableInlineAdminMixin
from django.contrib import admin, messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Avg, Count, Q, Sum
from django.shortcuts import get_object_or_404, render
from django.urls import path
from django.utils import timezone
from simple_history.admin import SimpleHistoryAdmin

from . import views
from .models import (
    LogRequetePartenaire,
    Academie,
    Affilie,
    Article,
    Inscription,
    InteractionCRM,
    Order,
    OutilRecommande,
    PartenaireAPI,
    Reaction,
    Reponse, 
    Sujet,
    Temoignage,
    Transaction,
    # Modèles pédagogiques
    Competence,
    CompetenceValidee,
    LearningOutcome,
    Ecole,
    Formation,
    Module,
    Lecon,
    Parcours,
    Quiz,
    Question,
    ResultatQuiz,
    Examen,
    QuestionExamen,
    ChoixExamen,
    TentativeExamen,
    WorkflowFormation,
    Cohorte,
    ProjetEtudiant,
    Certificat,
    EligibiliteCertification,
    Partenaire,
)

from users.admin import RolePermissionMixin
from users.models import Enseignant
from content.models import WorkflowArticle 
from django.http import HttpResponse


# ================================================
# Thème CSS global pour tout l'admin
# ================================================
class AdminThemeMixin:
    class Media:
        css = {"all": ["academie/admin/theme_premium.css"]}


# ================================================
# ADMIN — Écoles
# ================================================
@admin.register(Ecole)
class EcoleAdmin(AdminThemeMixin, admin.ModelAdmin):
    list_display = ["icone", "nom", "academie", "ordre"]
    list_editable = ["ordre"]
    list_filter = ["academie"]
    search_fields = ["nom"]
    class Media:
        js = ['academie/admin/generer_ecole.js']
    
    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        try:
            return request.user.profil.role in ["formateur", "resp_academique", "admin"]
        except Exception:
            return False


class LeconInline(SortableInlineAdminMixin, admin.TabularInline):
    model = Lecon
    extra = 3
    fields = ["ordre", "titre", "resume", "duree_minutes"]


class ReponseInline(admin.TabularInline):
    model = Reponse
    extra = 0
    fields = ["auteur", "contenu", "acceptee", "date_creation"]
    readonly_fields = ["date_creation"]


class ModuleInline(SortableInlineAdminMixin, admin.TabularInline):
    model = Module
    extra = 1
    fields = ["ordre", "titre", "description"]
    show_change_link = True


class LearningOutcomeInline(admin.TabularInline):
    model = LearningOutcome
    extra = 2


# ================================================
# ADMIN — Formation
# ================================================
@admin.register(Formation)
class FormationAdmin(RolePermissionMixin, AdminThemeMixin, SortableAdminBase, SimpleHistoryAdmin):
    roles_autorises = ['formateur', 'resp_academique', 'admin']

    list_display = [
        "icone", "nom", "ecole", "niveau", "duree_formatee",
        "prix", "actif", "gratuit", "delivre_certificat",
        "bouton_workspace", "bouton_workspace_liste"
    ]
    list_filter = ["actif", "niveau", "ecole", "gratuit", "delivre_certificat", "badge_associe"]
    search_fields = ["nom", "description", "badge_associe"]
    autocomplete_fields = ["formation_upgrade"]
    list_editable = ["actif", "gratuit", "prix"]
    inlines = [ModuleInline, LearningOutcomeInline]

    # Fieldsets FormationAdmin optimisés pour rédaction rapide
    fieldsets = [
        ('📌 Identité', {
            'fields': ['ecole', 'nom', 'slug', 'icone', 'niveau', 'gratuit', 'actif'],
            'description': "Le slug se génère automatiquement — laisse-le vide."
        }),
        ('📝 Présentation (page de vente)', {
            'fields': ['description', 'public_cible', 'debouches', 'prerequis'],
        }),
        ('📐 Pédagogie', {
            'fields': ['methode_pedagogique', 'criteres_evaluation', 'certifications'],
            'description': "Remplis ces champs pour que les nouvelles sections de la page de vente s'affichent."
        }),
        ('💰 Commercial', {
            'fields': ['duree', 'duree_unite', 'prix', 'formation_upgrade'],
        }),
        ('🏆 Compétences & Badge', {
            'fields': ['competences_acquises', 'badge_associe'],
            'classes': ['collapse'],
        }),
        ('📊 Salaires indicatifs', {
            'fields': ['salaire_haiti', 'salaire_international'],
            'classes': ['collapse'],
        }),
        ('⚙️ Options avancées', {
            'fields': ['sequentiel_obligatoire', 'delivre_certificat'],
            'classes': ['collapse'],
            'description': "Active si les leçons doivent être suivies dans l'ordre strict."
        }),
    ]

    actions = [
        "partager_sur_reseaux",
        "rendre_gratuit",
        "rendre_payant",
        "activer_formations",
        "desactiver_formations",
    ]

    def duree_formatee(self, obj):
        return f"{obj.duree} {obj.get_duree_unite_display()}"
    duree_formatee.short_description = "Durée"
    duree_formatee.admin_order_field = "duree"

    @admin.action(description="📢 Partager les formations sélectionnées sur les réseaux sociaux (simulation)")
    def partager_sur_reseaux(self, request, queryset):
        from .social import partager_formation
        n = 0
        for formation in queryset:
            partager_formation(formation)
            n += 1
        self.message_user(request, f"✅ {n} formation(s) partagée(s) (simulation).")

    @admin.action(description="🎁 Rendre gratuit")
    def rendre_gratuit(self, request, queryset):
        count = queryset.update(gratuit=True)
        self.message_user(request, f"✅ {count} formation(s) marquée(s) comme gratuites.")

    @admin.action(description="💰 Rendre payant")
    def rendre_payant(self, request, queryset):
        count = queryset.update(gratuit=False)
        self.message_user(request, f"✅ {count} formation(s) marquée(s) comme payantes.")

    @admin.action(description="✅ Activer")
    def activer_formations(self, request, queryset):
        count = queryset.update(actif=True)
        self.message_user(request, f"✅ {count} formation(s) activée(s).")

    @admin.action(description="⛔ Désactiver")
    def desactiver_formations(self, request, queryset):
        count = queryset.update(actif=False)
        self.message_user(request, f"✅ {count} formation(s) désactivée(s).")

    def bouton_workspace(self, obj):
        from django.utils.html import format_html
        url = f"/admin/formation/{obj.id}/workspace/"
        return format_html(
            '<a href="{}" style="background:#00B4D8; color:white; padding:4px 12px; border-radius:6px; text-decoration:none; font-size:11px; font-weight:700;">🗂️ Ouvrir le Workspace</a>',
            url,
        )
    bouton_workspace.short_description = "Workspace"

    def bouton_workspace_liste(self, obj):
        from django.utils.html import format_html
        return format_html(
            '<a href="/admin/formation/{}/workspace/" style="background:#003B8E; color:white; padding:4px 12px; border-radius:6px; text-decoration:none; font-size:11px; font-weight:700;">✏️ Rédiger</a>',
            obj.id
        )
    bouton_workspace_liste.short_description = 'Rédaction'

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        profil = getattr(request.user, 'profil', None)
        return profil and profil.role in ['resp_academique', 'admin']

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        profil = getattr(request.user, 'profil', None)
        return profil and profil.role == 'admin'

    class Media:
        js = ["academie/admin/generer_ia.js", "academie/admin/generer_programme.js"]



# ================================================
# ADMIN — Inscriptions CRM
# ================================================
class InteractionCRMInline(admin.TabularInline):
    model = InteractionCRM
    extra = 0
    readonly_fields = ["auteur", "date_creation"]


@admin.register(Inscription)
class InscriptionAdmin(AdminThemeMixin, admin.ModelAdmin):
    list_display = [
        "prenom", "nom", "email", "formation", "sujet", "statut_lead",
        "assigne_a", "date_inscription", "traite"
    ]
    list_filter = ["traite", "formation", "sujet", "statut_lead", "source_lead"]
    search_fields = ["prenom", "nom", "email"]
    list_editable = ["traite", "statut_lead"]
    readonly_fields = ["date_inscription"]
    inlines = [InteractionCRMInline]

    actions = ["marquer_traite", "marquer_non_traite", "assigner_a_support"]

    @admin.action(description="✅ Marquer comme traité")
    def marquer_traite(self, request, queryset):
        count = queryset.update(traite=True)
        self.message_user(request, f"✅ {count} inscription(s) marquée(s) comme traitées.")

    @admin.action(description="🔄 Marquer comme non traité")
    def marquer_non_traite(self, request, queryset):
        count = queryset.update(traite=False)
        self.message_user(request, f"🔄 {count} inscription(s) marquée(s) comme non traitées.")

    @admin.action(description="📌 Assigner à l'équipe support")
    def assigner_a_support(self, request, queryset):
        count = queryset.update(assigne_a=request.user)
        self.message_user(request, f"📌 {count} inscription(s) assignée(s) à {request.user.username}.")

    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        try:
            return request.user.profil.role in ["support", "marketing", "admin"]
        except Exception:
            return False


# ================================================
# ADMIN — Quiz
# ================================================
class QuestionInline(admin.TabularInline):
    model = Question
    extra = 5
    fields = ["ordre", "texte", "choix_a", "choix_b", "choix_c", "choix_d", "bonne_reponse"]


@admin.register(Quiz)
class QuizAdmin(RolePermissionMixin, AdminThemeMixin, admin.ModelAdmin):
    roles_autorises = ['formateur', 'examinateur', 'resp_academique', 'admin']
    list_display = [
        "titre", "formation", "module", "nombre_questions",
        "limite_temps_minutes", "actif", "date_creation"
    ]
    list_filter = ["actif", "formation", "module"]
    search_fields = ["titre"]
    list_editable = ["actif", "limite_temps_minutes"]
    inlines = [QuestionInline]
    
    # --- NOUVEAU ---
    filter_horizontal = ['competences_liees']

    actions = ["activer_quiz", "desactiver_quiz"]

    @admin.action(description="✅ Activer les quiz sélectionnés")
    def activer_quiz(self, request, queryset):
        count = queryset.update(actif=True)
        self.message_user(request, f"✅ {count} quiz activé(s).")

    @admin.action(description="⛔ Désactiver les quiz sélectionnés")
    def desactiver_quiz(self, request, queryset):
        count = queryset.update(actif=False)
        self.message_user(request, f"⛔ {count} quiz désactivé(s).")

    class Media:
        js = ["academie/admin/generer_quiz.js"]



# ================================================
# ADMIN — Résultats Quiz
# ================================================
@admin.register(ResultatQuiz)
class ResultatQuizAdmin(AdminThemeMixin, admin.ModelAdmin):
    list_display = ["utilisateur", "quiz", "score", "total_questions", "pourcentage", "date_passage"]
    list_filter = ["quiz"]
    search_fields = ["utilisateur__username"]
    readonly_fields = ["date_passage"]

    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        try:
            return request.user.profil.role in ["examinateur", "correcteur", "resp_academique", "admin"]
        except Exception:
            return False


# ================================================
# ADMIN — Module
# ================================================
@admin.register(Module)
class ModuleAdmin(RolePermissionMixin, AdminThemeMixin, SortableAdminBase, admin.ModelAdmin):
    roles_autorises = ['formateur', 'resp_academique', 'admin']
    list_display = ["titre", "get_ecole", "formation", "ordre", "nombre_lecons"]
    list_filter = ["formation__ecole", "formation"]
    search_fields = ["titre", "formation__nom"]
    ordering = ["formation__ecole", "formation", "ordre"]
    inlines = [LeconInline]

    def get_ecole(self, obj):
        return obj.formation.ecole if obj.formation.ecole else "—"
    get_ecole.short_description = "École"
    get_ecole.admin_order_field = "formation__ecole"

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        profil = getattr(request.user, 'profil', None)
        return profil and profil.role in ['resp_academique', 'admin']

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        profil = getattr(request.user, 'profil', None)
        return profil and profil.role == 'admin'

    class Media:
        js = ["academie/admin/generer_programme.js", "academie/admin/generer_contenu_module.js"]


# ================================================
# ADMIN — Lecon
# ================================================
@admin.register(Lecon)
class LeconAdmin(RolePermissionMixin, AdminThemeMixin, SimpleHistoryAdmin):
    roles_autorises = ['formateur', 'resp_academique', 'admin']
    list_display = ["titre", "get_ecole", "get_formation", "module", "duree_minutes", "ordre"]
    list_filter = ["module__formation__ecole", "module__formation"]
    search_fields = ["titre", "contenu", "module__formation__nom"]
    ordering = ["module__formation__ecole", "module__formation", "module__ordre", "ordre"]

    def get_ecole(self, obj):
        return obj.module.formation.ecole if obj.module.formation.ecole else "—"
    get_ecole.short_description = "École"
    get_ecole.admin_order_field = "module__formation__ecole"

    def get_formation(self, obj):
        return obj.module.formation
    get_formation.short_description = "Formation"
    get_formation.admin_order_field = "module__formation"

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        profil = getattr(request.user, 'profil', None)
        return profil and profil.role in ['resp_academique', 'admin']

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        profil = getattr(request.user, 'profil', None)
        return profil and profil.role == 'admin'

    class Media:
        js = ["academie/admin/generer_contenu_lecon.js"]


# ================================================
# ADMIN — Parcours
# ================================================
@admin.register(Parcours)
class ParcoursAdmin(AdminThemeMixin, admin.ModelAdmin):
    list_display = ["icone", "titre", "duree_formatee", "prix", "nombre_formations", "actif", "ordre"]
    list_filter = ["actif", "duree_unite"]
    search_fields = ["titre", "description"]
    list_editable = ["actif", "ordre"]
    filter_horizontal = ["formations"]
    prepopulated_fields = {"slug": ("titre",)}  # ← AJOUTÉ

    fieldsets = [
        ("Informations principales", {"fields": ["icone", "titre", "slug", "description", "duree", "duree_unite", "prix", "actif", "ordre"]}),
        ("Carrière & Métiers", {"fields": ["metiers_vises", "projets_inclus", "certifications_incluses"], "classes": ["collapse"]}),
        ("Formations incluses", {"fields": ["formations"], "description": "Sélectionne les formations qui composent ce parcours."}),
    ]

    def duree_formatee(self, obj):
        return f"{obj.duree} {obj.get_duree_unite_display()}"
    duree_formatee.short_description = "Durée"
    duree_formatee.admin_order_field = "duree"

    def nombre_formations(self, obj):
        return obj.formations.count()
    nombre_formations.short_description = "Formations"

    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        try:
            return request.user.profil.role in ["resp_academique", "admin"]
        except Exception:
            return False

    class Media:
        js = ["academie/admin/generer_parcours.js"]


# ================================================
# ADMIN — Sujet (Forum)
# ================================================
@admin.register(Sujet)
class SujetAdmin(RolePermissionMixin, AdminThemeMixin, admin.ModelAdmin):
    roles_autorises = ['support', 'admin']
    list_display = ["titre", "auteur", "formation", "categorie", "nombre_reponses", "vues", "epingle", "resolu", "date_creation"]
    list_filter = ["categorie", "resolu", "epingle", "formation"]
    search_fields = ["titre", "contenu", "auteur__username"]
    list_editable = ["epingle", "resolu"]
    readonly_fields = ["date_creation", "date_modification", "vues"]
    inlines = [ReponseInline]

    actions = ["marquer_resolu", "marquer_non_resolu", "epingler", "desepingler"]

    @admin.action(description="✅ Marquer comme résolu")
    def marquer_resolu(self, request, queryset):
        count = queryset.update(resolu=True)
        self.message_user(request, f"✅ {count} sujet(s) marqué(s) résolu(s).")

    @admin.action(description="🔄 Marquer comme non résolu")
    def marquer_non_resolu(self, request, queryset):
        count = queryset.update(resolu=False)
        self.message_user(request, f"🔄 {count} sujet(s) marqué(s) non résolu(s).")

    @admin.action(description="📌 Épingler")
    def epingler(self, request, queryset):
        count = queryset.update(epingle=True)
        self.message_user(request, f"📌 {count} sujet(s) épinglé(s).")

    @admin.action(description="📌 Désépingler")
    def desepingler(self, request, queryset):
        count = queryset.update(epingle=False)
        self.message_user(request, f"📌 {count} sujet(s) désépinglé(s).")


# ================================================
# ADMIN — Reponse (Forum)
# ================================================
@admin.register(Reponse)
class ReponseAdmin(RolePermissionMixin, AdminThemeMixin, admin.ModelAdmin):
    roles_autorises = ['support', 'admin']
    list_display = ["auteur", "sujet", "acceptee", "date_creation"]
    list_filter = ["acceptee"]
    search_fields = ["contenu", "auteur__username"]
    readonly_fields = ["date_creation"]

    actions = ["accepter_reponses", "refuser_reponses"]

    @admin.action(description="✅ Accepter les réponses sélectionnées")
    def accepter_reponses(self, request, queryset):
        count = queryset.update(acceptee=True)
        self.message_user(request, f"✅ {count} réponse(s) acceptée(s).")

    @admin.action(description="❌ Refuser les réponses sélectionnées")
    def refuser_reponses(self, request, queryset):
        count = queryset.update(acceptee=False)
        self.message_user(request, f"❌ {count} réponse(s) refusée(s).")


# ================================================
# ADMIN — Réactions
# ================================================
@admin.register(Reaction)
class ReactionAdmin(AdminThemeMixin, admin.ModelAdmin):
    list_display = ["utilisateur", "sujet", "reponse", "date_creation"]
    readonly_fields = ["date_creation"]

    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        try:
            return request.user.profil.role in ["support", "admin"]
        except Exception:
            return False


# ================================================
# ADMIN — Article (Blog)
# ================================================
@admin.register(Article)
class ArticleAdmin(AdminThemeMixin, SimpleHistoryAdmin):
    list_display = [
        "titre", "categorie", "auteur", "en_vedette", "statut_editorial",
        "temps_lecture", "date_publication", "bouton_apercu"
    ]
    list_filter = ["categorie", "statut_editorial", "en_vedette", "formation_liee", "academie"]
    search_fields = ["titre", "resume", "contenu", "mots_cles"]
    list_editable = ["en_vedette", "statut_editorial"]
    prepopulated_fields = {"slug": ("titre",)}
    readonly_fields = ["date_publication", "date_modification", "apercu_seo", "apercu_responsive"]

    # Fieldsets ArticleAdmin optimisés pour rédaction rapide
    fieldsets = [
        ('📌 Identité', {
            'fields': ['titre', 'slug', 'categorie', 'type_contenu', 'academie'],
            'description': "Le slug se génère automatiquement — laisse-le vide."
        }),
        ('📝 Contenu', {
            'fields': ['resume', 'contenu', 'temps_lecture'],
        }),
        ('🔗 Liens', {
            'fields': ['formation_liee', 'articles_associes', 'fichier_telechargeable'],
            'classes': ['collapse'],
        }),
        ('🔍 SEO', {
            'fields': ['meta_titre', 'meta_description', 'mots_cles', 'noindex', 'apercu_seo'],
            'classes': ['collapse'],
        }),
        ('👁️ Prévisualisation', {'fields': ['apercu_responsive']}),
        ('🚀 Publication', {
            'fields': ['statut_editorial', 'relu_par', 'en_vedette', 'auteur'],
        }),
    ]
    # Auto-remplissage auteur (gain de temps)
    def get_changeform_initial_data(self, request):
        return {'auteur': request.user.id}

    actions = ["publier_articles", "depublier_articles", "mettre_en_vedette", "retirer_vedette"]

    @admin.action(description="✅ Publier les articles sélectionnés")
    def publier_articles(self, request, queryset):
        count = queryset.update(statut_editorial='publie')
        self.message_user(request, f"✅ {count} article(s) publié(s).")

    @admin.action(description="⛔ Dépublier les articles sélectionnés")
    def depublier_articles(self, request, queryset):
        count = queryset.update(statut_editorial='brouillon')
        self.message_user(request, f"⛔ {count} article(s) dépublié(s).")

    @admin.action(description="⭐ Mettre en vedette")
    def mettre_en_vedette(self, request, queryset):
        count = queryset.update(en_vedette=True)
        self.message_user(request, f"⭐ {count} article(s) mis en vedette.")

    @admin.action(description="⭐ Retirer de la vedette")
    def retirer_vedette(self, request, queryset):
        count = queryset.update(en_vedette=False)
        self.message_user(request, f"⭐ {count} article(s) retiré(s) de la vedette.")

    def bouton_apercu(self, obj):
        from django.utils.html import format_html
        if obj.id:
            return format_html(
                '<a href="/admin/apercu-article/{}/" target="_blank" style="background:var(--bta-cyan); color:white; padding:4px 12px; border-radius:6px; text-decoration:none; font-size:11px; font-weight:700;">👁️ Aperçu</a>',
                obj.id,
            )
        return "—"
    bouton_apercu.short_description = "Aperçu"

    def apercu_seo(self, obj):
        from django.utils.html import format_html
        titre = obj.meta_titre or obj.titre
        desc = obj.meta_description or obj.resume[:160]
        return format_html(
            '<div style="border:1px solid #e2e8f0; border-radius:8px; padding:12px; max-width:500px;">'
            '<div style="color:#1a0dab; font-size:16px;">{}</div>'
            '<div style="color:#006621; font-size:12px;">blessytechacademy.com/ressources/{}</div>'
            '<div style="color:#4d5156; font-size:13px;">{}</div></div>',
            titre, obj.slug, desc,
        )
    apercu_seo.short_description = "Aperçu Google"

    def apercu_responsive(self, obj):
        from django.utils.html import format_html
        if not obj.id:
            return "Enregistre d'abord l'article pour voir l'aperçu."
        url = f"/admin/apercu-article/{obj.id}/"
        return format_html(
            """
            <div style="display:flex; gap:8px; margin-bottom:12px;">
                <button type="button" onclick="document.getElementById('apercu-frame').style.width='100%'; document.getElementById('apercu-frame').style.height='500px';" style="padding:6px 14px; border-radius:6px; border:1px solid #e2e8f0; cursor:pointer; background:white;">🖥️ Desktop</button>
                <button type="button" onclick="document.getElementById('apercu-frame').style.width='768px'; document.getElementById('apercu-frame').style.height='500px';" style="padding:6px 14px; border-radius:6px; border:1px solid #e2e8f0; cursor:pointer; background:white;">📱 Tablette</button>
                <button type="button" onclick="document.getElementById('apercu-frame').style.width='375px'; document.getElementById('apercu-frame').style.height='600px';" style="padding:6px 14px; border-radius:6px; border:1px solid #e2e8f0; cursor:pointer; background:white;">📱 Mobile</button>
                <a href="{}" target="_blank" style="padding:6px 14px; border-radius:6px; background:var(--bta-orange); color:white; text-decoration:none; font-size:13px;">Ouvrir en plein écran ↗</a>
            </div>
            <div style="border:1px solid #e2e8f0; border-radius:8px; padding:16px; background:#f8fafc; overflow-x:auto;">
                <iframe id="apercu-frame" src="{}" style="width:100%; height:500px; border:1px solid #ccc; border-radius:8px; background:white; transition:all 0.3s;"></iframe>
            </div>
            """,
            url, url,
        )
    apercu_responsive.short_description = "Prévisualisation"

    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        try:
            return request.user.profil.role in ["marketing", "resp_academique", "admin"]
        except Exception:
            return False


# ================================================
# ADMIN — OutilRecommande
# ================================================
@admin.register(OutilRecommande)
class OutilRecommandeAdmin(AdminThemeMixin, admin.ModelAdmin):
    list_display = ["icone", "nom", "categorie", "gratuit", "recommande_par_bta", "ordre"]
    list_filter = ["categorie", "gratuit", "recommande_par_bta"]
    search_fields = ["nom", "description"]
    list_editable = ["ordre", "recommande_par_bta"]

    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        try:
            return request.user.profil.role in ["marketing", "resp_academique", "admin"]
        except Exception:
            return False


# ================================================
# ADMIN — Temoignage
# ================================================
@admin.register(Temoignage)
class TemoignageAdmin(AdminThemeMixin, admin.ModelAdmin):
    list_display = ["prenom_nom", "formation_suivie", "note", "en_vedette", "approuve", "date_creation"]
    list_filter = ["note", "en_vedette", "approuve", "formation_suivie"]
    search_fields = ["prenom_nom", "texte"]
    list_editable = ["en_vedette", "approuve"]

    actions = ["approuver_temoignages", "desapprouver_temoignages"]

    @admin.action(description="✅ Approuver les témoignages sélectionnés")
    def approuver_temoignages(self, request, queryset):
        count = queryset.update(approuve=True)
        self.message_user(request, f"✅ {count} témoignage(s) approuvé(s).")

    @admin.action(description="⛔ Désapprouver les témoignages sélectionnés")
    def desapprouver_temoignages(self, request, queryset):
        count = queryset.update(approuve=False)
        self.message_user(request, f"⛔ {count} témoignage(s) désapprouvé(s).")

    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        try:
            return request.user.profil.role in ["marketing", "admin"]
        except Exception:
            return False


# ================================================
# ADMIN — Examen
# ================================================
class ChoixExamenInline(admin.TabularInline):
    model = ChoixExamen
    extra = 2


class QuestionExamenInline(admin.TabularInline):
    model = QuestionExamen
    extra = 0
    show_change_link = True


@admin.register(Examen)
class ExamenAdmin(admin.ModelAdmin):
    list_display = ["titre", "formation", "duree_minutes", "seuil_reussite", "actif"]
    list_filter = ["formation__ecole__academie", "formation", "actif"]
    search_fields = ["titre"]
    inlines = [QuestionExamenInline]
    filter_horizontal = ['competences_liees']
    list_editable = ["duree_minutes", "seuil_reussite", "actif"]

    actions = ["activer_examens", "desactiver_examens"]

    @admin.action(description="✅ Activer les examens sélectionnés")
    def activer_examens(self, request, queryset):
        count = queryset.update(actif=True)
        self.message_user(request, f"✅ {count} examen(s) activé(s).")

    @admin.action(description="⛔ Désactiver les examens sélectionnés")
    def desactiver_examens(self, request, queryset):
        count = queryset.update(actif=False)
        self.message_user(request, f"⛔ {count} examen(s) désactivé(s).")

    class Media:
        js = ["academie/admin/generer_examen.js"]

    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        try:
            return request.user.profil.role in ["examinateur", "resp_academique", "admin"]
        except Exception:
            return False


# ================================================
# ADMIN — Questions Examen
# ================================================
@admin.register(QuestionExamen)
class QuestionExamenAdmin(admin.ModelAdmin):
    list_display = ["texte_court", "examen", "type_question", "points"]
    inlines = [ChoixExamenInline]

    def texte_court(self, obj):
        return obj.texte[:80]

    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        try:
            return request.user.profil.role in ["examinateur", "resp_academique", "admin"]
        except Exception:
            return False


# ================================================
# ADMIN — Tentatives Examen
# ================================================
@admin.register(TentativeExamen)
class TentativeExamenAdmin(admin.ModelAdmin):
    list_display = ["utilisateur", "examen", "score", "reussi"]
    list_filter = ["reussi", "examen"]
    search_fields = ["utilisateur__username", "utilisateur__first_name", "utilisateur__last_name", "examen__titre"]
    readonly_fields = []

    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        try:
            return request.user.profil.role in ["examinateur", "correcteur", "resp_academique", "admin"]
        except Exception:
            return False


# ================================================
# ADMIN — Workflow
# ================================================
@admin.register(WorkflowFormation)
class WorkflowFormationAdmin(admin.ModelAdmin):
    list_display = ["formation", "etat_actuel", "score_checklist_affiche", "demande_par", "valide_par", "date_derniere_transition"]
    list_filter = ["etat_actuel"]
    readonly_fields = ["date_creation", "date_derniere_transition"]
    actions = ["action_envoyer_en_revision", "action_valider", "action_publier"]

    def score_checklist_affiche(self, obj):
        return f"{obj.score_checklist()}%"
    score_checklist_affiche.short_description = "Checklist"

    @admin.action(description="🔍 Envoyer en révision")
    def action_envoyer_en_revision(self, request, queryset):
        reussis = 0
        for wf in queryset:
            succes, _ = wf.transitionner('en_revision', request.user)
            if succes:
                reussis += 1
        self.message_user(request, f"✅ {reussis}/{queryset.count()} formation(s) envoyée(s) en révision")

    @admin.action(description="✅ Valider")
    def action_valider(self, request, queryset):
        reussis = 0
        for wf in queryset:
            succes, _ = wf.transitionner('validee', request.user)
            if succes:
                reussis += 1
        self.message_user(request, f"✅ {reussis}/{queryset.count()} formation(s) validée(s)")

    @admin.action(description="🌐 Publier")
    def action_publier(self, request, queryset):
        reussis, echecs = 0, 0
        for wf in queryset:
            succes, message = wf.transitionner('publiee', request.user)
            if succes:
                reussis += 1
            else:
                echecs += 1
        self.message_user(request, f"✅ {reussis} publiée(s), ⚠️ {echecs} bloquée(s) (checklist incomplète)")

    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        try:
            return request.user.profil.role in ["admin"]
        except Exception:
            return False


@admin.register(WorkflowArticle)
class WorkflowArticleAdmin(admin.ModelAdmin):
    list_display = ['article', 'etat_actuel', 'score_checklist_affiche', 'demande_par', 'valide_par', 'date_derniere_transition']
    list_filter = ['etat_actuel']
    readonly_fields = ['date_creation', 'date_derniere_transition']
    actions = ['action_publier_articles']

    def score_checklist_affiche(self, obj):
        return f"{obj.score_checklist()}%"
    score_checklist_affiche.short_description = "Checklist"

    @admin.action(description="🌐 Publier les articles sélectionnés")
    def action_publier_articles(self, request, queryset):
        reussis = 0
        for wf in queryset:
            wf.etat_actuel = 'publie'
            wf.valide_par = request.user
            wf.save()
            wf.article.statut_editorial = 'publie'
            wf.article.save()
            reussis += 1
        self.message_user(request, f"✅ {reussis} article(s) publié(s)")

    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        try:
            return request.user.profil.role in ["admin", "marketing"]
        except Exception:
            return False


# ================================================
# ADMIN — Académies
# ================================================
@admin.register(Academie)
class AcademieAdmin(admin.ModelAdmin):
    list_display = ["icone", "nom", "nb_ecoles", "nb_formations", "nb_etudiants", "actif", "est_academie_par_defaut", "bouton_stats"]
    list_editable = ["actif", "est_academie_par_defaut"]
    prepopulated_fields = {"slug": ("nom",)}
    fieldsets = [
        ("Identité", {"fields": ["nom", "slug", "sous_titre", "icone", "logo"]}),
        ("Charte graphique", {"fields": ["couleur_principale", "couleur_accent"]}),
        ("Configuration", {"fields": ["domaine_personnalise", "actif", "est_academie_par_defaut"]}),
    ]

    def bouton_stats(self, obj):
        from django.utils.html import format_html
        return format_html(
            '<a href="/admin/statistiques-academie/{}/" style="background:#00B4D8; color:white; padding:4px 12px; border-radius:6px; text-decoration:none; font-size:11px; font-weight:700;">📊 Statistiques</a>',
            obj.id,
        )
    bouton_stats.short_description = "Stats"

    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        try:
            return request.user.profil.role in ["direction", "admin"]
        except Exception:
            return False


# ================================================
# ADMIN — Partenaires API
# ================================================
from django.shortcuts import redirect
from django.utils.html import format_html

@admin.register(PartenaireAPI)
class PartenaireAPIAdmin(admin.ModelAdmin):
    list_display = [
        "nom", "email_contact", "type_partenaire", "academie_associee",
        "scopes", "limite_requetes_heure", "date_expiration", "actif", "bouton_rotation"
    ]
    list_filter = ["type_partenaire", "academie_associee", "actif"]
    search_fields = ["nom", "email_contact"]
    list_editable = ["actif", "limite_requetes_heure"]
    fields = [
        "nom", "email_contact", "cle_api", "type_partenaire", "academie_associee",
        "scopes", "limite_requetes_heure", "date_expiration", "actif", "bouton_rotation"
    ]
    readonly_fields = ["cle_api", "bouton_rotation"]

    def bouton_rotation(self, obj):
        if obj.pk:
            return format_html(
                '<a href="/admin/partenaire/{}/rotation-cle/" style="background:#ef4444; color:white; padding:4px 12px; border-radius:6px; text-decoration:none; font-size:11px; font-weight:700;" onclick="return confirm(\'⚠️ L\\\'ancienne clé sera immédiatement invalidée. Continuer ?\');">🔄 Rotation clé</a>',
                obj.pk
            )
        return "—"
    bouton_rotation.short_description = "Sécurité"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:partenaire_id>/rotation-cle/',
                self.admin_site.admin_view(self.rotation_cle_view),
                name='partenaire_rotation_cle',
            ),
        ]
        return custom_urls + urls

    def rotation_cle_view(self, request, partenaire_id):
        """Vue admin pour la rotation de clé API."""
        if not request.user.is_superuser:
            messages.error(request, "Seul un superadmin peut effectuer cette action.")
            return redirect('admin:academie_partenaireapi_changelist')

        partenaire = PartenaireAPI.objects.get(id=partenaire_id)
        partenaire.faire_tourner_la_cle()
        messages.success(
            request,
            f"✅ Clé API de « {partenaire.nom} » régénérée avec succès. Nouvelle clé : {partenaire.cle_api}"
        )
        return redirect('admin:academie_partenaireapi_change', partenaire_id)

    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        try:
            return request.user.profil.role in ["direction", "admin"]
        except Exception:
            return False


# ================================================
# ADMIN — Compétences
# ================================================
@admin.register(Competence)
class CompetenceAdmin(RolePermissionMixin, admin.ModelAdmin):
    roles_autorises = ['admin', 'formateur']
    list_display = ['icone', 'nom', 'categorie', 'nb_formations', 'nb_etudiants_maitrisant']
    list_filter = ['categorie']
    filter_horizontal = ['formations', 'modules', 'lecons']
    search_fields = ['nom']


@admin.register(LearningOutcome)
class LearningOutcomeAdmin(RolePermissionMixin, admin.ModelAdmin):
    roles_autorises = ['admin', 'formateur']
    list_display = ['formation', 'description', 'competence_associee', 'ordre']
    list_filter = ['formation']


@admin.register(CompetenceValidee)
class CompetenceValideeAdmin(admin.ModelAdmin):
    list_display = ['utilisateur', 'competence', 'niveau', 'source_type', 'score_obtenu', 'date_validation']
    list_filter = ['niveau', 'source_type', 'competence__categorie']
    search_fields = ['utilisateur__username', 'competence__nom']
    readonly_fields = ['date_validation']


# ================================================
# ADMIN — Cohorte
# ================================================
@admin.register(Cohorte)
class CohorteAdmin(admin.ModelAdmin):
    list_display = ['nom', 'nb_inscrits_affiche', 'progression_moyenne_affiche', 'nb_certificats_delivres', 'actif']
    filter_horizontal = ['formations', 'membres']
    list_editable = ['actif']

    def nb_inscrits_affiche(self, obj):
        return obj.nb_inscrits()
    nb_inscrits_affiche.short_description = 'Inscrits'

    def progression_moyenne_affiche(self, obj):
        return f"{obj.progression_moyenne()}%"
    progression_moyenne_affiche.short_description = 'Progression moy.'


# ================================================
# ADMIN — Partenaire (vitrine)
# ================================================

@admin.register(Partenaire)
class PartenaireAdmin(admin.ModelAdmin):
    list_display = ['nom', 'type_partenaire', 'actif', 'ordre']
    list_editable = ['actif', 'ordre']


# ================================================
# ADMIN — Ambassadeur
# ================================================
from .models import Ambassadeur

@admin.register(Ambassadeur)
class AmbassadeurAdmin(admin.ModelAdmin):
    list_display = ['utilisateur', 'niveau', 'visible_publiquement', 'date_nomination']
    list_editable = ['visible_publiquement']


# ================================================
# ADMIN — Outil + EtudeDeCas
# ================================================
from .models import Outil, EtudeDeCas

@admin.register(Outil)
class OutilAdmin(admin.ModelAdmin):
    list_display = ['icone', 'nom', 'site_officiel']
    filter_horizontal = ['formations']
    search_fields = ['nom']

@admin.register(EtudeDeCas)
class EtudeDeCasAdmin(admin.ModelAdmin):
    list_display = ['titre', 'formation', 'module_lie', 'ordre']
    list_filter = ['formation']


# ================================================
# VUES PERSONNALISÉES — GestionCoursAdminSite
# ================================================
class GestionCoursAdminSite(AdminThemeMixin):
    def get_urls(self, original_urls):
        custom_urls = [
            path("gestion-cours/", admin.site.admin_view(self.vue_gestion_cours), name="gestion_cours"),
            path("dashboard-editorial/", admin.site.admin_view(self.vue_dashboard_editorial), name="dashboard_editorial"),
            path("dashboard-business/", views.vue_dashboard_business, name="dashboard_business"),
            path("synchronisation/", admin.site.admin_view(views.admin_sync_dashboard), name="synchronisation"),
            path("synchronisation/export/", admin.site.admin_view(views.admin_sync_export), name="sync_export"),
            path("synchronisation/import/", admin.site.admin_view(views.admin_sync_import), name="sync_import"),
            path("synchronisation/backup-complet/", admin.site.admin_view(views.admin_backup_complet), name="backup_complet"),
            path("formation/<int:formation_id>/workspace/", admin.site.admin_view(views.workspace_formation), name="workspace_formation"),
            path("emails/", views.admin_emails_dashboard, name="admin_emails"),
            path("emails/preview/<str:template_name>/", views.admin_email_preview, name="email_preview"),
            path("emails/test/", views.admin_email_test, name="email_test"),
            path("dashboard-ia/", views.vue_dashboard_ia, name="dashboard_ia"),
            path("dashboard-ia/quotas/", admin.site.admin_view(self.vue_dashboard_quotas_ia), name="dashboard_quotas_ia"),
            path("export/ventes-excel/", views.export_ventes_excel, name="export_ventes_excel"),
            path("export/ventes-pdf/", views.export_ventes_pdf, name="export_ventes_pdf"),
            path("dashboard-crm/", views.dashboard_crm, name="dashboard_crm"),
            path("crm/interaction/<int:inscription_id>/", views.ajouter_interaction_crm, name="ajouter_interaction_crm"),
            path("dashboard-seo/", admin.site.admin_view(self.vue_dashboard_seo), name="dashboard_seo"),
            path("dashboard-analytics/", admin.site.admin_view(self.vue_dashboard_analytics), name="dashboard_analytics"),
            path("statistiques-academie/<int:academie_id>/", admin.site.admin_view(self.vue_statistiques_academie), name="statistiques_academie"),
            path("dashboard-executif/", admin.site.admin_view(self.vue_dashboard_executif), name="dashboard_executif"),
            path('monitoring-partenaires/', admin.site.admin_view(self.vue_monitoring_partenaires), name='monitoring-partenaires'),
            path('cohorte/<int:cohorte_id>/', admin.site.admin_view(self.vue_dashboard_cohorte), name='dashboard_cohorte'),

            # --- AJOUT : rotation de clé partenaire ---
            path(
                'partenaire/<int:partenaire_id>/rotation-cle/',
                admin.site.admin_view(self.vue_rotation_cle_partenaire),
                name='rotation_cle_partenaire',
            ),
            path('dashboard-temoignages/', admin.site.admin_view(self.vue_dashboard_temoignages), name='dashboard_temoignages'),
            path('dashboard-analyse-banque/', admin.site.admin_view(self.vue_dashboard_analyse_banque), name='dashboard_analyse_banque'),
        ]
        return custom_urls + original_urls

    def vue_gestion_cours(self, request):
        ecoles = Ecole.objects.prefetch_related("formations__modules__lecons").all()
        return render(request, "admin/gestion_cours.html", {"ecoles": ecoles, "title": "Gestion des cours par école", "site_header": admin.site.site_header})

    def vue_dashboard_editorial(self, request):
        articles_total = Article.objects.count()
        articles_publies = Article.objects.filter(publie=True).count()
        articles_brouillon = articles_total - articles_publies
        formations_sans_programme = Formation.objects.filter(actif=True, modules__isnull=True).distinct()
        lecons_sans_contenu = Lecon.objects.filter(Q(contenu__isnull=True) | Q(contenu="")).select_related("module__formation")[:15]
        derniers_articles = Article.objects.order_by("-date_publication")[:8]
        return render(request, "admin/dashboard_editorial.html", {
            "title": "📝 Dashboard Éditorial",
            "site_header": admin.site.site_header,
            "articles_total": articles_total,
            "articles_publies": articles_publies,
            "articles_brouillon": articles_brouillon,
            "formations_sans_programme": formations_sans_programme,
            "lecons_sans_contenu": lecons_sans_contenu,
            "derniers_articles": derniers_articles,
        })

    def vue_dashboard_executif(self, request):
        from django.contrib.auth.models import User
        from django.db.models import Sum
        maintenant = timezone.now()
        il_y_a_30j = maintenant - timedelta(days=30)
        il_y_a_60j = maintenant - timedelta(days=60)

        academie_id = request.GET.get("academie_id")
        if academie_id:
            academie_selectionnee = get_object_or_404(Academie, id=academie_id)
        else:
            academie_selectionnee = getattr(request, "academie_courante", None)

        if academie_selectionnee:
            filtre_order = Q(items__formation__ecole__academie=academie_selectionnee)
            filtre_transaction = Q(commande__items__formation__ecole__academie=academie_selectionnee)
            filtre_workflow = Q(formation__ecole__academie=academie_selectionnee)
            filtre_inscription = Q(formation__ecole__academie=academie_selectionnee)
            filtre_examen = Q(examen__formation__ecole__academie=academie_selectionnee)
            filtre_formation = Q(ecole__academie=academie_selectionnee)
        else:
            filtre_order = Q()
            filtre_transaction = Q()
            filtre_workflow = Q()
            filtre_inscription = Q()
            filtre_examen = Q()
            filtre_formation = Q()

        ca_total = Order.objects.filter(statut="paye").filter(filtre_order).aggregate(t=Sum("total"))["t"] or 0
        ca_30j = Order.objects.filter(statut="paye", date_paiement__gte=il_y_a_30j).filter(filtre_order).aggregate(t=Sum("total"))["t"] or 0
        ca_periode_precedente = Order.objects.filter(statut="paye", date_paiement__gte=il_y_a_60j, date_paiement__lt=il_y_a_30j).filter(filtre_order).aggregate(t=Sum("total"))["t"] or 0
        croissance_ca = round(((ca_30j - ca_periode_precedente) / ca_periode_precedente * 100), 1) if ca_periode_precedente else 0

        if academie_selectionnee:
            total_etudiants = User.objects.filter(is_staff=False, profil__academies=academie_selectionnee).count()
            nouveaux_etudiants_30j = User.objects.filter(is_staff=False, profil__academies=academie_selectionnee, date_joined__gte=il_y_a_30j).count()
        else:
            total_etudiants = User.objects.filter(is_staff=False).count()
            nouveaux_etudiants_30j = User.objects.filter(is_staff=False, date_joined__gte=il_y_a_30j).count()

        paiements_en_attente = Transaction.objects.filter(statut="en_verification").filter(filtre_transaction).count()
        formations_en_revision = WorkflowFormation.objects.filter(etat_actuel="en_revision").filter(filtre_workflow).count()
        leads_non_traites = Inscription.objects.filter(statut_lead="nouveau").filter(filtre_inscription).count()
        tentatives_30j = TentativeExamen.objects.filter(date_debut__gte=il_y_a_30j).filter(filtre_examen).count()
        stats_examens_30j = TentativeExamen.objects.filter(date_debut__gte=il_y_a_30j).filter(filtre_examen).aggregate(
            total=Count('id'),
            reussies=Count('id', filter=Q(reussi=True))
        )
        taux_reussite_examens_pct = round(
            (stats_examens_30j['reussies'] / stats_examens_30j['total']) * 100, 1
        ) if stats_examens_30j['total'] else None
        tentatives_academie = TentativeExamen.objects.filter(filtre_examen).count()
        articles_publies = Article.objects.filter(publie=True).count()
        articles_sans_seo = Article.objects.filter(publie=True, meta_description="").count()
        formations_actives = Formation.objects.filter(actif=True).filter(filtre_formation).count()
        formations_brouillon = WorkflowFormation.objects.filter(etat_actuel="brouillon").filter(filtre_workflow).count()
        toutes_academies = Academie.objects.filter(actif=True)

        return render(request, "admin/dashboard_executif.html", {
            "title": "🧠 Dashboard Exécutif",
            "site_header": admin.site.site_header,
            "ca_total": ca_total,
            "ca_30j": ca_30j,
            "croissance_ca": croissance_ca,
            "total_etudiants": total_etudiants,
            "nouveaux_etudiants_30j": nouveaux_etudiants_30j,
            "paiements_en_attente": paiements_en_attente,
            "formations_en_revision": formations_en_revision,
            "leads_non_traites": leads_non_traites,
            "tentatives_30j": tentatives_30j,
            "tentatives_academie": tentatives_academie,
            "articles_publies": articles_publies,
            "articles_sans_seo": articles_sans_seo,
            "formations_actives": formations_actives,
            "formations_brouillon": formations_brouillon,
            "toutes_academies": toutes_academies,
            "academie_selectionnee": academie_selectionnee,
        })

    def vue_dashboard_seo(self, request):
        articles = Article.objects.filter(publie=True)
        articles_avec_score = sorted(
            [{"article": a, "score": a.score_seo(), "suggestions": a.suggestions_seo()} for a in articles],
            key=lambda x: x["score"],
        )
        score_moyen = round(sum(a["score"] for a in articles_avec_score) / len(articles_avec_score)) if articles_avec_score else 0
        return render(request, "admin/dashboard_seo.html", {
            "title": "🔍 Suite SEO",
            "site_header": admin.site.site_header,
            "articles_avec_score": articles_avec_score,
            "score_moyen": score_moyen,
        })

    def vue_dashboard_analytics(self, request):
        return render(request, "admin/dashboard_analytics.html", {
            "title": "📈 Analytics Global",
            "site_header": admin.site.site_header,
            "ventes_par_ecole": Formation.objects.values("ecole__nom").annotate(total=Count("orderitem", filter=Q(orderitem__commande__statut="paye"))).order_by("-total"),
            "articles_top": Article.objects.filter(publie=True).order_by("-nb_vues")[:5],
            "quiz_taux_reussite": ResultatQuiz.objects.count(),
            "total_affilies": Affilie.objects.filter(actif=True).count(),
        })

    def vue_statistiques_academie(self, request, academie_id):
        academie = Academie.objects.get(id=academie_id)
        ecoles = academie.ecoles.all()
        formations = Formation.objects.filter(ecole__academie=academie)
        enseignants = Enseignant.objects.filter(formations_attribuees__ecole__academie=academie).distinct()
        articles = Article.objects.filter(academie=academie)
        ca_total = Order.objects.filter(items__formation__ecole__academie=academie, statut="paye").distinct().aggregate(t=Sum("total"))["t"] or 0
        tentatives_examens = TentativeExamen.objects.filter(examen__formation__ecole__academie=academie).count()
        return render(request, "admin/statistiques_academie.html", {
            "title": f"📊 Statistiques — {academie.nom}",
            "site_header": admin.site.site_header,
            "academie": academie,
            "nb_ecoles": ecoles.count(),
            "nb_formations": formations.filter(actif=True).count(),
            "nb_enseignants": enseignants.count(),
            "nb_articles": articles.filter(publie=True).count(),
            "nb_etudiants": academie.nb_etudiants(),
            "ca_total": ca_total,
            "tentatives_examens": tentatives_examens,
            "ecoles": ecoles,
        })

    def vue_monitoring_partenaires(self, request):
        from datetime import timedelta
        il_y_a_1h = timezone.now() - timedelta(hours=1)
        il_y_a_24h = timezone.now() - timedelta(hours=24)
        partenaires = PartenaireAPI.objects.filter(actif=True).annotate(requetes_24h=Count('requetes', filter=Q(requetes__date_creation__gte=il_y_a_24h)))
        partenaires_data = []
        for p in partenaires:
            requetes_1h = LogRequetePartenaire.objects.filter(partenaire=p, date_creation__gte=il_y_a_1h).count()
            erreurs_24h = LogRequetePartenaire.objects.filter(partenaire=p, date_creation__gte=il_y_a_24h, statut_reponse__gte=400).count()
            taux_usage = round((requetes_1h / p.limite_requetes_heure) * 100) if p.limite_requetes_heure else 0
            partenaires_data.append({
                'partenaire': p,
                'requetes_1h': requetes_1h,
                'taux_usage': taux_usage,
                'erreurs_24h': erreurs_24h,
                'proche_limite': taux_usage >= 80,
            })
        return render(request, 'admin/monitoring_partenaires.html', {
            'title': '📡 Monitoring API Partenaires',
            'site_header': admin.site.site_header,
            'partenaires_data': partenaires_data,
        })

    @staff_member_required
    def vue_dashboard_cohorte(self, request, cohorte_id):
        cohorte = Cohorte.objects.prefetch_related('formations', 'membres').get(id=cohorte_id)
        membres_details = []
        for membre in cohorte.membres.all():
            progressions_par_formation = {f.nom: f.progression_pour(membre) for f in cohorte.formations.all()}
            membres_details.append({
                'membre': membre,
                'progressions': progressions_par_formation,
                'nb_projets': ProjetEtudiant.objects.filter(auteur=membre, formation_liee__in=cohorte.formations.all()).count(),
                'nb_certificats': Certificat.objects.filter(utilisateur=membre, formation__in=cohorte.formations.all()).count(),
                'nb_competences': CompetenceValidee.objects.filter(utilisateur=membre, formation_origine__in=cohorte.formations.all()).values('competence').distinct().count(),
            })
        return render(request, 'admin/dashboard_cohorte.html', {
            'title': f'👥 {cohorte.nom}',
            'site_header': admin.site.site_header,
            'cohorte': cohorte,
            'membres_details': membres_details,
        })

    @staff_member_required
    def vue_dashboard_temoignages(self, request):
        from django.db.models import Avg, Count
        from django.utils import timezone
        from datetime import timedelta

        temoignages = Temoignage.objects.filter(approuve=True)

        nb_total = temoignages.count()
        moyenne_generale = round(temoignages.aggregate(m=Avg('note'))['m'] or 0, 1)
        taux_satisfaction = round(
            (temoignages.filter(note__gte=4).count() / nb_total * 100) if nb_total else 0
        )

        formations_mieux_notees = temoignages.values('formation_suivie__nom').annotate(
            moyenne=Avg('note'), nb=Count('id')
        ).filter(nb__gte=1).order_by('-moyenne')[:5]

        ecoles_mieux_notees = temoignages.values('formation_suivie__ecole__nom').annotate(
            moyenne=Avg('note'), nb=Count('id')
        ).filter(nb__gte=1).order_by('-moyenne')[:5]

        # Évolution mensuelle (6 derniers mois)
        evolution = []
        labels = []
        data = []
        for i in range(5, -1, -1):
            debut_mois = (timezone.now() - timedelta(days=30 * i)).replace(day=1)
            fin_mois = debut_mois + timedelta(days=32)
            nb_mois = temoignages.filter(date_creation__gte=debut_mois, date_creation__lt=fin_mois).count()
            evolution.append({'mois': debut_mois.strftime('%b %Y'), 'nb': nb_mois})
            labels.append(debut_mois.strftime('%b %Y'))
            data.append(nb_mois)

        return render(request, 'admin/dashboard_temoignages.html', {
            'title': '💬 Statistiques Témoignages',
            'site_header': admin.site.site_header,
            'nb_total': nb_total,
            'moyenne_generale': moyenne_generale,
            'taux_satisfaction': taux_satisfaction,
            'formations_mieux_notees': formations_mieux_notees,
            'ecoles_mieux_notees': ecoles_mieux_notees,
            'evolution': evolution,
            'chart_labels': labels,   # <-- Nouveau
            'chart_data': data,        # <-- Nouveau
        })


    def vue_dashboard_analyse_banque(self, request):
        from django.db.models import Avg, Count, Q as DjangoQ
        from academie.models_banque import QuestionBanque, StatistiqueQuestion, ExamenGenere, GabaritExamen

        gabarit = GabaritExamen.objects.filter(phase_test=True).first()

        examens_termines = ExamenGenere.objects.filter(
            gabarit=gabarit, statut='termine'
        ).select_related('utilisateur') if gabarit else ExamenGenere.objects.none()

        # Statistiques globales du test pilote
        nb_participants = examens_termines.values('utilisateur').distinct().count()
        score_moyen = examens_termines.aggregate(m=Avg('score_pourcentage'))['m'] or 0
        nb_reussis = examens_termines.filter(reussi=True).count()

        # Questions suspectes (trop faciles ou trop difficiles)
        questions_utilisees = StatistiqueQuestion.objects.filter(
            nb_utilisations__gte=1
        ).select_related('question', 'question__module', 'question__categorie')

        questions_a_revoir = [s for s in questions_utilisees if s.necessite_revision()]
        questions_a_revoir.sort(key=lambda s: s.taux_reussite())

        # Répartition par module
        stats_par_module = {}
        for s in questions_utilisees:
            module_nom = s.question.module.nom
            stats_par_module.setdefault(module_nom, {'utilisations': 0, 'reussites': 0})
            stats_par_module[module_nom]['utilisations'] += s.nb_utilisations
            stats_par_module[module_nom]['reussites'] += s.nb_reussites

        for module_nom, data in stats_par_module.items():
            data['taux'] = round((data['reussites'] / data['utilisations']) * 100) if data['utilisations'] else 0

        return render(request, 'admin/dashboard_analyse_banque.html', {
            'title': '🔍 Analyse Test Pilote — Banque de Questions',
            'site_header': admin.site.site_header,
            'gabarit': gabarit,
            'nb_participants': nb_participants,
            'score_moyen': round(score_moyen, 1),
            'nb_reussis': nb_reussis,
            'nb_total_termines': examens_termines.count(),
            'questions_a_revoir': questions_a_revoir[:20],
            'stats_par_module': stats_par_module,
            'examens_detail': examens_termines.order_by('-score_pourcentage'),
        })

    def vue_dashboard_quotas_ia(self, request):
        from django.core.cache import cache
        from .services.ia_service import QUOTA_QUOTIDIEN_GEMINI, _circuit_ouvert
        aujourdhui = timezone.now().strftime("%Y-%m-%d")
        cle_quota = f"gemini_quota_{aujourdhui}"
        utilisation_actuelle = cache.get(cle_quota, 0)
        quota_max = QUOTA_QUOTIDIEN_GEMINI
        quota_restant = max(quota_max - utilisation_actuelle, 0)
        pourcentage_utilise = round(utilisation_actuelle / quota_max * 100, 1) if quota_max else 0
        return render(request, "admin/dashboard_quotas_ia.html", {
            "title": "🤖 Dashboard IA — Quotas Gemini",
            "site_header": admin.site.site_header,
            "utilisation_actuelle": utilisation_actuelle,
            "quota_max": quota_max,
            "quota_restant": quota_restant,
            "pourcentage_utilise": pourcentage_utilise,
            "circuit_ouvert": _circuit_ouvert(),
        })

    # --- NOUVELLE VUE : rotation de clé partenaire ---
    @staff_member_required
    def vue_rotation_cle_partenaire(self, request, partenaire_id):
        """Vue admin pour la rotation de clé API d'un partenaire."""
        from .models import PartenaireAPI
        partenaire = PartenaireAPI.objects.get(id=partenaire_id)
        partenaire.faire_tourner_la_cle()
        messages.success(
            request,
            f"✅ Nouvelle clé générée pour {partenaire.nom}. Communique-la de façon sécurisée."
        )
        return redirect(f'/admin/academie/partenaireapi/{partenaire_id}/change/')


# ================================================
# Réorganisation de l'admin
# ================================================
_original_get_urls = admin.site.get_urls
_gestion = GestionCoursAdminSite()

def get_urls_avec_gestion():
    return _gestion.get_urls(_original_get_urls())

admin.site.get_urls = get_urls_avec_gestion

admin.site.site_header = "Blessy Tech Academy — Back Office"
admin.site.site_title = "BTA Admin"
admin.site.index_title = "Tableau de bord"


def get_app_list_reorganise(self, request, app_label=None):
    app_list = admin.AdminSite.get_app_list(admin.site, request, app_label)
    
    # --- NOUVELLE STRUCTURE DES GROUPES ---
    sections = {
        '🎓 Pédagogie': ['Ecole', 'Formation', 'Module', 'Lecon', 'Quiz', 'Question', 'Parcours', 'Examen', 'WorkflowFormation', 'NoteLecon', 'GradebookEntry', 'LearningOutcome'],
        '🧠 Banque de Questions & Évaluations': [
            'ModuleBanque', 'CategorieBanque', 'SousCategorieBanque',
            'QuestionBanque', 'VersionQuestionBanque', 'StatistiqueQuestion',
            'GabaritExamen', 'CompositionGabarit',
            'ExamenGenere', 'QuestionExamenGenere', 'ReponseEtudiantBanque'
        ],
        '🎓 Certifications & Preuves': [
            'Certificat', 'CertificatHistorique', 'RegistreEmissionCertificat',
            'EligibiliteCertification', 'AccesFormationDebloque',
            'Competence', 'CompetenceValidee'
        ],
        '💰 Commerce': ['Order', 'OrderItem', 'Transaction', 'Invoice', 'Coupon', 'Promotion', 'Subscription', 'PlanAbonnement', 'Affilie'],
        '👥 Communauté & Engagement': ['Sujet', 'Reponse', 'Reaction', 'BadgeForum', 'ProjetEtudiant', 'Temoignage', 'Ambassadeur'],
        '📢 Marketing & Contenu': ['Article', 'OutilRecommande', 'Outil', 'EtudeDeCas', 'Evenement', 'Inscription', 'InteractionCRM', 'Partenaire'],
        '⚙️ Système & Administration': [
            'Academie', 'ProfilUtilisateur', 'Enseignant', 'LogAudit',
            'PartenaireAPI', 'MoyenPaiement', 'AlerteFraude',
            'PushSubscription', 'NotificationPushEnvoyee', 'HistoriqueConversationIA'
        ],
        '📦 Autres (Gouvernance & Divers)': [
            'Cohorte', 'Enrollment', 'Parrainage', 'DemandeTemoignage',
            'StreakEtudiant', 'DisponibiliteMentor', 'ReservationMentorat',
            'SoumissionProjet', 'WorkflowArticle', 'NoteLecon', 'GradebookEntry'
        ],
    }
    # --- FIN DE LA MODIFICATION ---

    modeles_tous = []
    for app in app_list:
        modeles_tous.extend(app.get('models', []))
    nouveau_app_list = []
    for nom_section, noms_modeles in sections.items():
        modeles_section = [m for m in modeles_tous if m['object_name'] in noms_modeles]
        if modeles_section:
            nouveau_app_list.append({'name': nom_section, 'app_label': nom_section, 'app_url': '#', 'models': modeles_section})
    
    noms_classes = [n for liste in sections.values() for n in liste]
    modeles_restants = [m for m in modeles_tous if m['object_name'] not in noms_classes]
    if modeles_restants:
        nouveau_app_list.append({'name': '📦 Autres', 'app_label': 'autres', 'app_url': '#', 'models': modeles_restants})
    
    return nouveau_app_list

admin.site.get_app_list = get_app_list_reorganise.__get__(admin.site)


# ================================================
# ADMIN.PY — Registre d'émission certificat (Lecture seule stricte)
# ================================================

from .models import RegistreEmissionCertificat

@admin.register(RegistreEmissionCertificat)
class RegistreEmissionCertificatAdmin(admin.ModelAdmin):
    list_display = ['certificat', 'action', 'effectue_par', 'date_evenement']
    list_filter = ['action']
    readonly_fields = [f.name for f in RegistreEmissionCertificat._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


# ================================================
# ADMIN.PY — Administration Enrollment (registre canonique)
# ================================================
from .models import Enrollment

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ['utilisateur', 'formation', 'origine', 'statut', 'date_inscription']
    list_filter = ['origine', 'statut']
    search_fields = ['utilisateur__username', 'formation__nom']


# ================================================
# ADMIN — EligibiliteCertification (processus contrôlé pour cohortes)
# ================================================

@admin.register(EligibiliteCertification)
class EligibiliteCertificationAdmin(admin.ModelAdmin):
    list_display = [
        'utilisateur',
        'cohorte',
        'formation',
        'frais_paye',
        'valide_par',
        'date_validation',
        'certificat_genere',
        'boutons_actions',
    ]
    list_filter = ['cohorte', 'frais_paye', 'formation']
    search_fields = ['utilisateur__username', 'formation__nom']
    readonly_fields = ['date_creation', 'certificat_genere', 'date_validation', 'valide_par']

    def boutons_actions(self, obj):
        boutons = []

        # 1. Si frais non payés et pas encore de certificat → bouton "Valider paiement"
        if not obj.frais_paye and not obj.certificat_genere:
            boutons.append(
                f'<a href="/admin/eligibilite/{obj.id}/valider-paiement/" '
                f'style="background:#22c55e;color:white;padding:4px 10px;border-radius:6px;'
                f'text-decoration:none;font-size:11px;font-weight:700;margin-right:4px;">'
                f'✓ Valider paiement</a>'
            )

        # 2. Si frais payés et pas encore de certificat → bouton "Générer certificat"
        if obj.frais_paye and not obj.certificat_genere:
            boutons.append(
                f'<a href="/admin/eligibilite/{obj.id}/generer/" '
                f'style="background:#003B8E;color:white;padding:4px 10px;border-radius:6px;'
                f'text-decoration:none;font-size:11px;font-weight:700;margin-right:4px;">'
                f'🎓 Générer certificat</a>'
            )

        # 3. Si certificat déjà généré → bouton PDF et/ou Annuler
        if obj.certificat_genere:
            if obj.certificat_genere.fichier_pdf:
                boutons.append(
                    f'<a href="{obj.certificat_genere.fichier_pdf.url}" '
                    f'style="background:#00B5E2;color:white;padding:4px 10px;border-radius:6px;'
                    f'text-decoration:none;font-size:11px;font-weight:700;margin-right:4px;">'
                    f'📥 PDF</a>'
                )
            if obj.certificat_genere.statut == 'valide':
                boutons.append(
                    f'<a href="/admin/eligibilite/{obj.id}/annuler/" '
                    f'onclick="return confirm(\'⚠️ Annuler ce certificat ?\');" '
                    f'style="background:#ef4444;color:white;padding:4px 10px;border-radius:6px;'
                    f'text-decoration:none;font-size:11px;font-weight:700;">'
                    f'🚫 Annuler</a>'
                )

        return format_html(''.join(boutons)) if boutons else "—"
    boutons_actions.short_description = 'Actions'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:eligibilite_id>/valider-paiement/',
                self.admin_site.admin_view(self.valider_paiement_view),
                name='eligibilite_valider_paiement',
            ),
            path(
                '<int:eligibilite_id>/generer/',
                self.admin_site.admin_view(self.generer_certificat_view),
                name='eligibilite_generer_certificat',
            ),
            path(
                '<int:eligibilite_id>/annuler/',
                self.admin_site.admin_view(self.annuler_certificat_view),
                name='eligibilite_annuler_certificat',
            ),
        ]
        return custom_urls + urls

    def valider_paiement_view(self, request, eligibilite_id):
        """Marque les frais comme payés et met à jour le statut."""
        eligibilite = EligibiliteCertification.objects.get(id=eligibilite_id)
        if not eligibilite.frais_paye:
            eligibilite.frais_paye = True
            eligibilite.save()
            messages.success(request, f"✅ Paiement validé pour {eligibilite.utilisateur.username}")
        else:
            messages.warning(request, "Les frais sont déjà marqués comme payés.")
        return redirect('admin:academie_eligibilitecertification_change', eligibilite_id)

    def generer_certificat_view(self, request, eligibilite_id):
        """Génère le certificat final via la méthode valider() du modèle."""
        eligibilite = EligibiliteCertification.objects.get(id=eligibilite_id)
        try:
            certificat = eligibilite.valider(request.user)
            messages.success(request, f"🎓 Certificat généré avec succès : {certificat.numero}")
        except ValueError as e:
            messages.error(request, f"❌ {str(e)}")
        return redirect('admin:academie_eligibilitecertification_change', eligibilite_id)

    def annuler_certificat_view(self, request, eligibilite_id):
        """Révoque le certificat associé (annulation)."""
        eligibilite = EligibiliteCertification.objects.get(id=eligibilite_id)
        if eligibilite.certificat_genere:
            certificat = eligibilite.certificat_genere
            certificat.revoquer(admin=request.user, raison="Annulation admin")
            eligibilite.certificat_genere = None
            eligibilite.frais_paye = False
            eligibilite.save()
            messages.success(request, f"🚫 Certificat {certificat.numero} annulé.")
        else:
            messages.warning(request, "Aucun certificat à annuler pour cette éligibilité.")
        return redirect('admin:academie_eligibilitecertification_change', eligibilite_id)

    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        try:
            return request.user.profil.role in ['admin', 'formateur']
        except Exception:
            return False


# ================================================
# ADMIN.PY — Administration Banque de Questions
# ================================================

from academie.models_banque import (
    ModuleBanque, CategorieBanque, SousCategorieBanque, QuestionBanque,
    GabaritExamen, CompositionGabarit, ExamenGenere, StatistiqueQuestion,
    VersionQuestionBanque,
)
from users.admin import RolePermissionMixin


@admin.register(ModuleBanque)
class ModuleBanqueAdmin(admin.ModelAdmin):
    list_display = ['icone', 'nom', 'code', 'hors_examen_principal', 'ordre']
    list_editable = ['ordre']


@admin.register(CategorieBanque)
class CategorieBanqueAdmin(admin.ModelAdmin):
    list_display = ['nom', 'module', 'ordre']
    list_filter = ['module']


@admin.register(SousCategorieBanque)
class SousCategorieBanqueAdmin(admin.ModelAdmin):
    list_display = ['nom', 'categorie']
    list_filter = ['categorie__module']


class StatistiqueQuestionInline(admin.StackedInline):
    model = StatistiqueQuestion
    extra = 0
    readonly_fields = ['nb_utilisations', 'nb_reussites', 'temps_moyen_secondes']


@admin.register(QuestionBanque)
class QuestionBanqueAdmin(RolePermissionMixin, admin.ModelAdmin):
    roles_autorises = ['admin', 'formateur']
    change_list_template = 'admin/questionbanque_changelist.html'  # <-- AJOUT

    list_display = ['identifiant_unique', 'module', 'categorie', 'niveau', 'type_question', 'statut', 'points_ponderes_affiche', 'taux_reussite_affiche']
    list_filter = ['module', 'niveau', 'type_question', 'statut', 'categorie']
    search_fields = ['identifiant_unique', 'enonce', 'mots_cles']
    readonly_fields = ['identifiant_unique', 'version']
    inlines = [StatistiqueQuestionInline]
    actions = ['action_dupliquer', 'action_archiver', 'action_activer']

    fieldsets = [
        ('📌 Classification', {'fields': ['module', 'categorie', 'sous_categorie', 'niveau', 'type_question', 'competence_evaluee']}),
        ('📝 Contenu', {'fields': ['enonce', 'illustration', 'fichier_support']}),
        ('✅ Réponses', {'fields': ['reponses_possibles', 'reponse_texte_courte']}),
        ('🎓 Pédagogie', {'fields': ['explication_pedagogique', 'reference_cours', 'mots_cles']}),
        ('⚙️ Paramètres', {'fields': ['temps_conseille_secondes', 'points_base']}),
        ('🔐 Gouvernance', {'fields': ['statut', 'cree_par', 'valide_par']}),
    ]

    def points_ponderes_affiche(self, obj):
        return obj.points_ponderes()
    points_ponderes_affiche.short_description = 'Points pondérés'

    def taux_reussite_affiche(self, obj):
        stats = getattr(obj, 'statistiques', None)
        return f"{stats.taux_reussite()}%" if stats else "—"
    taux_reussite_affiche.short_description = 'Taux réussite'

    @admin.action(description="📋 Dupliquer les questions sélectionnées")
    def action_dupliquer(self, request, queryset):
        for q in queryset:
            q.dupliquer(request.user)
        self.message_user(request, f"✅ {queryset.count()} question(s) dupliquée(s)")

    @admin.action(description="📦 Archiver")
    def action_archiver(self, request, queryset):
        queryset.update(statut='archivee')

    @admin.action(description="✅ Activer")
    def action_activer(self, request, queryset):
        queryset.update(statut='active')

    def save_model(self, request, obj, form, change):
        if not change:
            obj.cree_par = request.user
        else:
            obj.version += 1
            VersionQuestionBanque.objects.create(
                question=obj, numero_version=obj.version,
                contenu_snapshot={'enonce': obj.enonce, 'reponses': obj.reponses_possibles},
                modifie_par=request.user,
            )
        super().save_model(request, obj, form, change)

    # ================================================================
    # AJOUTS IMPORT / EXPORT CSV
    # ================================================================
    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom = [
            path('export-csv/', self.admin_site.admin_view(self.exporter_csv), name='questionbanque_export'),
            path('import-csv/', self.admin_site.admin_view(self.importer_csv), name='questionbanque_import'),
        ]
        return custom + urls

    def exporter_csv(self, request):
        import csv
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="banque_questions.csv"'
        writer = csv.writer(response)
        writer.writerow(['identifiant', 'module', 'categorie', 'niveau', 'type', 'enonce', 'reponses_json', 'explication', 'points'])
        for q in QuestionBanque.objects.all():
            writer.writerow([
                q.identifiant_unique,
                q.module.code,
                q.categorie.nom,
                q.niveau,
                q.type_question,
                q.enonce,
                str(q.reponses_possibles),
                q.explication_pedagogique,
                q.points_base
            ])
        return response

    def importer_csv(self, request):
        if request.method == 'POST' and request.FILES.get('fichier_csv'):
            import csv, io, json
            fichier = io.TextIOWrapper(request.FILES['fichier_csv'].file, encoding='utf-8')
            reader = csv.DictReader(fichier)
            importees = 0
            for ligne in reader:
                module = ModuleBanque.objects.filter(code=ligne['module']).first()
                categorie = CategorieBanque.objects.filter(module=module, nom=ligne['categorie']).first()
                if module and categorie:
                    QuestionBanque.objects.create(
                        module=module,
                        categorie=categorie,
                        niveau=ligne['niveau'],
                        type_question=ligne['type'],
                        enonce=ligne['enonce'],
                        reponses_possibles=json.loads(ligne['reponses_json']),
                        explication_pedagogique=ligne['explication'],
                        points_base=float(ligne['points']),
                        cree_par=request.user,
                        statut='brouillon',
                    )
                    importees += 1
            messages.success(request, f"✅ {importees} question(s) importée(s)")
            return redirect('..')
        return render(request, 'admin/import_csv_questions.html')
class CompositionGabaritInline(admin.TabularInline):
    model = CompositionGabarit
    extra = 1


@admin.register(GabaritExamen)
class GabaritExamenAdmin(admin.ModelAdmin):
    list_display = ['nom', 'nombre_questions_total_affiche', 'points_total_affiche', 'duree_minutes', 'actif']
    inlines = [CompositionGabaritInline]

    def nombre_questions_total_affiche(self, obj):
        return obj.nombre_questions_total()
    nombre_questions_total_affiche.short_description = 'Nb questions'

    def points_total_affiche(self, obj):
        return obj.points_total()
    points_total_affiche.short_description = 'Points totaux'


@admin.register(ExamenGenere)
class ExamenGenereAdmin(admin.ModelAdmin):
    list_display = ['utilisateur', 'gabarit', 'statut', 'score_pourcentage', 'reussi', 'date_debut']
    list_filter = ['statut', 'reussi', 'gabarit']
    search_fields = ['utilisateur__username']


@admin.register(StatistiqueQuestion)
class StatistiqueQuestionAdmin(admin.ModelAdmin):
    list_display = ['question', 'nb_utilisations', 'nb_reussites', 'temps_moyen_secondes']
    readonly_fields = ['nb_utilisations', 'nb_reussites', 'temps_moyen_secondes']