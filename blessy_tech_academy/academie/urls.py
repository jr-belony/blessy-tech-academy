from django.urls import path
from . import views

urlpatterns = [
    path('', views.accueil, name='accueil'),
    path('formations/', views.formations, name='formations'),
    path('apropos/', views.apropos, name='apropos'),
    path('contact/', views.contact, name='contact'),
]