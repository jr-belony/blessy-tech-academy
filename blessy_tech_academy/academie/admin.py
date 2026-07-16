from django.urls import path
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import admin
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from datetime import timedelta
from simple_history.admin import SimpleHistoryAdmin
from adminsortable2.admin import SortableAdminMixin, SortableInlineAdminMixin, SortableAdminBase
from academie import views
from . import views
from .models import (Formation, Inscription, Ecole, Quiz, Question, ResultatQuiz, Module, Lecon, ProgressionLecon,
Parcours, Sujet, Reponse, Reaction, OutilRecommande, Article, Temoignage, MoyenPaiement, Coupon, Promotion, Order, OrderItem,
Invoice, Transaction, Refund, AccesFormationDebloque, ChoixExamen, QuestionExamen, 
TentativeExamen, Examen, ProfilUtilisateur, LogAudit, InteractionCRM, Enseignant,WorkflowFormation)

# ================================================
# Thème CSS global pour tout l'admin
# ================================================
class AdminThemeMixin:
    """Mixin qui injecte le CSS premium dans toutes les pages admin."""
    class Media:
        css = {
            'all': ['academie/admin/theme_premium.css']
        }


# ================================================
# ADMIN — Écoles (Formateur, RespAcademique, Admin, SuperAdmin)
# ================================================
@admin.register(Ecole)
class EcoleAdmin(AdminThemeMixin, admin.ModelAdmin):
    list_display = ['icone', 'nom', 'ordre']
    list_editable = ['ordre']
    search_fields = ['nom']

    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        try:
            return request.user.profil.role in ['formateur', 'resp_academique', 'admin']
        except Exception:
            return False
class ModuleInline(SortableInlineAdminMixin, admin.TabularInline):
    model = Module
    extra = 1
    fields = ['ordre', 'titre', 'description']
    show_change_link = True


class LeconInline(SortableInlineAdminMixin, admin.TabularInline):
    model = Lecon
    extra = 3
    fields = ['ordre', 'titre', 'resume', 'duree_minutes']


class ReponseInline(admin.TabularInline):
    model = Reponse
    extra = 0
    fields = ['auteur', 'contenu', 'acceptee', 'date_creation']
    readonly_fields = ['date_creation']

class ModuleInline(SortableInlineAdminMixin, admin.TabularInline):
    model = Module
    extra = 1
    fields = ['ordre', 'titre', 'description']
    show_change_link = True


# ================================================
# ADMIN — Formations (Formateur, RespAcademique, Admin, SuperAdmin)
# ================================================
@admin.register(Formation)
class FormationAdmin(AdminThemeMixin, SortableAdminBase, SimpleHistoryAdmin):
    list_display = [
        'icone', 'nom', 'ecole', 'niveau',
        'duree_mois', 'prix', 'actif', 'bouton_workspace'
    ]
    list_filter = ['actif', 'niveau', 'ecole']
    search_fields = ['nom', 'description']
    autocomplete_fields = ['formation_upgrade']
    list_editable = ['actif']
    inlines = [ModuleInline]

    fieldsets = [
        ('Informations principales', {
            'fields': [
                'ecole', 'nom', 'icone', 'description',
                'niveau', 'duree_mois', 'prix', 'actif',
                'gratuit', 'formation_upgrade',
            ]
        }),
        ('Contenu détaillé', {
            'fields': ['debouches', 'prerequis', 'certifications'],
            'classes': ['collapse'],
        }),
    ]

    actions = ['partager_sur_reseaux']

    @admin.action(description="📢 Partager les formations sélectionnées sur les réseaux sociaux (simulation)")
    def partager_sur_reseaux(self, request, queryset):
        from .social import partager_formation
        n = 0
        for formation in queryset:
            partager_formation(formation)
            n += 1
        self.message_user(request, f"✅ {n} formation(s) partagée(s) (simulation). Voir les logs pour le contenu.")

    def bouton_workspace(self, obj):
        from django.utils.html import format_html
        url = f"/admin/formation/{obj.id}/workspace/"
        return format_html(
            '<a href="{}" style="background:#00B4D8; color:white; padding:4px 12px; border-radius:6px; text-decoration:none; font-size:11px; font-weight:700;">🗂️ Ouvrir le Workspace</a>',
            url
        )
    bouton_workspace.short_description = 'Workspace'

    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        try:
            return request.user.profil.role in ['formateur', 'resp_academique', 'admin']
        except Exception:
            return False

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        try:
            return request.user.profil.role in ['resp_academique', 'admin']
        except Exception:
            return False

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        try:
            return request.user.profil.role in ['admin']
        except Exception:
            return False

    class Media:
        js = ['academie/admin/generer_ia.js', 'academie/admin/generer_programme.js']

