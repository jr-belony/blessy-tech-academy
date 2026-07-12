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
Invoice, Transaction, Refund, AccesFormationDebloque, ChoixExamen, QuestionExamen, TentativeExamen, Examen)

# ================================================
# Thème CSS global pour tout l'admin
# ================================================
class AdminThemeMixin:
    """Mixin qui injecte le CSS premium dans toutes les pages admin."""
    class Media:
        css = {
            'all': ['academie/admin/theme_premium.css']
        }


@admin.register(Ecole)
class EcoleAdmin(AdminThemeMixin, admin.ModelAdmin):
    list_display = ['icone', 'nom', 'ordre']
    list_editable = ['ordre']
    search_fields = ['nom']

class ModuleInline(SortableInlineAdminMixin, admin.TabularInline):
    model = Module
    extra = 1
    fields = ['ordre', 'titre', 'description']
    show_change_link = True


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

    class Media:
        js = ['academie/admin/generer_ia.js', 'academie/admin/generer_programme.js']
@admin.register(Inscription)
class InscriptionAdmin(AdminThemeMixin, admin.ModelAdmin):
    list_display = [
        'prenom', 'nom', 'email', 'formation',
        'sujet', 'date_inscription', 'traite'
    ]
    list_filter = ['traite', 'formation', 'sujet']
    search_fields = ['prenom', 'nom', 'email']
    list_editable = ['traite']
    readonly_fields = ['date_inscription']


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

    class Media:
        js = ['academie/admin/generer_quiz.js']


@admin.register(ResultatQuiz)
class ResultatQuizAdmin(AdminThemeMixin, admin.ModelAdmin):
    list_display = ['utilisateur', 'quiz', 'score', 'total_questions', 'pourcentage', 'date_passage']
    list_filter = ['quiz']
    search_fields = ['utilisateur__username']
    readonly_fields = ['date_passage']

class LeconInline(SortableInlineAdminMixin, admin.TabularInline):
    model = Lecon
    extra = 3
    fields = ['ordre', 'titre', 'resume', 'duree_minutes']


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

    class Media:
        js = ['academie/admin/generer_programme.js', 'academie/admin/generer_contenu_module.js']

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

    class Media:
        js = ['academie/admin/generer_contenu_lecon.js']


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


class ReponseInline(admin.TabularInline):
    model = Reponse
    extra = 0
    fields = ['auteur', 'contenu', 'acceptee', 'date_creation']
    readonly_fields = ['date_creation']


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


@admin.register(Reponse)
class ReponseAdmin(AdminThemeMixin, admin.ModelAdmin):
    list_display = ['auteur', 'sujet', 'acceptee', 'date_creation']
    list_filter = ['acceptee']
    search_fields = ['contenu', 'auteur__username']
    readonly_fields = ['date_creation']


@admin.register(Reaction)
class ReactionAdmin(AdminThemeMixin, admin.ModelAdmin):
    list_display = ['utilisateur', 'sujet', 'reponse', 'date_creation']
    readonly_fields = ['date_creation']


# ================================================
# Articles de blog
# ================================================

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
@admin.register(OutilRecommande)
class OutilRecommandeAdmin(AdminThemeMixin, admin.ModelAdmin):
    list_display = ['icone', 'nom', 'categorie', 'gratuit',
                    'recommande_par_bta', 'ordre']
    list_filter = ['categorie', 'gratuit', 'recommande_par_bta']
    search_fields = ['nom', 'description']
    list_editable = ['ordre', 'recommande_par_bta']


@admin.register(Temoignage)
class TemoignageAdmin(AdminThemeMixin, admin.ModelAdmin):
    list_display = ['prenom_nom', 'formation_suivie', 'note',
                    'en_vedette', 'approuve', 'date_creation']
    list_filter = ['note', 'en_vedette', 'approuve', 'formation_suivie']
    search_fields = ['prenom_nom', 'texte']
    list_editable = ['en_vedette', 'approuve']


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


@admin.register(Examen)
class ExamenAdmin(admin.ModelAdmin):
    list_display = ['titre', 'formation', 'duree_minutes', 'seuil_reussite', 'actif']
    list_filter = ['actif', 'formation']
    search_fields = ['titre']
    inlines = [QuestionExamenInline]


@admin.register(QuestionExamen)
class QuestionExamenAdmin(admin.ModelAdmin):
    list_display = ['texte_court', 'examen', 'type_question', 'points']
    inlines = [ChoixExamenInline]
    
    def texte_court(self, obj):
        return obj.texte[:80]


@admin.register(TentativeExamen)
class TentativeExamenAdmin(admin.ModelAdmin):
    list_display = ['utilisateur', 'examen', 'score', 'reussi', 'date_debut']
    list_filter = ['reussi', 'examen']
    readonly_fields = ['date_debut', 'date_fin', 'evenements_suspects']


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
            ]
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
# ADMIN.PY — Dashboard IA Admin (Intelligence Décisionnelle)
# Ajoute cette méthode dans GestionCoursAdminSite + route dans get_urls
# ================================================

