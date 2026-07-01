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
    path('api/generer-quiz/', views.api_generer_quiz, name='api_generer_quiz'),
    path('formation/<int:formation_id>/quiz/', views.liste_quiz, name='liste_quiz'),
    path('formation/<int:formation_id>/', views.detail_formation, name='detail_formation'),
    path('quiz/<int:quiz_id>/', views.passer_quiz, name='passer_quiz'),
    path('api/generer-programme/', views.api_generer_programme, name='api_generer_programme'),
    path('api/generer-contenu-lecon/', views.api_generer_contenu_lecon, name='api_generer_contenu_lecon'),
    path('lecon/<int:lecon_id>/', views.lire_lecon, name='lire_lecon'),
    path('api/generer-contenu-module/', views.api_generer_contenu_module, name='api_generer_contenu_module'),
    path('lecon/<int:lecon_id>/terminer/', views.marquer_lecon_terminee, name='marquer_lecon_terminee'),
    path('formation/<int:formation_id>/certificat/', views.telecharger_certificat, name='telecharger_certificat'),
    
    # Routes API pour le bouton IA (6 fonctionnalités)
    path('api/ia/assistant-code/', views.api_assistant_code, name='api-assistant-code'),
    path('api/ia/generateur-exercices/', views.api_generateur_exercices, name='api-generateur-exercices'),
    path('api/ia/explication-concept/', views.api_explication_concept, name='api-explication-concept'),
    path('api/ia/correction/', views.api_correction_automatique, name='api-correction'),
    path('api/ia/parcours-adaptatif/', views.api_parcours_adaptatif, name='api-parcours-adaptatif'),
    path('api/ia/chatbot/', views.api_chatbot_tuteur, name='api-chatbot'),
    
    # Simulateur de carrière
    path('simulateur-carriere/', views.simulateur_carriere, name='simulateur_carriere'),
    path('api/ia/simuler-carriere/', views.api_simuler_carriere, name='api-simuler-carriere'),
    
    # Espace recrutement / Portfolio
    path('recrutement/', views.espace_recrutement, name='espace_recrutement'),
    path('mon-portfolio/', views.mon_portfolio, name='mon_portfolio'),
    
    # Forum Communautaire
    path('forum/', views.forum_liste, name='forum_liste'),
    path('forum/nouveau/', views.forum_creer, name='forum_creer'),
    path('forum/<int:sujet_id>/', views.forum_detail, name='forum_detail'),
    path('forum/liker/<str:type_cible>/<int:cible_id>/', views.forum_liker, name='forum_liker'),
    path('forum/accepter/<int:reponse_id>/', views.forum_accepter_reponse, name='forum_accepter_reponse'),
    path('orientation/', views.orientation_ia, name='orientation_ia'),
    path('forum/membres/', views.forum_membres, name='forum_membres'),

    path('certificat/<str:numero>/', views.verifier_certificat, name='verifier_certificat'),
]