# ================================================
# ADMIN — Inscriptions CRM (Support, Marketing, Admin, SuperAdmin)
# ================================================
class InteractionCRMInline(admin.TabularInline):
    model = InteractionCRM
    extra = 0
    readonly_fields = ['auteur', 'date_creation']
@admin.register(Inscription)
class InscriptionAdmin(AdminThemeMixin, admin.ModelAdmin):
    list_display = [
        'prenom', 'nom', 'email', 'formation',
        'sujet', 'statut_lead', 'assigne_a', 'date_inscription', 'traite'
    ]
    list_filter = ['traite', 'formation', 'sujet', 'statut_lead', 'source_lead']
    search_fields = ['prenom', 'nom', 'email']
    list_editable = ['traite', 'statut_lead']
    readonly_fields = ['date_inscription']
    inlines = [InteractionCRMInline]

    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        try:
            return request.user.profil.role in ['support', 'marketing', 'admin']
        except Exception:
            return False
# ================================================
# ADMIN — Quiz (Formateur, Examinateur, RespAcademique, Admin, SuperAdmin)
# ================================================
class QuestionInline(admin.TabularInline):
    model = Question
    extra = 5
    fields = ['ordre', 'texte', 'choix_a', 'choix_b', 'choix_c', 'choix_d', 'bonne_reponse']
@admin.register(Quiz)
class QuizAdmin(AdminThemeMixin, admin.ModelAdmin):
    list_display = ['titre', 'formation', 'nombre_questions', 'limite_temps_minutes', 'actif', 'date_creation']
    list_filter = ['actif', 'formation']
    search_fields = ['titre']
    list_editable = ['actif', 'limite_temps_minutes']
    inlines = [QuestionInline]

    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        try:
            return request.user.profil.role in ['formateur', 'examinateur', 'resp_academique', 'admin']
        except Exception:
            return False

    class Media:
        js = ['academie/admin/generer_quiz.js']


# ================================================
# ADMIN — Résultats Quiz (Examinateur, Correcteur, RespAcademique, Admin, SuperAdmin)
# ================================================
@admin.register(ResultatQuiz)
class ResultatQuizAdmin(AdminThemeMixin, admin.ModelAdmin):
    list_display = ['utilisateur', 'quiz', 'score', 'total_questions', 'pourcentage', 'date_passage']
    list_filter = ['quiz']
    search_fields = ['utilisateur__username']
    readonly_fields = ['date_passage']

    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        try:
            return request.user.profil.role in ['examinateur', 'correcteur', 'resp_academique', 'admin']
        except Exception:
            return False

# ================================================
# ADMIN — Modules (Formateur, RespAcademique, Admin, SuperAdmin)
# ================================================
@admin.register(Module)
class ModuleAdmin(AdminThemeMixin, SortableAdminBase, admin.ModelAdmin):
    list_display = ['titre', 'get_ecole', 'formation', 'ordre', 'nombre_lecons']
    list_filter = ['formation__ecole', 'formation']
    search_fields = ['titre', 'formation__nom']
    ordering = ['formation__ecole', 'formation', 'ordre']
    inlines = [LeconInline]

    def get_ecole(self, obj):
        return obj.formation.ecole if obj.formation.ecole else "—"
    get_ecole.short_description = 'École'
    get_ecole.admin_order_field = 'formation__ecole'

    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        try:
            return request.user.profil.role in ['formateur', 'resp_academique', 'admin']
        except Exception:
            return False

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        try:
            return request.user.profil.role in ['resp_academique', 'admin']
        except Exception:
            return False

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        try:
            return request.user.profil.role in ['admin']
        except Exception:
            return False

    class Media:
        js = ['academie/admin/generer_programme.js', 'academie/admin/generer_contenu_module.js']


