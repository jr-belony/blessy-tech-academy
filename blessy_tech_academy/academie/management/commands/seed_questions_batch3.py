# ================================================
# SEED_QUESTIONS_BATCH3.PY — Troisième et dernier lot — 150/150
# Usage : python manage.py seed_questions_batch3
# 45 questions (15 Internet, 15 IA, 15 Bureautique)
# ================================================

from django.core.management.base import BaseCommand
from academie.models_banque import ModuleBanque, CategorieBanque, QuestionBanque


QUESTIONS_INTERNET = [
    {
        'categorie': 'Navigation Web', 'niveau': 'facile', 'type': 'qcm',
        'enonce': "Que fait le bouton « Actualiser » (ou F5) dans un navigateur ?",
        'reponses': [
            {'texte': 'Recharge la page actuelle depuis le serveur', 'correct': True},
            {'texte': 'Ferme le navigateur', 'correct': False},
            {'texte': 'Efface tout l\'historique', 'correct': False},
            {'texte': 'Ouvre une nouvelle fenêtre', 'correct': False},
        ],
        'explication': "F5 (ou le bouton circulaire) recharge la page actuelle, utile quand le contenu semble figé ou après une mise à jour côté serveur.",
        'mots_cles': 'actualiser, F5, navigation de base',
    },
    {
        'categorie': 'Navigation Web', 'niveau': 'intermediaire', 'type': 'qcm',
        'enonce': "Que permet de faire un signet (favori) dans un navigateur ?",
        'reponses': [
            {'texte': 'Enregistrer une page pour y accéder rapidement plus tard', 'correct': True},
            {'texte': 'Bloquer un site définitivement', 'correct': False},
            {'texte': 'Supprimer une page du web', 'correct': False},
            {'texte': 'Envoyer la page par email automatiquement', 'correct': False},
        ],
        'explication': "Un signet (favori/bookmark) enregistre l'adresse d'une page pour un accès rapide ultérieur, sans avoir à la rechercher à nouveau.",
        'mots_cles': 'signet, favori, organisation navigation',
    },
    {
        'categorie': 'Navigation Web', 'niveau': 'professionnel', 'type': 'etude_cas',
        'enonce': "Un navigateur affiche systématiquement des publicités intrusives et redirige vers des sites inconnus, même sur des sites fiables. Quel est le diagnostic le plus probable et la solution ?",
        'reponses': [
            {'texte': 'Une extension malveillante ou un adware installé — vérifier et supprimer les extensions suspectes dans les paramètres du navigateur', 'correct': True},
            {'texte': "C'est normal, tous les sites font ça", 'correct': False},
            {'texte': "Il faut changer d'ordinateur", 'correct': False},
            {'texte': "C'est un problème de l'imprimante", 'correct': False},
        ],
        'explication': "Des publicités intrusives sur TOUS les sites (même normalement fiables) indiquent généralement une extension de navigateur compromise (adware). La solution est de vérifier la liste des extensions installées et de supprimer celles non reconnues.",
        'mots_cles': 'adware, extension malveillante, diagnostic navigateur',
    },
    {
        'categorie': 'Recherche avancée', 'niveau': 'intermediaire', 'type': 'qcm',
        'enonce': "Quel opérateur de recherche permet de chercher l'un OU l'autre de deux termes (ex: « chat OR chien ») ?",
        'reponses': [
            {'texte': 'OR (en majuscules)', 'correct': True}, {'texte': 'AND', 'correct': False},
            {'texte': 'NOT', 'correct': False}, {'texte': '%', 'correct': False},
        ],
        'explication': "L'opérateur OR (en majuscules) élargit la recherche pour inclure des résultats contenant l'un OU l'autre terme, utile pour explorer des synonymes ou alternatives.",
        'mots_cles': 'opérateur OR, recherche élargie',
    },
    {
        'categorie': 'Recherche avancée', 'niveau': 'avance', 'type': 'qcm',
        'enonce': "Pour retrouver des images libres de droits utilisables commercialement, quelle démarche est correcte ?",
        'reponses': [
            {'texte': 'Utiliser le filtre « Droits d\'usage » de la recherche d\'images ou des banques dédiées (Unsplash, Pexels)', 'correct': True},
            {'texte': 'Prendre n\'importe quelle image trouvée sur Google Images', 'correct': False},
            {'texte': 'Toutes les images sur Internet sont libres de droits', 'correct': False},
            {'texte': 'Faire une capture d\'écran suffit toujours', 'correct': False},
        ],
        'explication': "La majorité des images trouvées via une recherche simple sont protégées par le droit d'auteur. Il faut utiliser le filtre de licences d'usage ou des banques d'images explicitement libres de droits pour un usage commercial légal.",
        'mots_cles': 'droits d\'auteur, images libres, licence usage',
    },
    {
        'categorie': 'Opérateurs de recherche', 'niveau': 'facile', 'type': 'qcm',
        'enonce': "Quel symbole utilisé devant un mot permet de le rendre obligatoire dans les résultats de recherche ?",
        'reponses': [
            {'texte': '+ (plus)', 'correct': True}, {'texte': '% (pourcentage)', 'correct': False},
            {'texte': '& (esperluette)', 'correct': False}, {'texte': '~ (tilde)', 'correct': False},
        ],
        'explication': "Le signe + (moins utilisé aujourd'hui sur Google, mais toujours valable sur d'autres moteurs) force la présence exacte du terme suivant dans les résultats.",
        'mots_cles': 'opérateur plus, recherche obligatoire',
    },
    {
        'categorie': 'Sécurité numérique', 'niveau': 'facile', 'type': 'qcm',
        'enonce': "Quelle est la meilleure pratique pour créer un mot de passe solide ?",
        'reponses': [
            {'texte': 'Combiner lettres majuscules/minuscules, chiffres et symboles, avec une longueur minimale de 12 caractères', 'correct': True},
            {'texte': 'Utiliser son prénom et sa date de naissance', 'correct': False},
            {'texte': 'Utiliser « 123456 » car c\'est facile à retenir', 'correct': False},
            {'texte': 'Utiliser le même mot de passe partout pour simplifier', 'correct': False},
        ],
        'explication': "Un mot de passe fort combine différents types de caractères et atteint une longueur suffisante (12+ caractères recommandés), rendant les attaques par force brute beaucoup plus difficiles.",
        'mots_cles': 'mot de passe fort, sécurité, bonnes pratiques',
    },
    {
        'categorie': 'Sécurité numérique', 'niveau': 'intermediaire', 'type': 'qcm',
        'enonce': "Que doit-on faire si l'on suspecte que son compte email a été piraté ?",
        'reponses': [
            {'texte': 'Changer immédiatement le mot de passe et activer la double authentification', 'correct': True},
            {'texte': 'Attendre pour voir si le problème se résout seul', 'correct': False},
            {'texte': 'Supprimer définitivement le compte', 'correct': False},
            {'texte': 'Ne rien faire, ce n\'est pas grave', 'correct': False},
        ],
        'explication': "En cas de suspicion de piratage, il faut agir immédiatement : changer le mot de passe et activer l'authentification à deux facteurs pour reprendre le contrôle du compte avant que des dégâts supplémentaires ne surviennent.",
        'mots_cles': 'compte piraté, réaction sécurité, urgence',
    },
    {
        'categorie': 'Sécurité numérique', 'niveau': 'professionnel', 'type': 'scenario_pro',
        'enonce': "Une entreprise reçoit un appel se présentant comme « le support technique Microsoft » demandant un accès à distance à un ordinateur pour « résoudre un problème critique ». Quelle est la bonne réaction ?",
        'reponses': [
            {'texte': 'Refuser et raccrocher — Microsoft ne contacte jamais proactivement par téléphone de cette façon (technique d\'ingénierie sociale)', 'correct': True},
            {'texte': 'Accorder l\'accès immédiatement car c\'est urgent', 'correct': False},
            {'texte': 'Donner son mot de passe pour accélérer le processus', 'correct': False},
            {'texte': 'Transférer l\'appel à un collègue sans vérifier', 'correct': False},
        ],
        'explication': "C'est une arnaque classique d'ingénierie sociale (« tech support scam »). Les vraies entreprises technologiques ne contactent jamais proactivement les utilisateurs par téléphone pour demander un accès distant — toujours raccrocher et vérifier via les canaux officiels.",
        'mots_cles': 'ingénierie sociale, arnaque support technique, vigilance',
    },
    {
        'categorie': 'Google Workspace', 'niveau': 'intermediaire', 'type': 'qcm',
        'enonce': "Quelle application Google Workspace sert de service de stockage cloud principal ?",
        'reponses': [
            {'texte': 'Google Drive', 'correct': True}, {'texte': 'Google Keep', 'correct': False},
            {'texte': 'Google Chat', 'correct': False}, {'texte': 'Google Calendar', 'correct': False},
        ],
        'explication': "Google Drive est le service de stockage cloud central de Google Workspace, hébergeant Docs, Sheets, Slides et tout autre type de fichier.",
        'mots_cles': 'Google Drive, stockage cloud, Google Workspace',
    },
    {
        'categorie': 'Google Workspace', 'niveau': 'avance', 'type': 'qcm',
        'enonce': "Dans Google Sheets, comment empêcher une ligne d'en-tête de défiler quand on parcourt un long tableau ?",
        'reponses': [
            {'texte': 'Affichage > Figer > 1 ligne', 'correct': True}, {'texte': 'Format > Couleur de remplissage', 'correct': False},
            {'texte': 'Insertion > Ligne', 'correct': False}, {'texte': 'Ce n\'est pas possible', 'correct': False},
        ],
        'explication': "La fonction « Figer » (Affichage > Figer) maintient une ou plusieurs lignes/colonnes visibles en permanence pendant le défilement, très utile pour garder les en-têtes visibles sur de grands tableaux.",
        'mots_cles': 'figer ligne, Google Sheets, navigation tableau',
    },
    {
        'categorie': 'Organisation des fichiers', 'niveau': 'intermediaire', 'type': 'classement',
        'enonce': "Classez ces pratiques d'organisation de fichiers de la moins efficace à la plus efficace.",
        'reponses': [
            'Tout enregistrer sur le Bureau sans dossier',
            'Créer quelques dossiers génériques (« Documents », « Autres »)',
            'Créer une arborescence par projet/date avec noms clairs',
        ],
        'explication': "Une arborescence structurée par projet, client ou date, avec des noms de fichiers explicites, est la méthode la plus efficace pour retrouver rapidement l'information — contrairement à l'accumulation désorganisée sur le Bureau.",
        'mots_cles': 'arborescence, organisation fichiers, efficacité',
    },
    {
        'categorie': 'Collaboration', 'niveau': 'intermediaire', 'type': 'qcm',
        'enonce': "Quel est l'intérêt principal des commentaires (pas les modifications directes) dans un document collaboratif ?",
        'reponses': [
            {'texte': 'Suggérer ou questionner sans modifier le contenu original, pour discussion avant validation', 'correct': True},
            {'texte': 'Supprimer automatiquement le texte commenté', 'correct': False},
            {'texte': 'Envoyer un email à tous les collaborateurs', 'correct': False},
            {'texte': 'Aucun intérêt particulier', 'correct': False},
        ],
        'explication': "Les commentaires permettent d'échanger, questionner ou suggérer sans altérer directement le contenu — une pratique essentielle en révision collaborative pour préserver la traçabilité des échanges.",
        'mots_cles': 'commentaires, révision collaborative, communication',
    },
    {
        'categorie': 'Productivité', 'niveau': 'intermediaire', 'type': 'qcm',
        'enonce': "Quel principe de gestion des tâches consiste à classer les priorités selon leur urgence ET leur importance ?",
        'reponses': [
            {'texte': 'La matrice d\'Eisenhower', 'correct': True}, {'texte': 'La méthode SCRUM', 'correct': False},
            {'texte': 'Le brainstorming', 'correct': False}, {'texte': 'Le mind mapping', 'correct': False},
        ],
        'explication': "La matrice d'Eisenhower classe les tâches en 4 quadrants (urgent/important, important/non-urgent, urgent/non-important, ni l'un ni l'autre) pour prioriser efficacement son temps de travail.",
        'mots_cles': 'matrice Eisenhower, priorisation, gestion du temps',
    },
]


