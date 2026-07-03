from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from academie import views as views_academie

urlpatterns = [
    path('admin/api/generer-article/', views_academie.api_generer_article, name='api_generer_article'),
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('', include('academie.urls')),
    path('ckeditor5/', include('django_ckeditor_5.urls')),
    path('i18n/', include('django.conf.urls.i18n')),
]

# Debug Toolbar (développement uniquement)
if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)