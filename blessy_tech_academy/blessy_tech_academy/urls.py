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

# === API REST v1 ===
router = DefaultRouter()
router.register('formations', FormationViewSet, basename='api-formations')
router.register('articles', ArticleViewSet, basename='api-articles')
router.register('ma-progression', MaProgressionViewSet, basename='api-progression')

urlpatterns += [
    path('api/v1/', include(router.urls)),
    path('api/v1/token/', obtenir_token_api, name='api-token'),
]