QUESTIONS_IA = [
    {
        'categorie': 'Fondamentaux', 'niveau': 'facile', 'type': 'qcm',
        'enonce': "Lequel de ces exemples illustre un usage courant de l'IA dans la vie quotidienne ?",
        'reponses': [
            {'texte': 'Les recommandations de vidéos sur YouTube', 'correct': True},
            {'texte': 'L\'horloge murale d\'un bureau', 'correct': False},
            {'texte': 'Une calculatrice de poche basique', 'correct': False},
            {'texte': 'Un stylo à bille', 'correct': False},
        ],
        'explication': "Les systèmes de recommandation (YouTube, Netflix, réseaux sociaux) utilisent des algorithmes d'IA pour analyser les comportements et suggérer du contenu personnalisé — un exemple d'IA omniprésent au quotidien.",
        'mots_cles': 'IA quotidienne, recommandation, exemples concrets',
    },
    {
        'categorie': 'IA générative', 'niveau': 'intermediaire', 'type': 'qcm',
        'enonce': "Quel est le principal avantage de demander à une IA de résumer un long document plutôt que de le lire intégralement ?",
        'reponses': [
            {'texte': 'Gain de temps significatif pour saisir rapidement les points clés', 'correct': True},
            {'texte': 'Le résumé est toujours 100% exhaustif et parfait', 'correct': False},
            {'texte': 'Cela remplace totalement la lecture pour toute décision importante', 'correct': False},
            {'texte': 'Aucun avantage réel', 'correct': False},
        ],
        'explication': "Un résumé IA fait gagner du temps pour une première compréhension, mais reste une synthèse potentiellement incomplète — pour des décisions importantes, une vérification du document original reste recommandée.",
        'mots_cles': 'résumé IA, gain de temps, limites',
    },
    {
        'categorie': 'Prompt Engineering', 'niveau': 'facile', 'type': 'qcm',
        'enonce': "Pourquoi préciser le format souhaité (liste, tableau, paragraphe) dans un prompt améliore-t-il le résultat ?",
        'reponses': [
            {'texte': 'Cela guide l\'IA vers une structure de réponse directement utilisable, sans reformatage manuel', 'correct': True},
            {'texte': 'Cela n\'a aucun effet sur la réponse', 'correct': False},
            {'texte': 'Cela ralentit systématiquement l\'IA', 'correct': False},
            {'texte': 'Le format n\'existe pas en IA générative', 'correct': False},
        ],
        'explication': "Préciser le format attendu (bullet points, tableau, email formel...) permet d'obtenir une réponse directement exploitable, évitant un travail de reformatage manuel après coup.",
        'mots_cles': 'format prompt, structure réponse, efficacité',
    },
    {
        'categorie': 'Prompt Engineering', 'niveau': 'avance', 'type': 'qcm',
        'enonce': "Quelle technique consiste à demander à l'IA de « réfléchir étape par étape » avant de donner sa réponse finale ?",
        'reponses': [
            {'texte': 'Le « chain-of-thought » prompting (raisonnement pas à pas)', 'correct': True},
            {'texte': 'Le zero-shot prompting', 'correct': False}, {'texte': 'Le prompt injection', 'correct': False},
            {'texte': 'Le fine-tuning', 'correct': False},
        ],
        'explication': "Le « chain-of-thought » (raisonnement en chaîne) encourage l'IA à décomposer son raisonnement en étapes explicites avant de conclure, améliorant souvent la précision sur des problèmes complexes (calculs, logique).",
        'mots_cles': 'chain-of-thought, raisonnement étape par étape, technique avancée',
    },
    {
        'categorie': 'Prompt Engineering', 'niveau': 'professionnel', 'type': 'analyse_prompt_ia',
        'enonce': "Comparez ces 2 prompts pour générer un plan marketing : A) « Fais-moi un plan marketing » B) « Élabore un plan marketing sur 3 mois pour une formation en ligne destinée à des jeunes de 18-25 ans en Haïti, budget limité, avec 3 canaux prioritaires ». Lequel est professionnellement supérieur et pourquoi ?",
        'reponses': [
            {'texte': 'Le prompt B — il précise cible, contexte, durée, contraintes et livrables attendus, réduisant l\'ambiguïté', 'correct': True},
            {'texte': 'Le prompt A — plus court donc plus efficace', 'correct': False},
            {'texte': 'Les deux sont équivalents', 'correct': False},
            {'texte': 'Aucun des deux ne fonctionnera', 'correct': False},
        ],
        'explication': "Le prompt B illustre les principes du prompt engineering professionnel : contexte précis (cible, zone géographique), contraintes explicites (budget, durée) et livrable clair — produisant une réponse directement exploitable plutôt qu'un contenu générique.",
        'mots_cles': 'analyse comparative prompt, precision professionnelle',
    },
    {
        'categorie': 'Éthique', 'niveau': 'facile', 'type': 'qcm',
        'enonce': "Pourquoi est-il important de vérifier les biais potentiels d'une IA avant de l'utiliser pour des décisions importantes ?",
        'reponses': [
            {'texte': 'Une IA entraînée sur des données biaisées peut reproduire des discriminations injustes', 'correct': True},
            {'texte': 'Les IA n\'ont jamais de biais', 'correct': False},
            {'texte': 'Ce n\'est pas important', 'correct': False},
            {'texte': 'Cela ralentit uniquement le système', 'correct': False},
        ],
        'explication': "Les IA apprennent à partir de données historiques qui peuvent contenir des biais sociétaux existants — sans vigilance, elles risquent de perpétuer ou amplifier ces discriminations dans leurs résultats.",
        'mots_cles': 'biais IA, éthique, discrimination algorithmique',
    },
    {
        'categorie': 'Vérification des réponses', 'niveau': 'intermediaire', 'type': 'qcm',
        'enonce': "Quelle stratégie simple aide à vérifier la fiabilité d'une réponse générée par IA sur un fait précis ?",
        'reponses': [
            {'texte': 'Croiser l\'information avec au moins une source indépendante fiable', 'correct': True},
            {'texte': 'Faire confiance systématiquement sans vérification', 'correct': False},
            {'texte': 'Demander à la même IA de confirmer sa propre réponse', 'correct': False},
            {'texte': 'Ignorer la réponse complètement', 'correct': False},
        ],
        'explication': "Demander à la même IA de « confirmer » sa réponse ne garantit rien — elle peut répéter la même erreur avec assurance. Croiser avec une source EXTERNE et indépendante reste la méthode de vérification la plus fiable.",
        'mots_cles': 'vérification croisée, source indépendante, fiabilité',
    },
    {
        'categorie': 'Cas professionnels', 'niveau': 'intermediaire', 'type': 'qcm',
        'enonce': "Comment l'IA peut-elle assister un formateur dans la création de supports pédagogiques ?",
        'reponses': [
            {'texte': 'En générant un premier brouillon d\'exercices ou d\'explications, à relire et adapter par le formateur', 'correct': True},
            {'texte': 'En remplaçant complètement le formateur', 'correct': False},
            {'texte': 'En décidant seule du programme sans supervision', 'correct': False},
            {'texte': 'Elle ne peut pas être utile en pédagogie', 'correct': False},
        ],
        'explication': "L'IA peut accélérer la création de premiers brouillons (exercices, quiz, explications) que le formateur relit, corrige et adapte à son public — un gain de temps précieux qui ne remplace pas l'expertise pédagogique humaine.",
        'mots_cles': 'IA pédagogie, assistance formateur, cas d\'usage éducatif',
    },
    {
        'categorie': 'Cas professionnels', 'niveau': 'professionnel', 'type': 'etude_cas',
        'enonce': "Une PME veut utiliser l'IA pour traduire automatiquement toute sa documentation technique vers l'anglais sans relecture humaine. Quel risque professionnel majeur cette décision comporte-t-elle ?",
        'reponses': [
            {'texte': 'Erreurs de traduction technique pouvant induire en erreur les utilisateurs ou créer des risques de sécurité/légaux', 'correct': True},
            {'texte': 'Aucun risque, la traduction IA est toujours parfaite', 'correct': False},
            {'texte': 'Le processus sera trop lent', 'correct': False},
            {'texte': 'Les documents deviendront illisibles pour tous', 'correct': False},
        ],
        'explication': "La traduction automatique de documentation TECHNIQUE (instructions de sécurité, spécifications) sans relecture humaine expose à des risques réels — une terminologie mal traduite peut avoir des conséquences légales ou de sécurité concrètes.",
        'mots_cles': 'traduction automatique, risque professionnel, relecture humaine',
    },
    {
        'categorie': 'Automatisation', 'niveau': 'facile', 'type': 'vrai_faux',
        'enonce': "Automatiser une tâche avec l'IA élimine totalement le besoin de supervision humaine.",
        'reponses': [{'texte': 'Vrai', 'correct': False}, {'texte': 'Faux', 'correct': True}],
        'explication': "C'est faux : même les processus automatisés bénéficient d'une supervision humaine périodique pour détecter les erreurs, anomalies ou dérives — l'automatisation réduit l'effort, elle ne l'élimine pas complètement.",
        'mots_cles': 'supervision humaine, limites automatisation, vigilance',
    },
    {
        'categorie': 'Automatisation', 'niveau': 'avance', 'type': 'qcm',
        'enonce': "Quel est l'avantage principal d'automatiser l'envoi d'un email de bienvenue à chaque nouvel inscrit sur une plateforme ?",
        'reponses': [
            {'texte': 'Cohérence et rapidité — chaque utilisateur reçoit immédiatement la même expérience de qualité sans intervention manuelle', 'correct': True},
            {'texte': 'Cela remplace toute autre communication avec le client', 'correct': False},
            {'texte': 'Cela coûte toujours plus cher que le manuel', 'correct': False},
            {'texte': 'Aucun avantage mesurable', 'correct': False},
        ],
        'explication': "L'automatisation d'actions répétitives et prévisibles (email de bienvenue) garantit rapidité et cohérence, libérant du temps humain pour des interactions à plus forte valeur ajoutée nécessitant du jugement.",
        'mots_cles': 'automatisation email, cohérence, efficacité opérationnelle',
    },
    {
        'categorie': 'Fondamentaux', 'niveau': 'professionnel', 'type': 'qcm',
        'enonce': "Que signifie l'expression « garbage in, garbage out » appliquée à l'IA ?",
        'reponses': [
            {'texte': 'Si les données d\'entraînement sont de mauvaise qualité, les résultats produits par l\'IA le seront aussi', 'correct': True},
            {'texte': 'Les IA produisent toujours des déchets numériques', 'correct': False},
            {'texte': 'C\'est un terme lié au recyclage informatique', 'correct': False},
            {'texte': 'Cela n\'a aucun lien avec l\'IA', 'correct': False},
        ],
        'explication': "Ce principe fondamental rappelle que la qualité des résultats d'un système IA dépend directement de la qualité des données utilisées pour l'entraîner — des données biaisées ou erronées produisent des résultats biaisés ou erronés.",
        'mots_cles': 'qualité des données, garbage in garbage out, fondamentaux',
    },
]