# ================================================
# ADMIN — Leçons (Formateur, RespAcademique, Admin, SuperAdmin)
# ================================================
@admin.register(Lecon)
class LeconAdmin(AdminThemeMixin, SimpleHistoryAdmin):
    list_display = ['titre', 'get_ecole', 'get_formation', 'module', 'duree_minutes', 'ordre']
    list_filter = ['module__formation__ecole', 'module__formation']
    search_fields = ['titre', 'contenu', 'module__formation__nom']
    ordering = ['module__formation__ecole', 'module__formation', 'module__ordre', 'ordre']

    def get_ecole(self, obj):
        return obj.module.formation.ecole if obj.module.formation.ecole else "—"
    get_ecole.short_description = 'École'
    get_ecole.admin_order_field = 'module__formation__ecole'

    def get_formation(self, obj):
        return obj.module.formation
    get_formation.short_description = 'Formation'
    get_formation.admin_order_field = 'module__formation'

    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        try:
            return request.user.profil.role in ['formateur', 'resp_academique', 'admin']
        except Exception:
            return False

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        try:
            return request.user.profil.role in ['resp_academique', 'admin']
        except Exception:
            return False

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        try:
            return request.user.profil.role in ['admin']
        except Exception:
            return False

    class Media:
        js = ['academie/admin/generer_contenu_lecon.js']
# ================================================
# ADMIN — Parcours (RespAcademique, Admin, SuperAdmin)
# ================================================
@admin.register(Parcours)
class ParcoursAdmin(AdminThemeMixin, admin.ModelAdmin):
    list_display = ['icone', 'titre', 'duree_mois', 'prix', 'nombre_formations', 'actif', 'ordre']
    list_filter = ['actif']
    search_fields = ['titre', 'description']
    list_editable = ['actif', 'ordre']
    filter_horizontal = ['formations']

    fieldsets = [
        ('Informations principales', {
            'fields': ['icone', 'titre', 'description', 'duree_mois', 'prix', 'actif', 'ordre']
        }),
        ('Formations incluses', {
            'fields': ['formations'],
            'description': 'Sélectionne les formations qui composent ce parcours.'
        }),
    ]

    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        try:
            return request.user.profil.role in ['resp_academique', 'admin']
        except Exception:
            return False


# ================================================
# ADMIN — Sujets (Support, Admin, SuperAdmin)
# ================================================
@admin.register(Sujet)
class SujetAdmin(AdminThemeMixin, admin.ModelAdmin):
    list_display = [
        'titre', 'auteur', 'formation', 'categorie',
        'nombre_reponses', 'vues', 'epingle', 'resolu',
        'date_creation'
    ]
    list_filter = ['categorie', 'resolu', 'epingle', 'formation']
    search_fields = ['titre', 'contenu', 'auteur__username']
    list_editable = ['epingle', 'resolu']
    readonly_fields = ['date_creation', 'date_modification', 'vues']
    inlines = [ReponseInline]

    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        try:
            return request.user.profil.role in ['support', 'admin']
        except Exception:
            return False


# ================================================
# ADMIN — Réponses (Support, Admin, SuperAdmin)
# ================================================
@admin.register(Reponse)
class ReponseAdmin(AdminThemeMixin, admin.ModelAdmin):
    list_display = ['auteur', 'sujet', 'acceptee', 'date_creation']
    list_filter = ['acceptee']
    search_fields = ['contenu', 'auteur__username']
    readonly_fields = ['date_creation']

    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        try:
            return request.user.profil.role in ['support', 'admin']
        except Exception:
            return False


# ================================================
# ADMIN — Réactions (Support, Admin, SuperAdmin)
# ================================================
@admin.register(Reaction)
class ReactionAdmin(AdminThemeMixin, admin.ModelAdmin):
    list_display = ['utilisateur', 'sujet', 'reponse', 'date_creation']
    readonly_fields = ['date_creation']

    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        try:
            return request.user.profil.role in ['support', 'admin']
        except Exception:
            return False

# ==============================================================
# Articles de blog (Marketing, RespAcademique, Admin, SuperAdmin)
# ==============================================================

