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
from rest_framework.permissions import IsAdminUser

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
    PartenaireAPI,
    Formation,
    Parcours,
    ProgressionLecon,
    WorkflowFormation,
)
from .throttles import ThrottlePartenaireAPI
from .api_partenaires import (
    obtenir_partenaire_depuis_request,
    journaliser_requete_partenaire,
    exiger_scope,
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
# Endpoint liste Academies
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
# VUE — PartenaireFormationsView (avec décorateur de scope)
# ================================================

class PartenaireFormationsView(APIView):
    """
    GET /api/v2/partenaire/formations/
    Endpoint réservé aux partenaires API (authentification par clé API).
    Retourne uniquement les formations de l'académie associée au partenaire.
    """

    authentication_classes = [PartenaireAPIAuthentication]
    permission_classes = []
    throttle_classes = [ThrottlePartenaireAPI]

    @exiger_scope('formations.lire')
    def get(self, request):
        partenaire = obtenir_partenaire_depuis_request(request)

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
# VUE — PartenaireEtudiantsFormesView (avec décorateur de scope)
# ================================================

class PartenaireEtudiantsFormesView(APIView):
    """
    GET /api/v2/partenaire/etudiants-formes/?formation_id=...
    Retourne les étudiants certifiés pour une formation donnée,
    uniquement si elle appartient à l'académie du partenaire.
    """

    authentication_classes = [PartenaireAPIAuthentication]
    permission_classes = []
    throttle_classes = [ThrottlePartenaireAPI]

    @exiger_scope('etudiants.lire')
    def get(self, request):
        partenaire = obtenir_partenaire_depuis_request(request)
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


# ================================================
# Endpoint workflow (déjà sécurisé, réutilise transitionner())
# ================================================

@api_view(['POST'])
@permission_classes([IsAdminUser])
def api_workflow_transition(request, formation_id):
    """Transition de workflow via API — sécurisée, réutilise transitionner() du modèle."""
    try:
        formation = Formation.objects.get(id=formation_id)
        workflow, _ = WorkflowFormation.objects.get_or_create(formation=formation)

        nouvel_etat = request.data.get('nouvel_etat')
        commentaire = request.data.get('commentaire', '')

        if not nouvel_etat:
            return Response({'erreur': 'nouvel_etat requis'}, status=400)

        # Vérifie explicitement le rôle (double protection avec IsAdminUser)
        profil = getattr(request.user, 'profil', None)
        if not profil or profil.role not in ['admin', 'formateur']:
            return Response({'erreur': 'Permissions insuffisantes'}, status=403)

        succes, message = workflow.transitionner(nouvel_etat, request.user, commentaire)

        if succes:
            return Response({'succes': True, 'nouvel_etat': workflow.etat_actuel, 'message': message})
        return Response({'succes': False, 'erreur': message}, status=400)

    except Formation.DoesNotExist:
        return Response({'erreur': 'Formation introuvable'}, status=404)