from django.urls import path
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import admin
from .models import (Formation, Inscription, Ecole, Quiz, Question, ResultatQuiz, Module, Lecon, ProgressionLecon,
Parcours, Sujet, Reponse, Reaction, )

@admin.register(Ecole)
class EcoleAdmin(admin.ModelAdmin):
    list_display = ['icone', 'nom', 'ordre']
    list_editable = ['ordre']
    search_fields = ['nom']


class ModuleInline(admin.TabularInline):
    model = Module
    extra = 1
    fields = ['ordre', 'titre', 'description']
    show_change_link = True  # permet de cliquer pour gérer les leçons du module
@admin.register(Formation)
class FormationAdmin(admin.ModelAdmin):
    list_display = [
        'icone', 'nom', 'ecole', 'niveau',
        'duree_mois', 'prix', 'actif'
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

    class Media:
        js = ['academie/admin/generer_ia.js', 'academie/admin/generer_programme.js']

@admin.register(Inscription)
class InscriptionAdmin(admin.ModelAdmin):
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
class QuizAdmin(admin.ModelAdmin):
    list_display = ['titre', 'formation', 'nombre_questions', 'actif', 'date_creation']
    list_filter = ['actif', 'formation']
    search_fields = ['titre']
    list_editable = ['actif']
    inlines = [QuestionInline]

    class Media:
        js = ['academie/admin/generer_quiz.js']


@admin.register(ResultatQuiz)
class ResultatQuizAdmin(admin.ModelAdmin):
    list_display = ['utilisateur', 'quiz', 'score', 'total_questions', 'pourcentage', 'date_passage']
    list_filter = ['quiz']
    search_fields = ['utilisateur__username']
    readonly_fields = ['date_passage']

class LeconInline(admin.TabularInline):
    model = Lecon
    extra = 3
    fields = ['ordre', 'titre', 'resume', 'duree_minutes']


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
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
class LeconAdmin(admin.ModelAdmin):
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
class ParcoursAdmin(admin.ModelAdmin):
    list_display = ['icone', 'titre', 'duree_mois', 'prix', 'nombre_formations', 'actif', 'ordre']
    list_filter = ['actif']
    search_fields = ['titre', 'description']
    list_editable = ['actif', 'ordre']
    filter_horizontal = ['formations']  # sélecteur intuitif pour ManyToMany

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
class SujetAdmin(admin.ModelAdmin):
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
class ReponseAdmin(admin.ModelAdmin):
    list_display = ['auteur', 'sujet', 'acceptee', 'date_creation']
    list_filter = ['acceptee']
    search_fields = ['contenu', 'auteur__username']
    readonly_fields = ['date_creation']


@admin.register(Reaction)
class ReactionAdmin(admin.ModelAdmin):
    list_display = ['utilisateur', 'sujet', 'reponse', 'date_creation']
    readonly_fields = ['date_creation']    


    # ================================================
# Vue personnalisée — Gestion organisée par École
# ================================================


class GestionCoursAdminSite:
    """Ajoute une page personnalisée de gestion des cours par école."""

    def get_urls(self, original_urls):
        custom_urls = [
            path('gestion-cours/', admin.site.admin_view(self.vue_gestion_cours),
                name='gestion_cours'),
        ]
        return custom_urls + original_urls

    def vue_gestion_cours(self, request):
        ecoles = Ecole.objects.prefetch_related(
            'formations__modules__lecons'
        ).all()

        return render(request, 'admin/gestion_cours.html', {
            'ecoles': ecoles,
            'title': 'Gestion des cours par école',
            'site_header': admin.site.site_header,
        })


# Injecte les nouvelles URLs dans l'admin
_original_get_urls = admin.site.get_urls
_gestion = GestionCoursAdminSite()

def get_urls_avec_gestion():
    return _gestion.get_urls(_original_get_urls())

admin.site.get_urls = get_urls_avec_gestion