@admin.register(Article)
class ArticleAdmin(AdminThemeMixin, SimpleHistoryAdmin):
    list_display = ['titre', 'categorie', 'auteur', 'en_vedette',
                    'badge_publie', 'temps_lecture', 'date_publication', 'bouton_apercu']
    list_filter = ['categorie', 'publie', 'en_vedette', 'formation_liee']
    search_fields = ['titre', 'resume', 'contenu', 'mots_cles']
    list_editable = ['en_vedette']
    prepopulated_fields = {'slug': ('titre',)}
    readonly_fields = ['date_publication', 'date_modification', 'apercu_seo', 'apercu_responsive']

    fieldsets = [
        ('Informations principales', {
            'fields': ['titre', 'slug', 'categorie', 'resume',
                    'temps_lecture', 'formation_liee', 'auteur']
        }),
        ('Contenu', {'fields': ['contenu']}),
        ('👁️ Prévisualisation Responsive', {
            'fields': ['apercu_responsive'],
        }),
        ('🔍 Référencement SEO', {
            'fields': ['meta_titre', 'meta_description', 'mots_cles', 'noindex', 'apercu_seo'],
            'classes': ['collapse'],
        }),
        ('Publication', {
            'fields': ['publie', 'en_vedette', 'date_publication', 'date_modification']
        }),
    ]

    def badge_publie(self, obj):
        from django.utils.html import format_html
        if obj.publie:
            return format_html('<span style="background:#22c55e;color:white;padding:2px 8px;border-radius:10px;font-size:12px;">Publié</span>')
        return format_html('<span style="background:#a0aec0;color:white;padding:2px 8px;border-radius:10px;font-size:12px;">Brouillon</span>')
    badge_publie.short_description = 'Statut'

    def bouton_apercu(self, obj):
        from django.utils.html import format_html
        if obj.id:
            return format_html(
                '<a href="/admin/apercu-article/{}/" target="_blank" '
                'style="background:var(--bta-cyan); color:white; padding:4px 12px; '
                'border-radius:6px; text-decoration:none; font-size:11px; font-weight:700;">'
                '👁️ Aperçu</a>', obj.id
            )
        return "—"
    bouton_apercu.short_description = 'Aperçu'

    def apercu_seo(self, obj):
        from django.utils.html import format_html
        titre = obj.meta_titre or obj.titre
        desc = obj.meta_description or obj.resume[:160]
        return format_html(
            '<div style="border:1px solid #e2e8f0; border-radius:8px; padding:12px; max-width:500px;">'
            '<div style="color:#1a0dab; font-size:16px;">{}</div>'
            '<div style="color:#006621; font-size:12px;">blessytechacademy.com/ressources/{}</div>'
            '<div style="color:#4d5156; font-size:13px;">{}</div></div>',
            titre, obj.slug, desc
        )
    apercu_seo.short_description = "Aperçu Google"

    def apercu_responsive(self, obj):
        from django.utils.html import format_html
        if not obj.id:
            return "Enregistre d'abord l'article pour voir l'aperçu."
        url = f"/admin/apercu-article/{obj.id}/"
        return format_html(
            '''
            <div style="display:flex; gap:8px; margin-bottom:12px;">
                <button type="button" onclick="document.getElementById('apercu-frame').style.width='100%'; document.getElementById('apercu-frame').style.height='500px';"
                        style="padding:6px 14px; border-radius:6px; border:1px solid #e2e8f0; cursor:pointer; background:white;">🖥️ Desktop</button>
                <button type="button" onclick="document.getElementById('apercu-frame').style.width='768px'; document.getElementById('apercu-frame').style.height='500px';"
                        style="padding:6px 14px; border-radius:6px; border:1px solid #e2e8f0; cursor:pointer; background:white;">📱 Tablette</button>
                <button type="button" onclick="document.getElementById('apercu-frame').style.width='375px'; document.getElementById('apercu-frame').style.height='600px';"
                        style="padding:6px 14px; border-radius:6px; border:1px solid #e2e8f0; cursor:pointer; background:white;">📱 Mobile</button>
                <a href="{}" target="_blank" style="padding:6px 14px; border-radius:6px; background:var(--bta-orange); color:white; text-decoration:none; font-size:13px;">Ouvrir en plein écran ↗</a>
            </div>
            <div style="border:1px solid #e2e8f0; border-radius:8px; padding:16px; background:#f8fafc; overflow-x:auto;">
                <iframe id="apercu-frame" src="{}" style="width:100%; height:500px; border:1px solid #ccc; border-radius:8px; background:white; transition:all 0.3s;"></iframe>
            </div>
            ''', url, url
        )
    apercu_responsive.short_description = "Prévisualisation"

    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        try:
            return request.user.profil.role in ['marketing', 'resp_academique', 'admin']
        except Exception:
            return False


