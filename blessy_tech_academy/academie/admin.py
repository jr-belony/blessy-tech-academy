from django.contrib import admin
from .models import Formation, Inscription


@admin.register(Formation)
class FormationAdmin(admin.ModelAdmin):
    list_display = [
        'icone',
        'nom',
        'niveau',
        'duree_mois',
        'prix',
        'actif'
    ]
    list_filter = ['actif', 'niveau']
    search_fields = ['nom', 'description']
    list_editable = ['actif']

    fieldsets = [
        ('Informations principales', {
            'fields': [
                'nom', 'icone', 'description',
                'niveau', 'duree_mois', 'prix', 'actif',
            ]
        }),
        ('Contenu détaillé', {
            'fields': [
                'debouches', 'prerequis', 'certifications',
            ],
            'classes': ['collapse'],
        }),
    ]


@admin.register(Inscription)
class InscriptionAdmin(admin.ModelAdmin):
    list_display = [
        'prenom', 'nom', 'email',
        'formation', 'sujet',
        'date_inscription', 'traite'
    ]
    list_filter = ['traite', 'formation', 'sujet']
    search_fields = ['prenom', 'nom', 'email']
    list_editable = ['traite']
    readonly_fields = ['date_inscription']

    fieldsets = [
        ('Informations personnelles', {
            'fields': ['prenom', 'nom', 'email', 'telephone']
        }),
        ('Demande', {
            'fields': ['formation', 'sujet', 'message']
        }),
        ('Statut', {
            'fields': ['traite', 'date_inscription']
        }),
    ]