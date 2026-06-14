from django.contrib import admin
from .models import Formation, Inscription


@admin.register(Formation)
class FormationAdmin(admin.ModelAdmin):
    list_display = ['nom', 'duree_mois', 'prix', 'actif']
    list_filter = ['actif']
    search_fields = ['nom', 'description']
    list_editable = ['actif', 'prix']


@admin.register(Inscription)
class InscriptionAdmin(admin.ModelAdmin):
    list_display = ['prenom', 'nom', 'email', 'formation', 'date_inscription', 'traite']
    list_filter = ['traite', 'formation']
    search_fields = ['prenom', 'nom', 'email']
    list_editable = ['traite']
    readonly_fields = ['date_inscription']