@admin.register(OutilRecommande)
class OutilRecommandeAdmin(AdminThemeMixin, admin.ModelAdmin):
    list_display = ['icone', 'nom', 'categorie', 'gratuit',
                    'recommande_par_bta', 'ordre']
    list_filter = ['categorie', 'gratuit', 'recommande_par_bta']
    search_fields = ['nom', 'description']
    list_editable = ['ordre', 'recommande_par_bta']

    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        try:
            return request.user.profil.role in ['marketing', 'resp_academique', 'admin']
        except Exception:
            return False


@admin.register(Temoignage)
class TemoignageAdmin(AdminThemeMixin, admin.ModelAdmin):
    list_display = ['prenom_nom', 'formation_suivie', 'note',
                    'en_vedette', 'approuve', 'date_creation']
    list_filter = ['note', 'en_vedette', 'approuve', 'formation_suivie']
    search_fields = ['prenom_nom', 'texte']
    list_editable = ['en_vedette', 'approuve']

    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        try:
            return request.user.profil.role in ['marketing', 'admin']
        except Exception:
            return False
        
# ================================================
# ADMIN — Plateforme d'examens officiels
# ================================================

class ChoixExamenInline(admin.TabularInline):
    model = ChoixExamen
    extra = 2


class QuestionExamenInline(admin.TabularInline):
    model = QuestionExamen
    extra = 0
    show_change_link = True


# ================================================
# ADMIN — Examens (Examinateur, RespAcademique, Admin, SuperAdmin)
# ================================================
@admin.register(Examen)
class ExamenAdmin(admin.ModelAdmin):
    list_display = ['titre', 'formation', 'duree_minutes', 'seuil_reussite', 'actif']
    list_filter = ['actif', 'formation']
    search_fields = ['titre']
    inlines = [QuestionExamenInline]

    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        try:
            return request.user.profil.role in ['examinateur', 'resp_academique', 'admin']
        except Exception:
            return False


# ================================================
# ADMIN — Questions Examen (Examinateur, RespAcademique, Admin, SuperAdmin)
# ================================================
@admin.register(QuestionExamen)
class QuestionExamenAdmin(admin.ModelAdmin):
    list_display = ['texte_court', 'examen', 'type_question', 'points']
    inlines = [ChoixExamenInline]
    
    def texte_court(self, obj):
        return obj.texte[:80]

    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        try:
            return request.user.profil.role in ['examinateur', 'resp_academique', 'admin']
        except Exception:
            return False


# ================================================
# ADMIN — Tentatives Examen (Examinateur, Correcteur, RespAcademique, Admin, SuperAdmin)
# ================================================
@admin.register(TentativeExamen)
class TentativeExamenAdmin(admin.ModelAdmin):
    list_display = ['utilisateur', 'examen', 'score', 'reussi', 'date_debut']
    list_filter = ['reussi', 'examen']
    readonly_fields = ['date_debut', 'date_fin', 'evenements_suspects']

    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        try:
            return request.user.profil.role in ['examinateur', 'correcteur', 'resp_academique', 'admin']
        except Exception:
            return False
        
# ================================================
# Vue personnalisée — Gestion organisée par École
# ================================================

