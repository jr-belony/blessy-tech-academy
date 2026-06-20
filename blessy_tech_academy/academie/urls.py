from django.urls import path
from . import views

urlpatterns = [
    # Pages principales
    path('', views.accueil, name='accueil'),
    path('formations/', views.formations, name='formations'),
    path('apropos/', views.apropos, name='apropos'),
    path('contact/', views.contact, name='contact'),

    # Authentification
    path('inscription/', views.inscription_compte, name='inscription_compte'),
    path('connexion/', views.connexion, name='connexion'),
    path('deconnexion/', views.deconnexion, name='deconnexion'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('recherche/', views.recherche_formations, name='recherche'),

    # Statistiques admin
    path('statistiques/', views.statistiques, name='statistiques'),

    # Intelligence Artificielle
    path('chat/', views.chat_ia, name='chat_ia'),
    path('api/chat/', views.api_chat_ia, name='api_chat_ia'),
    path('recommandations/', views.recommandations_ia, name='recommandations_ia'),
    path('api/generer-formation/', views.api_generer_formation, name='api_generer_formation'),
]