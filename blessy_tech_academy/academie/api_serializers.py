# ================================================
# API_SERIALIZERS.PY — Sérialisation des données pour l'API BTA
# ================================================

from rest_framework import serializers
from .models import Formation, Ecole, Article, ProgressionLecon


class EcoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ecole
        fields = ['id', 'nom', 'icone', 'description']


class FormationSerializer(serializers.ModelSerializer):
    ecole = EcoleSerializer(read_only=True)
    class Meta:
        model = Formation
        fields = ['id', 'nom', 'icone', 'description', 'duree_mois', 'prix', 'niveau', 'gratuit', 'ecole']


class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = ['id', 'titre', 'slug', 'resume', 'categorie', 'type_contenu', 'date_publication', 'temps_lecture']


class ProgressionSerializer(serializers.ModelSerializer):
    lecon_titre = serializers.CharField(source='lecon.titre', read_only=True)
    class Meta:
        model = ProgressionLecon
        fields = ['id', 'lecon_titre', 'terminee', 'date_completion']