class GestionCoursAdminSite(AdminThemeMixin):

    def get_urls(self, original_urls):
        custom_urls = [
            path('gestion-cours/', admin.site.admin_view(self.vue_gestion_cours), name='gestion_cours'),
            path('dashboard-editorial/', admin.site.admin_view(self.vue_dashboard_editorial), name='dashboard_editorial'),
            path('dashboard-business/', views.vue_dashboard_business, name='dashboard_business'),            path('synchronisation/', admin.site.admin_view(views.admin_sync_dashboard), name='synchronisation'),
            path('synchronisation/export/', admin.site.admin_view(views.admin_sync_export), name='sync_export'),
            path('synchronisation/import/', admin.site.admin_view(views.admin_sync_import), name='sync_import'),
            path('formation/<int:formation_id>/workspace/', admin.site.admin_view(views.workspace_formation), name='workspace_formation'),
            
            # === Centre d'administration des Emails (apercu + test) ===
            path('emails/', views.admin_emails_dashboard, name='admin_emails'),
            path('emails/preview/<str:template_name>/', views.admin_email_preview, name='email_preview'),
            path('emails/test/', views.admin_email_test, name='email_test'),
            path('dashboard-ia/', views.vue_dashboard_ia, name='dashboard_ia'), 
            # === Export Ventes (Excel / PDF) ===
            path('export/ventes-excel/', views.export_ventes_excel, name='export_ventes_excel'),
            path('export/ventes-pdf/', views.export_ventes_pdf, name='export_ventes_pdf'),
            # ROUTE — Dashboard Business (via views.py)
            path('dashboard-business/', views.vue_dashboard_business, name='dashboard_business'),
            # === CRM ===
            path('dashboard-crm/', views.dashboard_crm, name='dashboard_crm'),
            path('crm/interaction/<int:inscription_id>/', views.ajouter_interaction_crm, name='ajouter_interaction_crm'),
            path('dashboard-executif/', admin.site.admin_view(self.vue_dashboard_executif), name='dashboard_executif'),            ]
        return custom_urls + original_urls

    def vue_gestion_cours(self, request):
        ecoles = Ecole.objects.prefetch_related('formations__modules__lecons').all()
        return render(request, 'admin/gestion_cours.html', {
            'ecoles': ecoles, 'title': 'Gestion des cours par école',
            'site_header': admin.site.site_header,
        })

    def vue_dashboard_editorial(self, request):
        articles_total = Article.objects.count()
        articles_publies = Article.objects.filter(publie=True).count()
        articles_brouillon = articles_total - articles_publies

        formations_sans_programme = Formation.objects.filter(
            actif=True, modules__isnull=True
        ).distinct()

        lecons_sans_contenu = Lecon.objects.filter(
            Q(contenu__isnull=True) | Q(contenu='')
        ).select_related('module__formation')[:15]

        derniers_articles = Article.objects.order_by('-date_publication')[:8]

        return render(request, 'admin/dashboard_editorial.html', {
            'title': '📝 Dashboard Éditorial',
            'site_header': admin.site.site_header,
            'articles_total': articles_total,
            'articles_publies': articles_publies,
            'articles_brouillon': articles_brouillon,
            'formations_sans_programme': formations_sans_programme,
            'lecons_sans_contenu': lecons_sans_contenu,
            'derniers_articles': derniers_articles,
        })

    # ================================================
    # Vue Dashboard Exécutif (agrégation complète)
    # ================================================
    def vue_dashboard_executif(self, request):
        from datetime import timedelta
        from django.db.models import Sum, Count, Avg
        from django.contrib.auth.models import User

        maintenant = timezone.now()
        il_y_a_30j = maintenant - timedelta(days=30)
        il_y_a_60j = maintenant - timedelta(days=60)

        # ---- REVENUS ----
        ca_total = Order.objects.filter(statut='paye').aggregate(t=Sum('total'))['t'] or 0
        ca_30j = Order.objects.filter(statut='paye', date_paiement__gte=il_y_a_30j).aggregate(t=Sum('total'))['t'] or 0
        ca_periode_precedente = Order.objects.filter(
            statut='paye', date_paiement__gte=il_y_a_60j, date_paiement__lt=il_y_a_30j
        ).aggregate(t=Sum('total'))['t'] or 0
        croissance_ca = round(((ca_30j - ca_periode_precedente) / ca_periode_precedente * 100), 1) if ca_periode_precedente else 0

        # ---- ÉTUDIANTS ----
        total_etudiants = User.objects.filter(is_staff=False).count()
        nouveaux_etudiants_30j = User.objects.filter(is_staff=False, date_joined__gte=il_y_a_30j).count()

        # ---- ALERTES ----
        paiements_en_attente = Transaction.objects.filter(statut='en_verification').count()
        formations_en_revision = WorkflowFormation.objects.filter(etat_actuel='en_revision').count()
        leads_non_traites = Inscription.objects.filter(statut_lead='nouveau').count()

        # ---- EXAMENS ----
        tentatives_30j = TentativeExamen.objects.filter(date_debut__gte=il_y_a_30j).count()
        taux_reussite_examens = TentativeExamen.objects.filter(
            date_debut__gte=il_y_a_30j, reussi__isnull=False
        ).aggregate(taux=Avg('reussi'))['taux']
        taux_reussite_examens_pct = round(taux_reussite_examens * 100, 1) if taux_reussite_examens else None

        # ---- ARTICLES / SEO ----
        articles_publies = Article.objects.filter(publie=True).count()
        articles_sans_seo = Article.objects.filter(publie=True, meta_description='').count()

        # ---- PERFORMANCE ----
        formations_actives = Formation.objects.filter(actif=True).count()
        formations_brouillon = WorkflowFormation.objects.filter(etat_actuel='brouillon').count()

        return render(request, 'admin/dashboard_executif.html', {
            'title': '🧠 Dashboard Exécutif',
            'site_header': admin.site.site_header,
            'ca_total': ca_total, 'ca_30j': ca_30j, 'croissance_ca': croissance_ca,
            'total_etudiants': total_etudiants, 'nouveaux_etudiants_30j': nouveaux_etudiants_30j,
            'paiements_en_attente': paiements_en_attente,
            'formations_en_revision': formations_en_revision,
            'leads_non_traites': leads_non_traites,
            'tentatives_30j': tentatives_30j,
            'articles_publies': articles_publies, 'articles_sans_seo': articles_sans_seo,
            'formations_actives': formations_actives, 'formations_brouillon': formations_brouillon,
        })


