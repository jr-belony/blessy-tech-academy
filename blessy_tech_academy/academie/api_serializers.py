# ================================================
# API_SERIALIZERS.PY — Sérialisation des données pour l'API BTA
# ================================================
from rest_framework import serializers

from .models import Article, Ecole, Formation, Module, Parcours, ProgressionLecon


class EcoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ecole
        fields = ["id", "nom", "icone", "description"]


class FormationSerializer(serializers.ModelSerializer):
    ecole = EcoleSerializer(read_only=True)
    academie_nom = serializers.CharField(source="ecole.academie.nom", read_only=True, default=None)

    class Meta:
        model = Formation
        fields = [
            "id",
            "nom",
            "icone",
            "description",
            "duree_mois",
            "prix",
            "niveau",
            "gratuit",
            "ecole",
            "academie_nom",
        ]


class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = [
            "id",
            "titre",
            "slug",
            "resume",
            "categorie",
            "type_contenu",
            "date_publication",
            "temps_lecture",
        ]


class ProgressionSerializer(serializers.ModelSerializer):
    lecon_titre = serializers.CharField(source="lecon.titre", read_only=True)

    class Meta:
        model = ProgressionLecon
        fields = ["id", "lecon_titre", "terminee", "date_completion"]


# ================================================
# API_SERIALIZERS.PY — Extensions v2 (Parcours, Ecole détaillée)
# ================================================
class ModuleSerializer(serializers.ModelSerializer):
    nombre_lecons = serializers.SerializerMethodField()

    class Meta:
        model = Module
        fields = ["id", "titre", "description", "ordre", "nombre_lecons"]

    def get_nombre_lecons(self, obj):
        return obj.lecons.count()


class FormationDetailSerializer(serializers.ModelSerializer):
    """Version enrichie avec modules — pour /formations/{id}/detail/"""

    ecole = serializers.StringRelatedField()
    modules = ModuleSerializer(many=True, read_only=True)
    academie_nom = serializers.CharField(source="ecole.academie.nom", read_only=True, default=None)

    class Meta:
        model = Formation
        fields = [
            "id",
            "nom",
            "icone",
            "description",
            "duree_mois",
            "prix",
            "niveau",
            "gratuit",
            "ecole",
            "academie_nom",
            "modules",
            "debouches",
            "prerequis",
        ]


class ParcoursSerializer(serializers.ModelSerializer):
    formations = FormationSerializer(many=True, read_only=True)
    nombre_formations = serializers.SerializerMethodField()

    class Meta:
        model = Parcours
        fields = [
            "id",
            "titre",
            "icone",
            "description",
            "duree_mois",
            "prix",
            "formations",
            "nombre_formations",
        ]

    def get_nombre_formations(self, obj):
        return obj.formations.count()
