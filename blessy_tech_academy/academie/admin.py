from django.contrib import admin
from .models import (Formation, Inscription, Ecole, Quiz, Question, ResultatQuiz, Module, Lecon )

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
    list_editable = ['actif']
    inlines = [ModuleInline]

    fieldsets = [
        ('Informations principales', {
            'fields': [
                'ecole', 'nom', 'icone', 'description',
                'niveau', 'duree_mois', 'prix', 'actif',
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
    list_display = ['titre', 'formation', 'ordre', 'nombre_lecons']
    list_filter = ['formation']
    search_fields = ['titre']
    inlines = [LeconInline]

    class Media:
        js = ['academie/admin/generer_programme.js', 'academie/admin/generer_contenu_module.js']

@admin.register(Lecon)
class LeconAdmin(admin.ModelAdmin):
    list_display = ['titre', 'module', 'duree_minutes', 'ordre']
    list_filter = ['module__formation']
    search_fields = ['titre', 'contenu']
    class Media:
        js = ['academie/admin/generer_contenu_lecon.js']