from django.contrib.auth.models import User

# Injecte les nouvelles URLs dans l'admin
_original_get_urls = admin.site.get_urls
_gestion = GestionCoursAdminSite()

def get_urls_avec_gestion():
    return _gestion.get_urls(_original_get_urls())

admin.site.get_urls = get_urls_avec_gestion

# Personnalisation de l'interface d'administration
admin.site.site_header = "Blessy Tech Academy — Back Office"
admin.site.site_title = "BTA Admin"
admin.site.index_title = "Tableau de bord"


# ================================================
# ADMIN.PY — Payment Center (Finance, Admin, SuperAdmin)
# ================================================
@admin.register(MoyenPaiement)
class MoyenPaiementAdmin(admin.ModelAdmin):
    list_display = ['icone', 'nom_affiche', 'code', 'actif', 'ordre']
    list_editable = ['actif', 'ordre']

    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        try:
            return request.user.profil.role in ['finance', 'admin']
        except Exception:
            return False

    # === RBAC : permissions de modification/suppression ===
    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        try:
            return request.user.profil.role in ['admin']
        except Exception:
            return False

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        try:
            return request.user.profil.role in ['admin']
        except Exception:
            return False


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'type_reduction', 'valeur', 'utilisations_actuelles', 'utilisations_max', 'actif']
    list_editable = ['actif']
    search_fields = ['code']

    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        try:
            return request.user.profil.role in ['finance', 'admin']
        except Exception:
            return False

    # === RBAC : permissions de modification/suppression ===
    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        try:
            return request.user.profil.role in ['admin']
        except Exception:
            return False

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        try:
            return request.user.profil.role in ['admin']
        except Exception:
            return False


@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = ['nom', 'pourcentage_reduction', 'date_debut', 'date_fin', 'actif']
    list_editable = ['actif']
    filter_horizontal = ['ecoles_concernees', 'formations_concernees']

    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        try:
            return request.user.profil.role in ['finance', 'admin']
        except Exception:
            return False

    # === RBAC : permissions de modification/suppression ===
    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        try:
            return request.user.profil.role in ['admin']
        except Exception:
            return False

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        try:
            return request.user.profil.role in ['admin']
        except Exception:
            return False


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
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

    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        try:
            return request.user.profil.role in ['finance', 'admin']
        except Exception:
            return False

    # === RBAC : permissions de modification/suppression ===
    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        try:
            return request.user.profil.role in ['finance', 'admin']
        except Exception:
            return False

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        try:
            return request.user.profil.role in ['admin']
        except Exception:
            return False


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['numero_facture', 'commande', 'date_emission']
    search_fields = ['numero_facture']

    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        try:
            return request.user.profil.role in ['finance', 'admin']
        except Exception:
            return False

    # === RBAC : factures non modifiables ===
    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        try:
            return request.user.profil.role in ['admin']
        except Exception:
            return False


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ['commande', 'montant', 'statut', 'date_demande']
    list_editable = ['statut']

    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        try:
            return request.user.profil.role in ['finance', 'admin']
        except Exception:
            return False

    # === RBAC : permissions de modification/suppression ===
    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        try:
            return request.user.profil.role in ['finance', 'admin']
        except Exception:
            return False

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        try:
            return request.user.profil.role in ['admin']
        except Exception:
            return False