@staff_member_required
def vue_dashboard_ia(self, request):
    from django.db.models import Count, Avg, Sum

    # Collecte des vraies données de la plateforme
    formations_stats = Formation.objects.filter(actif=True).annotate(
        nb_inscrits=Count('orderitem', filter=Q(orderitem__commande__statut='paye')),
        nb_articles_lies=Count('articles'),
    ).order_by('-nb_inscrits')[:10]

    lecons_abandon = Lecon.objects.annotate(
        nb_vues=Count('progressions'),
        nb_terminees=Count('progressions', filter=Q(progressions__terminee=True)),
    ).filter(nb_vues__gt=0)

    quiz_difficiles = ResultatQuiz.objects.values('quiz__titre').annotate(
        score_moyen=Avg('score'), nb_tentatives=Count('id')
    ).order_by('score_moyen')[:5]

    articles_populaires = Article.objects.filter(publie=True).order_by('-date_publication')[:5]

    contexte_donnees = f"""
Formations les plus vendues : {[(f.nom, f.nb_inscrits) for f in formations_stats[:5]]}
Quiz avec scores les plus bas (difficiles) : {list(quiz_difficiles)}
Nombre total de formations actives : {Formation.objects.filter(actif=True).count()}
Nombre d'étudiants inscrits : {User.objects.filter(is_staff=False).count()}
Chiffre d'affaires : {Order.objects.filter(statut='paye').aggregate(t=Sum('total'))['t'] or 0} $
"""

    analyse_ia = None
    if request.GET.get('lancer_analyse'):
        from academie.ia import analyser_plateforme_ia
        analyse_ia = analyser_plateforme_ia(contexte_donnees)

    return render(request, 'admin/dashboard_ia.html', {
        'title': '🧠 Dashboard IA — Intelligence Décisionnelle',
        'site_header': admin.site.site_header,
        'formations_stats': formations_stats,
        'quiz_difficiles': quiz_difficiles,
        'articles_populaires': articles_populaires,
        'analyse_ia': analyse_ia,
    })


# ================================================
# ADMIN.PY — Payment Center
# ================================================
@admin.register(MoyenPaiement)
class MoyenPaiementAdmin(admin.ModelAdmin):
    list_display = ['icone', 'nom_affiche', 'code', 'actif', 'ordre']
    list_editable = ['actif', 'ordre']


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'type_reduction', 'valeur', 'utilisations_actuelles', 'utilisations_max', 'actif']
    list_editable = ['actif']
    search_fields = ['code']


@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = ['nom', 'pourcentage_reduction', 'date_debut', 'date_fin', 'actif']
    list_editable = ['actif']
    filter_horizontal = ['ecoles_concernees', 'formations_concernees']


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['formation', 'nom_produit_snapshot', 'prix_unitaire']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['reference', 'utilisateur', 'total', 'statut', 'date_creation']
    list_filter = ['statut', 'devise']
    search_fields = ['reference', 'utilisateur__username']
    inlines = [OrderItemInline]
    readonly_fields = ['reference', 'sous_total', 'reduction_totale', 'total']


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


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['numero_facture', 'commande', 'date_emission']
    search_fields = ['numero_facture']


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ['commande', 'montant', 'statut', 'date_demande']
    list_editable = ['statut']


@admin.register(AccesFormationDebloque)
class AccesFormationDebloqueAdmin(admin.ModelAdmin):
    list_display = ['utilisateur', 'nom_formation_snapshot', 'date_deblocage']
    search_fields = ['utilisateur__username', 'nom_formation_snapshot']


# ========================================================================
# ADMIN.PY — Enrichissement vue_dashboard_business avec données Chart.js
# Remplace la méthode existante du même nom
# ========================================================================

@staff_member_required
def vue_dashboard_business(self, request):
    from datetime import timedelta
    import json

    total_inscriptions = Inscription.objects.count()
    inscriptions_non_traitees = Inscription.objects.filter(traite=False).count()

    # Revenus réels (basés sur commandes payées — pas potentiels)
    ca_total = Order.objects.filter(statut='paye').aggregate(total=Sum('total'))['total'] or 0

    # Ventes des 30 derniers jours (pour graphique)
    labels_jours, valeurs_jours = [], []
    for i in range(29, -1, -1):
        jour = timezone.now().date() - timedelta(days=i)
        montant_jour = Order.objects.filter(
            statut='paye', date_paiement__date=jour
        ).aggregate(total=Sum('total'))['total'] or 0
        labels_jours.append(jour.strftime('%d/%m'))
        valeurs_jours.append(float(montant_jour))

    # Top formations vendues
    formations_populaires = Formation.objects.annotate(
        nb_ventes=Count('orderitem', filter=Q(orderitem__commande__statut='paye'))
    ).order_by('-nb_ventes')[:8]

    # Répartition par moyen de paiement
    repartition_moyens = Transaction.objects.filter(statut='reussie').values(
        'moyen_paiement__nom_affiche'
    ).annotate(total=Count('id'))

    coupons_utilises = Coupon.objects.filter(utilisations_actuelles__gt=0).count()
    remboursements_total = Refund.objects.filter(statut='approuve').aggregate(total=Sum('montant'))['total'] or 0

    return render(request, 'admin/dashboard_business.html', {
        'title': '💼 Dashboard Business',
        'site_header': admin.site.site_header,
        'ca_total': ca_total,
        'total_inscriptions': total_inscriptions,
        'inscriptions_non_traitees': inscriptions_non_traitees,
        'formations_populaires': formations_populaires,
        'coupons_utilises': coupons_utilises,
        'remboursements_total': remboursements_total,
        'chart_labels_json': json.dumps(labels_jours),
        'chart_valeurs_json': json.dumps(valeurs_jours),
        'chart_moyens_labels': json.dumps([m['moyen_paiement__nom_affiche'] or 'N/A' for m in repartition_moyens]),
        'chart_moyens_valeurs': json.dumps([m['total'] for m in repartition_moyens]),
    })


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