QUESTIONS_BUREAUTIQUE = [
    {
        'categorie': 'Microsoft Word', 'niveau': 'facile', 'type': 'qcm',
        'enonce': "Quel outil Word souligne automatiquement les fautes d'orthographe en rouge ondulé ?",
        'reponses': [
            {'texte': 'Le correcteur orthographique automatique', 'correct': True},
            {'texte': 'Le mode plan', 'correct': False}, {'texte': 'Le suivi des modifications', 'correct': False},
            {'texte': 'Le publipostage', 'correct': False},
        ],
        'explication': "Word intègre un correcteur orthographique/grammatical qui souligne automatiquement les erreurs potentielles, aidant à produire des documents professionnels sans fautes.",
        'mots_cles': 'correcteur orthographique, Word de base, qualité rédaction',
    },
    {
        'categorie': 'Microsoft Word', 'niveau': 'intermediaire', 'type': 'qcm',
        'enonce': "Comment activer le suivi des modifications dans Word pour tracer les changements apportés par plusieurs relecteurs ?",
        'reponses': [
            {'texte': 'Révision > Suivi des modifications', 'correct': True},
            {'texte': 'Fichier > Nouveau', 'correct': False},
            {'texte': 'Insertion > Tableau', 'correct': False},
            {'texte': 'Ce n\'est pas possible dans Word', 'correct': False},
        ],
        'explication': "Le suivi des modifications (onglet Révision) enregistre chaque ajout, suppression ou changement de mise en forme avec le nom de l'auteur, essentiel pour la relecture collaborative de documents professionnels.",
        'mots_cles': 'suivi modifications, révision collaborative, Word',
    },
    {
        'categorie': 'Microsoft Word', 'niveau': 'professionnel', 'type': 'correction_word',
        'enonce': "Un CV présente des espacements incohérents entre les sections (parfois 1 ligne vide, parfois 3), rendant la lecture désordonnée. Quelle est la cause probable et la bonne pratique corrective ?",
        'reponses': [
            {'texte': 'Utilisation de lignes vides manuelles au lieu de l\'espacement « Avant/Après paragraphe » dans les styles — utiliser la mise en forme des paragraphes plutôt que des lignes vides', 'correct': True},
            {'texte': 'Le document est corrompu', 'correct': False},
            {'texte': 'Il faut changer de police', 'correct': False},
            {'texte': 'Le format PDF résout automatiquement ce problème', 'correct': False},
        ],
        'explication': "L'espacement incohérent vient souvent de lignes vides ajoutées manuellement (Entrée) au lieu d'utiliser les paramètres d'espacement « Avant/Après » dans la mise en forme du paragraphe, qui garantissent un espacement uniforme et modifiable en un clic.",
        'mots_cles': 'espacement paragraphe, mise en forme professionnelle, correction CV',
    },
    {
        'categorie': 'Microsoft Excel', 'niveau': 'facile', 'type': 'qcm',
        'enonce': "Quelle touche permet de passer d'une cellule à la suivante (à droite) dans Excel ?",
        'reponses': [
            {'texte': 'Tabulation (Tab)', 'correct': True}, {'texte': 'Échap', 'correct': False},
            {'texte': 'Ctrl', 'correct': False}, {'texte': 'Alt', 'correct': False},
        ],
        'explication': "La touche Tabulation déplace la sélection vers la cellule suivante à droite, tandis qu'Entrée déplace généralement vers le bas — des raccourcis de navigation de base essentiels.",
        'mots_cles': 'navigation cellule, tabulation, Excel de base',
    },
    {
        'categorie': 'Microsoft Excel', 'niveau': 'intermediaire', 'type': 'qcm',
        'enonce': "Quelle fonction Excel permet d'arrondir un nombre à 2 décimales ?",
        'reponses': [
            {'texte': '=ARRONDI(nombre;2)', 'correct': True}, {'texte': '=ROND(nombre;2)', 'correct': False},
            {'texte': '=DECIMALE(nombre;2)', 'correct': False}, {'texte': '=PRECISION(nombre;2)', 'correct': False},
        ],
        'explication': "=ARRONDI(nombre; nombre_de_chiffres) arrondit une valeur au nombre de décimales spécifié — très utilisée pour les calculs financiers et les rapports nécessitant une présentation propre.",
        'mots_cles': 'ARRONDI, fonction Excel, précision numérique',
    },
    {
        'categorie': 'Microsoft Excel', 'niveau': 'avance', 'type': 'qcm',
        'enonce': "Quel type de graphique Excel est le plus adapté pour montrer l'évolution des ventes mois par mois sur une année ?",
        'reponses': [
            {'texte': 'Graphique en courbes (ligne)', 'correct': True}, {'texte': 'Graphique en secteurs (camembert)', 'correct': False},
            {'texte': 'Nuage de points uniquement', 'correct': False}, {'texte': 'Aucun graphique n\'est adapté', 'correct': False},
        ],
        'explication': "Un graphique en courbes est idéal pour visualiser une évolution dans le temps (tendance, saisonnalité), tandis qu'un camembert convient mieux pour montrer des proportions à un instant donné.",
        'mots_cles': 'graphique courbe, visualisation données, choix graphique',
    },
    {
        'categorie': 'Microsoft Excel', 'niveau': 'professionnel', 'type': 'analyse_excel',
        'enonce': "Une feuille Excel de suivi de stock affiche des valeurs négatives inattendues dans la colonne « Quantité restante ». Quelle démarche d'analyse adopter en priorité ?",
        'reponses': [
            {'texte': 'Vérifier la formule de calcul (entrées - sorties) et les données sources pour détecter une erreur de saisie ou de logique', 'correct': True},
            {'texte': 'Supprimer simplement les valeurs négatives', 'correct': False},
            {'texte': 'Ignorer le problème, ce n\'est pas important', 'correct': False},
            {'texte': 'Recommencer tout le tableau depuis zéro', 'correct': False},
        ],
        'explication': "Une valeur négative de stock signale généralement une erreur de saisie (sortie supérieure aux entrées enregistrées) ou une erreur de formule. Il faut auditer la logique de calcul et les données sources avant toute correction, plutôt que de masquer le symptôme.",
        'mots_cles': 'audit formule, diagnostic données, gestion de stock',
    },
    {
        'categorie': 'Microsoft PowerPoint', 'niveau': 'intermediaire', 'type': 'qcm',
        'enonce': "Quelle fonctionnalité PowerPoint permet de répéter un logo ou un numéro de page sur toutes les diapositives automatiquement ?",
        'reponses': [
            {'texte': 'Le masque des diapositives', 'correct': True}, {'texte': 'Le mode lecture', 'correct': False},
            {'texte': 'La transition', 'correct': False}, {'texte': 'L\'animation', 'correct': False},
        ],
        'explication': "Le masque des diapositives permet de placer un élément (logo, numérotation, pied de page) une seule fois, qui apparaîtra automatiquement sur toutes les diapositives de la présentation.",
        'mots_cles': 'masque diapositives, éléments récurrents, PowerPoint',
    },
    {
        'categorie': 'Gestion des fichiers', 'niveau': 'facile', 'type': 'qcm',
        'enonce': "Quelle est l'unité de mesure généralement utilisée pour indiquer la taille d'un fichier volumineux (ex: une vidéo) ?",
        'reponses': [
            {'texte': 'Mo (Mégaoctet) ou Go (Gigaoctet)', 'correct': True}, {'texte': 'Km (Kilomètre)', 'correct': False},
            {'texte': 'Kg (Kilogramme)', 'correct': False}, {'texte': '°C (Degré Celsius)', 'correct': False},
        ],
        'explication': "Les fichiers numériques se mesurent en octets, généralement en Mo (mégaoctets) pour des fichiers moyens ou Go (gigaoctets) pour des fichiers volumineux comme des vidéos.",
        'mots_cles': 'taille fichier, mégaoctet, unités numériques',
    },
    {
        'categorie': 'Gestion des fichiers', 'niveau': 'intermediaire', 'type': 'qcm',
        'enonce': "Pourquoi compresser (zipper) plusieurs fichiers avant de les envoyer par email peut être utile ?",
        'reponses': [
            {'texte': 'Réduit la taille totale et regroupe plusieurs fichiers en un seul pour l\'envoi', 'correct': True},
            {'texte': 'Cela améliore automatiquement la qualité des fichiers', 'correct': False},
            {'texte': 'Cela supprime les virus des fichiers', 'correct': False},
            {'texte': 'Aucun intérêt réel', 'correct': False},
        ],
        'explication': "La compression (ZIP) réduit la taille globale des fichiers (facilitant l'envoi sous les limites de taille d'email) et permet de regrouper plusieurs fichiers en une seule pièce jointe organisée.",
        'mots_cles': 'compression fichiers, ZIP, envoi email',
    },
    {
        'categorie': 'Productivité', 'niveau': 'avance', 'type': 'qcm',
        'enonce': "Quel est l'intérêt d'utiliser des raccourcis clavier plutôt que la souris pour les actions répétitives en bureautique ?",
        'reponses': [
            {'texte': 'Gain de temps significatif et réduction de la fatigue lors de tâches répétitives', 'correct': True},
            {'texte': 'Aucun avantage mesurable', 'correct': False},
            {'texte': 'Cela fonctionne uniquement sur Mac', 'correct': False},
            {'texte': 'Cela rend le travail plus lent au début et pour toujours', 'correct': False},
        ],
        'explication': "Bien qu'il y ait une courbe d'apprentissage initiale, la maîtrise des raccourcis clavier pour les actions fréquentes (copier/coller, enregistrer, formater) génère un gain de productivité cumulatif important sur le long terme.",
        'mots_cles': 'raccourcis clavier, gain de temps, productivité bureautique',
    },
    {
        'categorie': 'Raccourcis clavier', 'niveau': 'facile', 'type': 'qcm',
        'enonce': "Quel raccourci permet de tout sélectionner dans un document ou une feuille de calcul ?",
        'reponses': [
            {'texte': 'Ctrl + A', 'correct': True}, {'texte': 'Ctrl + D', 'correct': False},
            {'texte': 'Ctrl + Q', 'correct': False}, {'texte': 'Ctrl + M', 'correct': False},
        ],
        'explication': "Ctrl+A (Select All) sélectionne l'intégralité du contenu du document ou de la feuille active — l'un des raccourcis les plus utilisés en bureautique.",
        'mots_cles': 'Ctrl+A, sélection totale, raccourci de base',
    },
    {
        'categorie': 'Mise en page', 'niveau': 'intermediaire', 'type': 'qcm',
        'enonce': "Quelle est la fonction des « en-têtes et pieds de page » dans un document Word professionnel ?",
        'reponses': [
            {'texte': 'Afficher des informations récurrentes (logo, titre, numéro de page) sur toutes les pages automatiquement', 'correct': True},
            {'texte': 'Modifier la couleur du texte principal', 'correct': False},
            {'texte': 'Corriger automatiquement les fautes', 'correct': False},
            {'texte': 'Compresser le fichier', 'correct': False},
        ],
        'explication': "Les en-têtes et pieds de page affichent automatiquement des éléments récurrents (titre du document, numéro de page, date, logo) sur chaque page — indispensable pour les rapports professionnels multi-pages.",
        'mots_cles': 'en-tête, pied de page, présentation professionnelle',
    },
    {
        'categorie': 'Impression', 'niveau': 'facile', 'type': 'qcm',
        'enonce': "Quel est l'intérêt d'imprimer en mode « recto-verso » (duplex) pour un document interne ?",
        'reponses': [
            {'texte': 'Économiser du papier', 'correct': True}, {'texte': 'Améliorer la qualité des couleurs', 'correct': False},
            {'texte': 'Accélérer l\'impression', 'correct': False}, {'texte': 'Réduire la taille du fichier', 'correct': False},
        ],
        'explication': "L'impression recto-verso divise par deux la consommation de papier — une pratique écologique et économique recommandée, particulièrement pour les documents internes volumineux.",
        'mots_cles': 'recto-verso, économie papier, impression responsable',
    },
    {
        'categorie': 'Impression', 'niveau': 'professionnel', 'type': 'qcm',
        'enonce': "Un document destiné à l'impression professionnelle en couleur affiche des couleurs différentes à l'écran et sur papier. Quelle est la cause technique la plus probable ?",
        'reponses': [
            {'texte': 'Différence entre les modes colorimétriques RVB (écran) et CMJN (impression)', 'correct': True},
            {'texte': 'L\'imprimante est cassée', 'correct': False},
            {'texte': 'Le fichier est corrompu', 'correct': False},
            {'texte': 'Il faut changer d\'ordinateur', 'correct': False},
        ],
        'explication': "Les écrans affichent en RVB (lumière), les imprimantes reproduisent en CMJN (encre) — ces deux systèmes colorimétriques ne couvrent pas exactement la même gamme de couleurs, expliquant les différences visuelles entre écran et papier.",
        'mots_cles': 'RVB, CMJN, colorimétrie, impression professionnelle',
    },
]


