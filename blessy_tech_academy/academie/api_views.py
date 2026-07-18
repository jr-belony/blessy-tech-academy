# ================================================
# API_VIEWS.PY — Endpoints REST de Blessy Tech Academy
# ================================================

from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import authentication, filters, permissions, serializers, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.response import Response
from rest_framework.views import APIView

from .api_serializers import (
    ArticleSerializer,
    FormationDetailSerializer,
    FormationSerializer,
    ParcoursSerializer,
    ProgressionSerializer,
)
from .models import (
    Academie,
    AccesFormationDebloque,
    Article,
    Formation,
    Parcours,
    PartenaireAPI,
    ProgressionLecon,
)

# ================================================
# Endpoints v1 (rétrocompatibles)
# ================================================


class FormationViewSet(viewsets.ReadOnlyModelViewSet):
    """GET /api/v1/formations/ — Liste publique des formations."""

    queryset = Formation.objects.filter(actif=True)
    serializer_class = FormationSerializer
    permission_classes = [permissions.AllowAny]


class ArticleViewSet(viewsets.ReadOnlyModelViewSet):
    """GET /api/v1/articles/ — Knowledge Center public."""

    queryset = Article.objects.filter(publie=True)
    serializer_class = ArticleSerializer
    permission_classes = [permissions.AllowAny]


class MaProgressionViewSet(viewsets.ReadOnlyModelViewSet):
    """GET /api/v1/ma-progression/ — Progression de l'utilisateur authentifié."""

    serializer_class = ProgressionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ProgressionLecon.objects.filter(utilisateur=self.request.user)


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def obtenir_token_api(request):
    """POST /api/v1/token/ — Génère un token d'accès API pour l'utilisateur."""
    token, _ = Token.objects.get_or_create(user=request.user)
    return Response({"token": token.key})


# ================================================
# Endpoints v2 (enrichis, filtrables, documentés)
# ================================================


class ParcoursViewSet(viewsets.ReadOnlyModelViewSet):
    """GET /api/v2/parcours/ — Parcours professionnels avec formations incluses."""

    queryset = Parcours.objects.filter(actif=True).prefetch_related("formations")
    serializer_class = ParcoursSerializer
    permission_classes = [permissions.AllowAny]


class FormationV2ViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/v2/formations/ — Liste filtrable (école, niveau, gratuit, academie)
    GET /api/v2/formations/{id}/ — Détail avec modules complets
    """

    queryset = (
        Formation.objects.filter(actif=True)
        .select_related("ecole", "ecole__academie")
        .prefetch_related("modules")
    )
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["nom", "description"]
    ordering_fields = ["prix", "duree_mois"]
    filterset_fields = ["ecole", "niveau", "gratuit"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return FormationDetailSerializer
        return FormationSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        academie_id = self.request.query_params.get("academie_id")
        if academie_id:
            queryset = queryset.filter(ecole__academie_id=academie_id)
        return queryset

    @extend_schema(
        parameters=[
            OpenApiParameter(name="ecole", type=int, description="Filtrer par ID d'école"),
            OpenApiParameter(
                name="niveau", type=str, description="debutant|intermediaire|avance|professionnel"
            ),
            OpenApiParameter(name="gratuit", type=bool, description="Filtrer formations gratuites"),
            OpenApiParameter(name="academie_id", type=int, description="Filtrer par ID d'académie"),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


# ================================================
# API_VIEWS.PY — Endpoint liste Academies
# ================================================


class AcademieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Academie
        fields = [
            "id",
            "nom",
            "slug",
            "sous_titre",
            "icone",
            "couleur_principale",
            "couleur_accent",
        ]


class AcademieViewSet(viewsets.ReadOnlyModelViewSet):
    """GET /api/v2/academies/ — Liste toutes les académies actives."""

    queryset = Academie.objects.filter(actif=True)
    serializer_class = AcademieSerializer
    permission_classes = [permissions.AllowAny]


# ================================================
# AUTHENTIFICATION — Partenaire API (clé API)
# ================================================


class PartenaireAPIAuthentication(authentication.BaseAuthentication):
    """Authentifie un partenaire via son header X-API-Key."""

    def authenticate(self, request):
        api_key = request.headers.get("X-API-Key")
        if not api_key:
            return None

        try:
            partenaire = PartenaireAPI.objects.get(cle_api=api_key, actif=True)
        except PartenaireAPI.DoesNotExist:
            raise AuthenticationFailed("Clé API invalide ou partenaire inactif.")

        return (partenaire, None)


# ================================================
# FONCTION UTILITAIRE — Journalisation requêtes partenaires
# ================================================


def journaliser_requete_partenaire(request, partenaire, code_http):
    """Log basique des appels partenaires (peut être enrichi avec LogAudit)."""
    print(f"[PARTENAIRE API] {partenaire.nom} - {request.path} - HTTP {code_http}")


# ================================================
# VUE — PartenaireFormationsView (isolation multi-académie)
# ================================================


class PartenaireFormationsView(APIView):
    """
    GET /api/v2/partenaire/formations/
    Endpoint réservé aux partenaires API (authentification par clé API).
    Retourne uniquement les formations de l'académie associée au partenaire.
    """

    authentication_classes = [PartenaireAPIAuthentication]
    permission_classes = []
    throttle_classes = []  # ← Désactive la limite de débit pour les partenaires

    def get(self, request):
        partenaire = request.user

        formations = Formation.objects.filter(actif=True).select_related("ecole", "ecole__academie")

        if partenaire.academie_associee:
            formations = formations.filter(ecole__academie=partenaire.academie_associee)

        data = FormationSerializer(formations, many=True).data
        journaliser_requete_partenaire(request, partenaire, 200)

        return Response(
            {
                "partenaire": partenaire.nom,
                "academie_scope": (
                    partenaire.academie_associee.nom
                    if partenaire.academie_associee
                    else "Toutes académies"
                ),
                "formations": data,
            }
        )


# ================================================
# VUE — PartenaireEtudiantsFormesView (isolation multi-académie)
# ================================================


class PartenaireEtudiantsFormesView(APIView):
    """
    GET /api/v2/partenaire/etudiants-formes/?formation_id=...
    Retourne les étudiants certifiés pour une formation donnée,
    uniquement si elle appartient à l'académie du partenaire.
    """

    authentication_classes = [PartenaireAPIAuthentication]
    permission_classes = []
    throttle_classes = []  # ← Désactive la limite de débit pour les partenaires

    def get(self, request):
        partenaire = request.user
        formation_id = request.query_params.get("formation_id")

        if not formation_id:
            journaliser_requete_partenaire(request, partenaire, 400)
            return Response({"erreur": "formation_id requis"}, status=400)

        if partenaire.academie_associee:
            formation_valide = Formation.objects.filter(
                id=formation_id, ecole__academie=partenaire.academie_associee
            ).exists()
            if not formation_valide:
                journaliser_requete_partenaire(request, partenaire, 403)
                return Response(
                    {"erreur": "Cette formation n'appartient pas à votre académie."}, status=403
                )

        certifies = AccesFormationDebloque.objects.filter(formation_id=formation_id).select_related(
            "utilisateur"
        )

        data = [
            {
                "nom": c.utilisateur.get_full_name() or c.utilisateur.username,
                "date_debloque": c.date_deblocage,
            }
            for c in certifies
        ]
        journaliser_requete_partenaire(request, partenaire, 200)
        return Response({"partenaire": partenaire.nom, "etudiants_certifies": data})
