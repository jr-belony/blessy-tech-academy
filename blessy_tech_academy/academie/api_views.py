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