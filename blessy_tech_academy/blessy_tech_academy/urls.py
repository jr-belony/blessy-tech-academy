from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from academie import views as views_academie
from rest_framework.routers import DefaultRouter
from academie.api_views import FormationViewSet, ArticleViewSet, MaProgressionViewSet, obtenir_token_api

urlpatterns = [
    path('admin/api/generer-article/', views_academie.api_generer_article, name='api_generer_article'),
    path('admin/synchronisation/', views_academie.admin_sync_dashboard, name='admin_sync_dashboard'),
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('', include('academie.urls')),
    path('ckeditor5/', include('django_ckeditor_5.urls')),
    path('i18n/', include('django.conf.urls.i18n')),
    path('sitemap.xml', views_academie.sitemap_xml, name='sitemap'),
    path('robots.txt', views_academie.robots_txt, name='robots'),
    # === Export Ventes (Excel / PDF) ===
    path('admin/export/ventes-excel/', views_academie.export_ventes_excel, name='export_ventes_excel'),
    path('admin/export/ventes-pdf/', views_academie.export_ventes_pdf, name='export_ventes_pdf'),
]

# Debug Toolbar (développement uniquement)
if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# ================================================
# URLS — API v1 + v2 + Documentation Swagger
# ================================================

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from academie.api_views import ParcoursViewSet, FormationV2ViewSet

# --- v1 (rétrocompatibilité) ---
router_v1 = DefaultRouter()
router_v1.register('formations', FormationViewSet, basename='api-v1-formations')
router_v1.register('articles', ArticleViewSet, basename='api-v1-articles')
router_v1.register('ma-progression', MaProgressionViewSet, basename='api-v1-progression')

# --- v2 enrichie ---
router_v2 = DefaultRouter()
router_v2.register('formations', FormationV2ViewSet, basename='api-v2-formations')
router_v2.register('parcours', ParcoursViewSet, basename='api-v2-parcours')
router_v2.register('articles', ArticleViewSet, basename='api-v2-articles')
router_v2.register('ma-progression', MaProgressionViewSet, basename='api-v2-progression')

urlpatterns += [
    path('api/v1/', include(router_v1.urls)),
    path('api/v1/token/', obtenir_token_api, name='api-token'),

    path('api/v2/', include(router_v2.urls)),
    path('api/v2/token/', obtenir_token_api, name='api-v2-token'),

    # Documentation interactive
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]