@admin.register(AccesFormationDebloque)
class AccesFormationDebloqueAdmin(admin.ModelAdmin):
    list_display = ['utilisateur', 'nom_formation_snapshot', 'date_deblocage']
    search_fields = ['utilisateur__username', 'nom_formation_snapshot']

    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        try:
            return request.user.profil.role in ['finance', 'admin']
        except Exception:
            return False

    # === RBAC : lecture seule ===
    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        try:
            return request.user.profil.role in ['admin']
        except Exception:
            return False


# ================================================
# ADMIN.PY — Administration abonnements
# ================================================
from .models import PlanAbonnement, Subscription

@admin.register(PlanAbonnement)
class PlanAbonnementAdmin(admin.ModelAdmin):
    list_display = ['nom', 'prix', 'periodicite', 'actif']
    list_editable = ['actif']

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['utilisateur', 'plan_nom_snapshot', 'statut', 'date_prochain_renouvellement']
    list_filter = ['statut']


    # === Réorganisation de l'admin par groupes ===
from django.conf import settings
from django.utils.safestring import mark_safe

original_get_app_list = admin.site.get_app_list

def grouped_app_list(request):
    app_list = original_get_app_list(request)
    grouping = getattr(settings, 'ADMIN_GROUPING', {})
    
    academie_app = None
    for app in app_list:
        if app['app_label'] == 'academie':
            academie_app = app
            break
    
    if academie_app:
        new_models = []
        seen = set()
        
        for group_name, model_names in grouping.items():
            group_models = []
            for model in academie_app['models']:
                model_name = model['object_name']
                if model_name in model_names and model_name not in seen:
                    group_models.append(model)
                    seen.add(model_name)
            if group_models:
                # Ajouter un séparateur de catégorie stylisé
                group_models.insert(0, {
                    'name': mark_safe(
                        f'<div style="background:#407690;color:white;padding:8px 12px;'
                        f'border-radius:6px;margin:8px 0 4px;font-weight:700;font-size:13px;">'
                        f'{group_name}</div>'
                    ),
                    'object_name': None,
                    'admin_url': None,
                    'add_url': None,
                    'perms': {'add': False, 'change': False, 'delete': False, 'view': False},
                })
                new_models.extend(group_models)
        
        academie_app['models'] = new_models
    
    return app_list

admin.site.get_app_list = grouped_app_list


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
    list_display = ['action', 'utilisateur', 'description_courte', 'adresse_ip', 'date_creation']
    list_filter = ['action']
    readonly_fields = ['utilisateur', 'action', 'description', 'objet_type', 'objet_id', 'adresse_ip', 'date_creation']
    search_fields = ['description', 'utilisateur__username']

    def description_courte(self, obj):
        return obj.description[:80]
    description_courte.short_description = 'Description'

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

    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        try:
            return request.user.profil.role in ['admin']
        except Exception:
            return False
        

# ================================================
# ADMIN — Workflow Formation (Admin, SuperAdmin)
# ================================================
@admin.register(WorkflowFormation)
class WorkflowFormationAdmin(admin.ModelAdmin):
    list_display = ['formation', 'etat_actuel', 'score_checklist_affiche', 'demande_par', 'valide_par', 'date_derniere_transition']
    list_filter = ['etat_actuel']
    readonly_fields = ['date_creation', 'date_derniere_transition']

    def score_checklist_affiche(self, obj):
        return f"{obj.score_checklist()}%"
    score_checklist_affiche.short_description = 'Checklist'

    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        try:
            return request.user.profil.role in ['admin']
        except Exception:
            return False