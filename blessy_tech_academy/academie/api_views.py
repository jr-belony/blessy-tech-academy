# ================================================
# API_VIEWS.PY — Endpoints REST de Blessy Tech Academy
# ================================================

from rest_framework import viewsets, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token

from .models import Formation, Article, ProgressionLecon
from .api_serializers import FormationSerializer, ArticleSerializer, ProgressionSerializer


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


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def obtenir_token_api(request):
    """POST /api/v1/token/ — Génère un token d'accès API pour l'utilisateur."""
    token, _ = Token.objects.get_or_create(user=request.user)
    return Response({'token': token.key})


# ================================================
# API_VIEWS.PY — Endpoints v2 (Parcours, filtres avancés, throttling custom)
# ================================================

from rest_framework import filters
from drf_spectacular.utils import extend_schema, OpenApiParameter
from .models import Parcours
from .api_serializers import ParcoursSerializer, FormationDetailSerializer


class ParcoursViewSet(viewsets.ReadOnlyModelViewSet):
    """GET /api/v2/parcours/ — Parcours professionnels avec formations incluses."""
    queryset = Parcours.objects.filter(actif=True).prefetch_related('formations')
    serializer_class = ParcoursSerializer
    permission_classes = [permissions.AllowAny]


class FormationV2ViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/v2/formations/ — Liste filtrable (école, niveau, gratuit)
    GET /api/v2/formations/{id}/ — Détail avec modules complets
    """
    queryset = Formation.objects.filter(actif=True).select_related('ecole').prefetch_related('modules')
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nom', 'description']
    ordering_fields = ['prix', 'duree_mois']
    filterset_fields = ['ecole', 'niveau', 'gratuit']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return FormationDetailSerializer
        return FormationSerializer

    @extend_schema(
        parameters=[
            OpenApiParameter(name='ecole', type=int, description="Filtrer par ID d'école"),
            OpenApiParameter(name='niveau', type=str, description="debutant|intermediaire|avance|professionnel"),
            OpenApiParameter(name='gratuit', type=bool, description="Filtrer formations gratuites"),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)