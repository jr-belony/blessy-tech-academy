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

    # Statistiques admin
    path('statistiques/', views.statistiques, name='statistiques'),
]