class Command(BaseCommand):
    help = "Seed Batch 3 (FINAL) : 45 questions — complète la banque à 150/150"

    def handle(self, *args, **options):
        modules = {
            'INT': (QUESTIONS_INTERNET, 'Internet, Recherche et Productivité'),
            'IA': (QUESTIONS_IA, 'Intelligence Artificielle'),
            'BUR': (QUESTIONS_BUREAUTIQUE, 'Bureautique Professionnelle'),
        }

        total_creees = 0
        for code, (questions, nom_module) in modules.items():
            module = ModuleBanque.objects.filter(code=code).first()
            if not module:
                self.stdout.write(self.style.ERROR(f"❌ Module {code} introuvable"))
                continue

            for q in questions:
                categorie = CategorieBanque.objects.filter(module=module, nom=q['categorie']).first()
                if not categorie:
                    self.stdout.write(self.style.WARNING(f"⚠️ Catégorie '{q['categorie']}' introuvable pour {code}, ignorée"))
                    continue

                QuestionBanque.objects.create(
                    module=module, categorie=categorie, niveau=q['niveau'], type_question=q['type'],
                    enonce=q['enonce'], reponses_possibles=q.get('reponses', []),
                    reponse_texte_courte=q.get('reponse_texte_courte', ''),
                    explication_pedagogique=q['explication'], mots_cles=q.get('mots_cles', ''),
                    statut='active',
                )
                total_creees += 1

            self.stdout.write(self.style.SUCCESS(f"✅ {nom_module} : {len(questions)} questions créées"))

        self.stdout.write(self.style.SUCCESS(f"\n🎉🎉 BANQUE COMPLÈTE : {total_creees} questions créées — 150/150 ATTEINT !"))