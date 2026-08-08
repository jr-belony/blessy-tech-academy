# ================================================
# SEED_QUESTIONS_BATCH1.PY — Premier lot de questions officielles BTA
# Usage : python manage.py seed_questions_batch1
# 60 questions (20 Internet, 20 IA, 20 Bureautique)
# Réparties sur tous les niveaux et plusieurs types de questions
# ================================================

from django.core.management.base import BaseCommand
from academie.models_banque import ModuleBanque, CategorieBanque, QuestionBanque


QUESTIONS_INTERNET = [
    {
        'categorie': 'Navigation Web', 'niveau': 'facile', 'type': 'qcm',
        'enonce': "Que signifie l'abréviation « URL » ?",
        'reponses': [
            {'texte': 'Uniform Resource Locator', 'correct': True},
            {'texte': 'Universal Reading Language', 'correct': False},
            {'texte': 'United Resource List', 'correct': False},
            {'texte': 'Uniform Record Line', 'correct': False},
        ],
        'explication': "URL signifie « Uniform Resource Locator » : c'est l'adresse unique qui permet de localiser une ressource sur Internet (page, image, fichier).",
        'mots_cles': 'URL, adresse web, navigation',
    },
    {
        'categorie': 'Navigation Web', 'niveau': 'facile', 'type': 'vrai_faux',
        'enonce': "Un cadenas fermé dans la barre d'adresse signifie que la connexion au site est sécurisée (HTTPS).",
        'reponses': [{'texte': 'Vrai', 'correct': True}, {'texte': 'Faux', 'correct': False}],
        'explication': "Le cadenas indique que la connexion utilise le protocole HTTPS, qui chiffre les données échangées entre le navigateur et le site.",
        'mots_cles': 'HTTPS, sécurité, cadenas',
    },
    {
        'categorie': 'Navigation Web', 'niveau': 'intermediaire', 'type': 'qcm',
        'enonce': "Quel raccourci clavier permet d'ouvrir un nouvel onglet dans la plupart des navigateurs ?",
        'reponses': [
            {'texte': 'Ctrl + T', 'correct': True}, {'texte': 'Ctrl + N', 'correct': False},
            {'texte': 'Ctrl + O', 'correct': False}, {'texte': 'Ctrl + W', 'correct': False},
        ],
        'explication': "Ctrl + T ouvre un nouvel onglet. Ctrl + N ouvre une nouvelle fenêtre, Ctrl + W ferme l'onglet actif.",
        'mots_cles': 'raccourci clavier, onglet, navigateur',
    },
    {
        'categorie': 'Recherche avancée', 'niveau': 'intermediaire', 'type': 'qcm',
        'enonce': "Vous cherchez des informations UNIQUEMENT sur le site gouv.ht. Quelle syntaxe utiliser dans Google ?",
        'reponses': [
            {'texte': 'site:gouv.ht', 'correct': True}, {'texte': 'site=gouv.ht', 'correct': False},
            {'texte': 'from:gouv.ht', 'correct': False}, {'texte': '@gouv.ht', 'correct': False},
        ],
        'explication': "L'opérateur « site: » restreint les résultats de recherche à un domaine précis — très utile pour des recherches ciblées et fiables.",
        'mots_cles': 'opérateur de recherche, Google, site:',
    },
    {
        'categorie': 'Opérateurs de recherche', 'niveau': 'avance', 'type': 'qcm',
        'enonce': "Quelle recherche exclut le mot « gratuit » des résultats sur « formation informatique » ?",
        'reponses': [
            {'texte': 'formation informatique -gratuit', 'correct': True},
            {'texte': 'formation informatique !gratuit', 'correct': False},
            {'texte': 'formation informatique NOT(gratuit)', 'correct': False},
            {'texte': 'formation informatique #gratuit', 'correct': False},
        ],
        'explication': "Le signe « - » (moins) juste avant un mot, sans espace, exclut ce terme des résultats de recherche.",
        'mots_cles': 'opérateur exclusion, recherche avancée',
    },
    {
        'categorie': 'Opérateurs de recherche', 'niveau': 'professionnel', 'type': 'reponse_courte',
        'enonce': "Quel opérateur permet de rechercher une expression EXACTE (dans l'ordre précis des mots) sur Google ?",
        'reponses': [],
        'reponse_texte_courte': 'guillemets|" "|guillemets doubles',
        'explication': 'Placer une expression entre guillemets (" ") force Google à chercher exactement cette suite de mots, dans cet ordre précis.',
        'mots_cles': 'guillemets, recherche exacte, opérateur',
    },
    {
        'categorie': 'Sécurité numérique', 'niveau': 'facile', 'type': 'qcm',
        'enonce': "Quelle est la meilleure pratique face à un email demandant vos identifiants bancaires en urgence ?",
        'reponses': [
            {'texte': 'Ne jamais répondre et vérifier directement sur le site officiel', 'correct': True},
            {'texte': 'Répondre rapidement avec les informations demandées', 'correct': False},
            {'texte': 'Cliquer sur le lien pour vérifier', 'correct': False},
            {'texte': "Transférer l'email à des amis pour avis", 'correct': False},
        ],
        'explication': "C'est un cas typique de phishing (hameçonnage). Il ne faut jamais transmettre d'identifiants par email — toujours vérifier directement via le site officiel, sans cliquer sur les liens reçus.",
        'mots_cles': 'phishing, hameçonnage, sécurité, email',
    },
    {
        'categorie': 'Sécurité numérique', 'niveau': 'intermediaire', 'type': 'vrai_faux',
        'enonce': "Utiliser le même mot de passe sur plusieurs sites est une bonne pratique pour ne pas les oublier.",
        'reponses': [{'texte': 'Vrai', 'correct': False}, {'texte': 'Faux', 'correct': True}],
        'explication': "C'est faux et dangereux : si un site est piraté, tous vos autres comptes utilisant le même mot de passe deviennent vulnérables. Utilisez un mot de passe unique par service, idéalement géré par un gestionnaire de mots de passe.",
        'mots_cles': 'mot de passe, sécurité, bonnes pratiques',
    },
    {
        'categorie': 'Sécurité numérique', 'niveau': 'avance', 'type': 'choix_multiples',
        'enonce': "Parmi ces éléments, lesquels sont des signes d'un site potentiellement frauduleux ? (plusieurs réponses possibles)",
        'reponses': [
            {'texte': "Absence de cadenas HTTPS", 'correct': True},
            {'texte': "Fautes d'orthographe nombreuses", 'correct': True},
            {'texte': "URL très proche d'un site connu mais légèrement différente", 'correct': True},
            {'texte': "Présence d'un logo officiel", 'correct': False},
        ],
        'explication': "L'absence de HTTPS, les fautes d'orthographe et les URLs imitant un site connu (typosquatting) sont des signaux d'alerte classiques. Un simple logo ne garantit rien, il peut être copié facilement.",
        'mots_cles': 'phishing, site frauduleux, typosquatting',
    },
    {
        'categorie': 'Google Workspace', 'niveau': 'facile', 'type': 'qcm',
        'enonce': "Quel outil Google Workspace permet de créer des documents texte collaboratifs en ligne ?",
        'reponses': [
            {'texte': 'Google Docs', 'correct': True}, {'texte': 'Google Sheets', 'correct': False},
            {'texte': 'Google Slides', 'correct': False}, {'texte': 'Google Forms', 'correct': False},
        ],
        'explication': "Google Docs est l'équivalent de Word dans Google Workspace — traitement de texte collaboratif en temps réel.",
        'mots_cles': 'Google Docs, Google Workspace, collaboration',
    },
    {
        'categorie': 'Google Workspace', 'niveau': 'intermediaire', 'type': 'qcm',
        'enonce': "Dans Google Docs, comment donner à quelqu'un le droit de MODIFIER un document sans pouvoir le supprimer ?",
        'reponses': [
            {'texte': 'Partager avec le rôle « Éditeur »', 'correct': True},
            {'texte': 'Partager avec le rôle « Lecteur »', 'correct': False},
            {'texte': 'Partager avec le rôle « Commentateur »', 'correct': False},
            {'texte': 'Rendre le document public', 'correct': False},
        ],
        'explication': "Le rôle « Éditeur » permet de modifier le contenu. « Lecteur » ne permet que la consultation, « Commentateur » permet d'ajouter des commentaires sans modifier le texte.",
        'mots_cles': 'partage, permissions, Google Docs',
    },
    {
        'categorie': 'Organisation des fichiers', 'niveau': 'facile', 'type': 'qcm',
        'enonce': "Quelle extension de fichier correspond généralement à un document PDF ?",
        'reponses': [
            {'texte': '.pdf', 'correct': True}, {'texte': '.doc', 'correct': False},
            {'texte': '.exe', 'correct': False}, {'texte': '.zip', 'correct': False},
        ],
        'explication': "L'extension .pdf identifie un fichier au format PDF (Portable Document Format), lisible sur presque tous les appareils sans modification de mise en page.",
        'mots_cles': 'extension fichier, PDF, format',
    },
    {
        'categorie': 'Organisation des fichiers', 'niveau': 'intermediaire', 'type': 'classement',
        'enonce': "Classez ces éléments du plus général au plus spécifique dans une organisation de dossiers.",
        'reponses': ['Disque dur', 'Dossier principal', 'Sous-dossier', 'Fichier'],
        'explication': "Une organisation hiérarchique va du général (disque) vers le spécifique (fichier), en passant par des dossiers et sous-dossiers de plus en plus précis.",
        'mots_cles': 'arborescence, organisation fichiers, hiérarchie',
    },
    {
        'categorie': 'Collaboration', 'niveau': 'intermediaire', 'type': 'qcm',
        'enonce': "Quel est l'avantage principal du travail collaboratif en ligne (type Google Docs) par rapport à l'envoi de fichiers par email ?",
        'reponses': [
            {'texte': 'Modification simultanée et une seule version à jour', 'correct': True},
            {'texte': 'Aucune connexion Internet nécessaire', 'correct': False},
            {'texte': 'Les fichiers sont plus légers', 'correct': False},
            {'texte': 'Impossible à pirater', 'correct': False},
        ],
        'explication': "Le travail collaboratif en ligne évite le problème classique des multiples versions d'un même fichier envoyées par email — tout le monde travaille sur LA même version, en temps réel.",
        'mots_cles': 'collaboration, cloud, versions de fichiers',
    },
    {
        'categorie': 'Productivité', 'niveau': 'facile', 'type': 'qcm',
        'enonce': "Quelle application permet de créer des sondages et formulaires en ligne dans Google Workspace ?",
        'reponses': [
            {'texte': 'Google Forms', 'correct': True}, {'texte': 'Google Keep', 'correct': False},
            {'texte': 'Google Meet', 'correct': False}, {'texte': 'Google Chat', 'correct': False},
        ],
        'explication': "Google Forms permet de créer des formulaires, sondages et quiz, avec collecte automatique des réponses dans une feuille de calcul.",
        'mots_cles': 'Google Forms, sondage, formulaire',
    },
    {
        'categorie': 'Productivité', 'niveau': 'avance', 'type': 'scenario_pro',
        'enonce': "Un manager vous demande de recueillir les disponibilités de 30 collègues pour une réunion, sans échange d'emails multiples. Quel outil recommandez-vous et pourquoi ?",
        'reponses': [
            {'texte': 'Google Forms ou un sondage type Doodle, pour centraliser automatiquement les réponses', 'correct': True},
            {'texte': "Envoyer 30 emails individuels", 'correct': False},
            {'texte': 'Appeler chaque personne', 'correct': False},
            {'texte': 'Créer un groupe WhatsApp', 'correct': False},
        ],
        'explication': "Un formulaire centralisé (Google Forms, Doodle) permet de collecter et visualiser automatiquement toutes les réponses sans échanges manuels répétitifs — gain de temps considérable pour ce cas d'usage.",
        'mots_cles': 'organisation réunion, outils collaboratifs, efficacité',
    },
    {
        'categorie': 'Navigation Web', 'niveau': 'professionnel', 'type': 'etude_cas',
        'enonce': "Un client se plaint que son navigateur affiche « Votre connexion n'est pas privée » sur le site de sa banque. Que devez-vous lui conseiller en priorité ?",
        'reponses': [
            {'texte': 'Ne pas continuer, fermer la page et contacter directement la banque par téléphone', 'correct': True},
            {'texte': "Cliquer sur « Continuer quand même »", 'correct': False},
            {'texte': "Ignorer l'avertissement s'il est pressé", 'correct': False},
            {'texte': "Redémarrer l'ordinateur", 'correct': False},
        ],
        'explication': "Cet avertissement signale un problème de certificat de sécurité — potentiellement un site frauduleux imitant la banque. La bonne pratique est de ne jamais continuer et de vérifier directement par un canal officiel (téléphone, application bancaire).",
        'mots_cles': 'certificat SSL, sécurité, phishing bancaire',
    },
    {
        'categorie': 'Recherche avancée', 'niveau': 'facile', 'type': 'qcm',
        'enonce': "Pour trouver rapidement une information récente, quel filtre Google est utile ?",
        'reponses': [
            {'texte': 'Outils > Résultats récents (dernière semaine/mois)', 'correct': True},
            {'texte': 'Ajouter le mot « récent » à la recherche', 'correct': False},
            {'texte': 'Rechercher en majuscules', 'correct': False},
            {'texte': 'Utiliser un point d\'exclamation', 'correct': False},
        ],
        'explication': "Google propose un filtre « Outils » permettant de restreindre les résultats par période (dernière heure, jour, semaine, mois, année) — bien plus fiable que d'ajouter un mot-clé.",
        'mots_cles': 'filtre recherche, actualité, Google',
    },
    {
        'categorie': 'Google Workspace', 'niveau': 'avance', 'type': 'qcm',
        'enonce': "Comment récupérer une version antérieure d'un document Google Docs après une modification indésirable ?",
        'reponses': [
            {'texte': 'Fichier > Historique des versions > Voir l\'historique des versions', 'correct': True},
            {'texte': "Ce n'est pas possible, il faut retaper le document", 'correct': False},
            {'texte': 'Supprimer et recréer le document', 'correct': False},
            {'texte': 'Contacter le support Google', 'correct': False},
        ],
        'explication': "Google Docs enregistre automatiquement l'historique complet des versions — accessible via Fichier > Historique des versions, permettant de restaurer un état antérieur à tout moment.",
        'mots_cles': 'historique versions, Google Docs, récupération',
    },
    {
        'categorie': 'Sécurité numérique', 'niveau': 'professionnel', 'type': 'reponse_courte',
        'enonce': "Quel terme désigne une authentification nécessitant deux éléments distincts (mot de passe + code SMS par exemple) ?",
        'reponses': [],
        'reponse_texte_courte': 'authentification à deux facteurs|2FA|double authentification|authentification multifacteur',
        'explication': "L'authentification à deux facteurs (2FA) ajoute une couche de sécurité : même si le mot de passe est compromis, un second élément (code, application) reste nécessaire pour se connecter.",
        'mots_cles': '2FA, authentification, sécurité renforcée',
    },
]


QUESTIONS_IA = [
    {
        'categorie': 'Fondamentaux', 'niveau': 'facile', 'type': 'qcm',
        'enonce': "Que signifie « IA » ?",
        'reponses': [
            {'texte': 'Intelligence Artificielle', 'correct': True}, {'texte': 'Interface Automatique', 'correct': False},
            {'texte': 'Information Analytique', 'correct': False}, {'texte': 'Intégration Applicative', 'correct': False},
        ],
        'explication': "IA signifie Intelligence Artificielle : des systèmes informatiques capables de réaliser des tâches nécessitant normalement l'intelligence humaine (raisonnement, apprentissage, compréhension du langage).",
        'mots_cles': 'IA, définition, intelligence artificielle',
    },
    {
        'categorie': 'Fondamentaux', 'niveau': 'intermediaire', 'type': 'vrai_faux',
        'enonce': "ChatGPT et les IA génératives « comprennent » réellement ce qu'elles écrivent, comme un être humain.",
        'reponses': [{'texte': 'Vrai', 'correct': False}, {'texte': 'Faux', 'correct': True}],
        'explication': "C'est faux : les IA génératives prédisent statistiquement le mot suivant le plus probable à partir de leur entraînement, sans compréhension consciente au sens humain du terme — d'où l'importance de toujours vérifier leurs réponses.",
        'mots_cles': 'IA générative, compréhension, limites',
    },
    {
        'categorie': 'IA générative', 'niveau': 'facile', 'type': 'qcm',
        'enonce': "Lequel de ces outils est une IA générative capable de produire du texte ?",
        'reponses': [
            {'texte': 'ChatGPT / Gemini / Claude', 'correct': True}, {'texte': 'Google Maps', 'correct': False},
            {'texte': 'Microsoft Paint', 'correct': False}, {'texte': 'Adobe Acrobat Reader', 'correct': False},
        ],
        'explication': "ChatGPT, Gemini et Claude sont des IA génératives conversationnelles capables de produire du texte, répondre à des questions et assister dans diverses tâches.",
        'mots_cles': 'IA générative, chatbot, outils IA',
    },
    {
        'categorie': 'IA générative', 'niveau': 'intermediaire', 'type': 'association',
        'enonce': "Associez chaque type d'IA générative à son usage principal.",
        'reponses': [
            {'gauche': 'IA de texte (ChatGPT, Claude)', 'droite': 'Rédiger, résumer, répondre à des questions'},
            {'gauche': 'IA d\'image (Midjourney, DALL-E)', 'droite': 'Créer des visuels à partir de descriptions'},
            {'gauche': 'IA de code (GitHub Copilot)', 'droite': 'Assister à la programmation'},
        ],
        'explication': "Chaque famille d'IA générative est spécialisée : texte pour la rédaction, image pour la création visuelle, code pour l'assistance à la programmation — bien que les frontières deviennent de plus en plus floues (IA multimodales).",
        'mots_cles': 'types IA générative, spécialisation',
    },
    {
        'categorie': 'Prompt Engineering', 'niveau': 'intermediaire', 'type': 'qcm',
        'enonce': "Quel prompt (instruction) est le plus susceptible de donner une bonne réponse d'une IA générative ?",
        'reponses': [
            {'texte': '« Rédige un email professionnel de 100 mots pour reporter une réunion, ton courtois, destinataire : mon équipe »', 'correct': True},
            {'texte': '« Écris un email »', 'correct': False},
            {'texte': '« Fais quelque chose de bien »', 'correct': False},
            {'texte': '« Email »', 'correct': False},
        ],
        'explication': "Un bon prompt est précis : il indique le contexte, le format, la longueur, le ton et le destinataire. Plus l'instruction est claire, plus la réponse générée sera pertinente et exploitable.",
        'mots_cles': 'prompt engineering, précision, instructions IA',
    },
    {
        'categorie': 'Prompt Engineering', 'niveau': 'avance', 'type': 'analyse_prompt_ia',
        'enonce': "Analysez ce prompt : « Explique-moi Excel ». Quel est son principal défaut et comment l'améliorer ?",
        'reponses': [
            {'texte': 'Trop vague — préciser le niveau, l\'objectif et le format attendu (ex: « Explique les formules SOMME et MOYENNE à un débutant, avec un exemple concret »)', 'correct': True},
            {'texte': 'Il est parfait tel quel', 'correct': False},
            {'texte': 'Il est trop long', 'correct': False},
            {'texte': 'Il contient une faute grammaticale', 'correct': False},
        ],
        'explication': "Un prompt vague comme « Explique-moi Excel » couvre un sujet immense — l'IA doit deviner le niveau et l'objectif. Préciser le contexte (débutant/avancé), l'objectif (apprendre une formule précise) et le format (avec exemple) améliore drastiquement la pertinence de la réponse.",
        'mots_cles': 'analyse prompt, precision, amelioration instruction',
    },
    {
        'categorie': 'Prompt Engineering', 'niveau': 'professionnel', 'type': 'completer',
        'enonce': "Complétez : Donner à l'IA un ______ (des exemples de ce que vous attendez) améliore souvent la qualité de sa réponse. C'est ce qu'on appelle le prompting « few-shot ».",
        'reponses': [],
        'reponse_texte_courte': 'exemple|des exemples|contexte',
        'explication': "Le « few-shot prompting » consiste à fournir un ou plusieurs exemples du résultat attendu dans le prompt lui-même, ce qui guide fortement l'IA vers le format et le style souhaités.",
        'mots_cles': 'few-shot prompting, exemples, technique avancée',
    },
    {
        'categorie': 'Éthique', 'niveau': 'facile', 'type': 'vrai_faux',
        'enonce': "Il est acceptable de soumettre à une IA générative des informations confidentielles d'une entreprise sans autorisation.",
        'reponses': [{'texte': 'Vrai', 'correct': False}, {'texte': 'Faux', 'correct': True}],
        'explication': "C'est faux : les données saisies dans certains outils IA peuvent être utilisées pour l'entraînement ou stockées par le fournisseur. Il faut toujours vérifier la politique de confidentialité et obtenir les autorisations nécessaires avant de partager des informations sensibles.",
        'mots_cles': 'éthique IA, confidentialité, données sensibles',
    },
    {
        'categorie': 'Éthique', 'niveau': 'intermediaire', 'type': 'qcm',
        'enonce': "Un étudiant utilise une IA pour rédiger entièrement son devoir et le remet sans le préciser. Quel est le problème principal ?",
        'reponses': [
            {'texte': "Manque d'intégrité académique — le travail ne reflète pas ses propres compétences", 'correct': True},
            {'texte': "Aucun problème, c'est une pratique normale", 'correct': False},
            {'texte': "L'IA est illégale", 'correct': False},
            {'texte': "Le devoir sera automatiquement meilleur", 'correct': False},
        ],
        'explication': "Utiliser une IA pour produire un travail sans le déclarer pose un problème d'intégrité académique — cela ne permet pas d'évaluer les compétences réelles de l'étudiant, contraire à l'objectif de l'apprentissage.",
        'mots_cles': 'intégrité académique, éthique, plagiat IA',
    },
    {
        'categorie': 'Vérification des réponses', 'niveau': 'intermediaire', 'type': 'qcm',
        'enonce': "Que désigne le terme « hallucination » en intelligence artificielle générative ?",
        'reponses': [
            {'texte': "Une information fausse générée avec assurance par l'IA, présentée comme vraie", 'correct': True},
            {'texte': "Un bug qui fait planter le logiciel", 'correct': False},
            {'texte': "Une image générée par erreur", 'correct': False},
            {'texte': "Un virus informatique", 'correct': False},
        ],
        'explication': "Une « hallucination » est une réponse incorrecte ou inventée que l'IA présente avec un ton assuré, comme si elle était vraie. C'est pourquoi il est essentiel de toujours vérifier les faits, dates, chiffres et sources fournis par une IA.",
        'mots_cles': 'hallucination IA, fiabilité, vérification',
    },
    {
        'categorie': 'Vérification des réponses', 'niveau': 'avance', 'type': 'scenario_pro',
        'enonce': "Une IA vous fournit une statistique précise (« 73,2% des entreprises... ») sans citer de source. Quelle est la bonne démarche professionnelle ?",
        'reponses': [
            {'texte': "Vérifier cette statistique auprès d'une source fiable avant de l'utiliser dans un document officiel", 'correct': True},
            {'texte': "L'utiliser telle quelle, l'IA est toujours fiable", 'correct': False},
            {'texte': "L'ignorer complètement sans vérifier", 'correct': False},
            {'texte': "Arrondir le chiffre pour le rendre crédible", 'correct': False},
        ],
        'explication': "Les IA génératives peuvent produire des chiffres précis mais inventés (hallucination). Dans un contexte professionnel, toute statistique doit être vérifiée auprès d'une source fiable avant publication ou utilisation dans une prise de décision.",
        'mots_cles': 'vérification faits, statistiques, rigueur professionnelle',
    },
    {
        'categorie': 'Cas professionnels', 'niveau': 'intermediaire', 'type': 'scenario_pro',
        'enonce': "Vous devez rédiger 20 descriptions de produits similaires pour un catalogue. Comment l'IA peut-elle vous faire gagner du temps efficacement ?",
        'reponses': [
            {'texte': 'Créer un modèle de prompt réutilisable avec les variables (nom, caractéristiques) puis relire chaque résultat', 'correct': True},
            {'texte': 'Publier directement les 20 textes générés sans relecture', 'correct': False},
            {'texte': 'Ne pas utiliser l\'IA, c\'est trop risqué', 'correct': False},
            {'texte': 'Copier la même description pour tous les produits', 'correct': False},
        ],
        'explication': "L'IA excelle pour accélérer les tâches répétitives structurées (comme des descriptions similaires) via un prompt réutilisable — mais une relecture humaine reste indispensable pour garantir exactitude et qualité avant publication.",
        'mots_cles': 'productivité IA, cas d\'usage professionnel, relecture',
    },
    {
        'categorie': 'Cas professionnels', 'niveau': 'professionnel', 'type': 'etude_cas',
        'enonce': "Un responsable RH veut utiliser une IA pour présélectionner des CV. Quel risque éthique majeur doit-il anticiper ?",
        'reponses': [
            {'texte': 'Biais algorithmique pouvant discriminer certains profils de façon injuste et non intentionnelle', 'correct': True},
            {'texte': 'Aucun risque, l\'IA est neutre par nature', 'correct': False},
            {'texte': 'Le processus sera trop lent', 'correct': False},
            {'texte': 'Les CV seront automatiquement tous acceptés', 'correct': False},
        ],
        'explication': "Les IA entraînées sur des données historiques peuvent reproduire ou amplifier des biais existants (genre, origine, âge...). Une supervision humaine et un audit régulier du système sont indispensables pour un usage RH éthique et responsable.",
        'mots_cles': 'biais algorithmique, éthique RH, IA responsable',
    },
    {
        'categorie': 'Automatisation', 'niveau': 'facile', 'type': 'qcm',
        'enonce': "Quel est l'objectif principal de l'automatisation de tâches avec l'IA en entreprise ?",
        'reponses': [
            {'texte': 'Gagner du temps sur les tâches répétitives pour se concentrer sur des tâches à plus forte valeur ajoutée', 'correct': True},
            {'texte': 'Remplacer complètement tous les employés', 'correct': False},
            {'texte': 'Compliquer les processus existants', 'correct': False},
            {'texte': 'Augmenter les coûts sans bénéfice', 'correct': False},
        ],
        'explication': "L'automatisation intelligente vise à libérer du temps humain sur les tâches répétitives et à faible valeur (tri d'emails, saisie de données) pour se concentrer sur l'analyse, la créativité et la relation client.",
        'mots_cles': 'automatisation, productivité, valeur ajoutée',
    },
    {
        'categorie': 'Automatisation', 'niveau': 'avance', 'type': 'qcm',
        'enonce': "Quel type de tâche est le MOINS adapté à une automatisation complète par IA actuellement ?",
        'reponses': [
            {'texte': 'Une décision complexe nécessitant du jugement éthique et contextuel', 'correct': True},
            {'texte': 'Le tri automatique d\'emails par mots-clés', 'correct': False},
            {'texte': 'La génération d\'un brouillon de réponse type', 'correct': False},
            {'texte': 'Le calcul automatique de statistiques simples', 'correct': False},
        ],
        'explication': "Les décisions nécessitant jugement éthique, empathie et compréhension contextuelle fine (ex: licenciement, litige client sensible) restent du ressort humain — l'IA peut assister mais pas remplacer ce type de décision.",
        'mots_cles': 'limites automatisation, jugement humain, IA responsable',
    },
    {
        'categorie': 'Fondamentaux', 'niveau': 'avance', 'type': 'qcm',
        'enonce': "Quelle différence principale distingue une IA générative d'un moteur de recherche classique comme Google ?",
        'reponses': [
            {'texte': "L'IA générative crée du nouveau contenu, le moteur de recherche indexe et retrouve du contenu existant", 'correct': True},
            {'texte': "Il n'y a aucune différence", 'correct': False},
            {'texte': "Le moteur de recherche est plus récent", 'correct': False},
            {'texte': "L'IA générative ne fonctionne pas sur Internet", 'correct': False},
        ],
        'explication': "Un moteur de recherche retrouve et classe des pages web EXISTANTES. Une IA générative PRODUIT du nouveau texte/image en se basant sur des motifs appris — d'où l'importance de vérifier ses réponses, contrairement à une source déjà publiée et vérifiable.",
        'mots_cles': 'IA générative vs moteur de recherche, distinction',
    },
    {
        'categorie': 'Éthique', 'niveau': 'professionnel', 'type': 'reponse_courte',
        'enonce': "Quel terme désigne le fait de citer/attribuer correctement l'usage de l'IA dans un travail académique ou professionnel ?",
        'reponses': [],
        'reponse_texte_courte': 'transparence|divulgation|attribution|citation',
        'explication': "La transparence sur l'usage de l'IA (préciser qu'un outil a été utilisé et comment) est une pratique éthique de plus en plus attendue dans les milieux académiques et professionnels, garantissant l'intégrité du travail présenté.",
        'mots_cles': 'transparence IA, attribution, intégrité',
    },
    {
        'categorie': 'IA générative', 'niveau': 'professionnel', 'type': 'analyse_prompt_ia',
        'enonce': "Un collègue vous montre ce prompt utilisé pour générer un rapport financier : « Invente des chiffres de vente réalistes pour notre entreprise ». Quel est le problème critique ?",
        'reponses': [
            {'texte': "Demander à l'IA d'« inventer » des données financières est dangereux — cela produit de fausses informations pouvant induire en erreur des décisions réelles", 'correct': True},
            {'texte': "Aucun problème, c'est un usage normal", 'correct': False},
            {'texte': "Le prompt est trop court", 'correct': False},
            {'texte': "Il manque une virgule", 'correct': False},
        ],
        'explication': "Demander explicitement à une IA d'« inventer » des données financières crée un contenu potentiellement trompeur qui pourrait être confondu avec de vraies données — un risque majeur en contexte professionnel où l'exactitude est critique.",
        'mots_cles': 'donnees fictives, risque professionnel, analyse critique prompt',
    },
    {
        'categorie': 'Vérification des réponses', 'niveau': 'facile', 'type': 'qcm',
        'enonce': "Après avoir reçu une réponse d'une IA sur un sujet médical important, que devez-vous faire avant d'agir ?",
        'reponses': [
            {'texte': 'Consulter un professionnel de santé qualifié pour confirmation', 'correct': True},
            {'texte': 'Agir immédiatement selon la réponse de l\'IA', 'correct': False},
            {'texte': 'Partager la réponse sur les réseaux sociaux', 'correct': False},
            {'texte': 'Ignorer complètement le sujet', 'correct': False},
        ],
        'explication': "Pour tout sujet à enjeu important (santé, droit, finance), une IA générative ne remplace jamais un professionnel qualifié — elle peut informer, mais la décision finale doit être validée par une expertise humaine compétente.",
        'mots_cles': 'limites IA, sujets sensibles, validation professionnelle',
    },
]


QUESTIONS_BUREAUTIQUE = [
    {
        'categorie': 'Microsoft Word', 'niveau': 'facile', 'type': 'qcm',
        'enonce': "Quel raccourci clavier permet de mettre un texte en gras dans Word ?",
        'reponses': [
            {'texte': 'Ctrl + G', 'correct': True}, {'texte': 'Ctrl + B', 'correct': False},
            {'texte': 'Ctrl + I', 'correct': False}, {'texte': 'Ctrl + U', 'correct': False},
        ],
        'explication': "Ctrl + G applique le gras dans la version française de Word (Ctrl+B dans la version anglaise « Bold »). Ctrl+I est l'italique, Ctrl+U le souligné.",
        'mots_cles': 'Word, gras, raccourci clavier',
    },
    {
        'categorie': 'Microsoft Word', 'niveau': 'intermediaire', 'type': 'qcm',
        'enonce': "Comment insérer automatiquement une table des matières qui se met à jour dans Word ?",
        'reponses': [
            {'texte': 'Utiliser les styles de titre (Titre 1, Titre 2...) puis Références > Table des matières', 'correct': True},
            {'texte': "Taper manuellement chaque titre et son numéro de page", 'correct': False},
            {'texte': 'Copier-coller les titres dans un tableau', 'correct': False},
            {'texte': "Ce n'est pas possible dans Word", 'correct': False},
        ],
        'explication': "L'utilisation cohérente des styles de titre permet à Word de générer et mettre à jour automatiquement une table des matières via l'onglet Références — un gain de temps essentiel pour les documents longs.",
        'mots_cles': 'table des matières, styles, Word',
    },
    {
        'categorie': 'Microsoft Word', 'niveau': 'avance', 'type': 'correction_word',
        'enonce': "Un document Word présente des titres qui ne sont pas alignés avec la table des matières après modification. Quelle est la cause la plus probable et la solution ?",
        'reponses': [
            {'texte': "La table des matières n'a pas été actualisée — clic droit dessus > Mettre à jour les champs", 'correct': True},
            {'texte': 'Le document est corrompu, il faut le refaire entièrement', 'correct': False},
            {'texte': "C'est un bug impossible à corriger", 'correct': False},
            {'texte': "Il faut réinstaller Word", 'correct': False},
        ],
        'explication': "La table des matières générée automatiquement ne se met PAS à jour en temps réel — il faut la rafraîchir manuellement (clic droit > Mettre à jour les champs) après toute modification des titres.",
        'mots_cles': 'mise à jour table des matières, correction document',
    },
    {
        'categorie': 'Microsoft Excel', 'niveau': 'facile', 'type': 'qcm',
        'enonce': "Quelle formule Excel additionne automatiquement une plage de cellules (ex: A1 à A10) ?",
        'reponses': [
            {'texte': '=SOMME(A1:A10)', 'correct': True}, {'texte': '=ADDITION(A1:A10)', 'correct': False},
            {'texte': '=TOTAL(A1:A10)', 'correct': False}, {'texte': '=PLUS(A1:A10)', 'correct': False},
        ],
        'explication': "=SOMME() est la fonction Excel dédiée à l'addition d'une plage de cellules — l'une des formules les plus utilisées en bureautique.",
        'mots_cles': 'Excel, SOMME, formule de base',
    },
    {
        'categorie': 'Microsoft Excel', 'niveau': 'intermediaire', 'type': 'qcm',
        'enonce': "Quelle fonction Excel permet de rechercher une valeur dans une colonne et retourner une donnée correspondante d'une autre colonne ?",
        'reponses': [
            {'texte': 'RECHERCHEV (ou XLOOKUP)', 'correct': True}, {'texte': 'SOMME.SI', 'correct': False},
            {'texte': 'CONCATENER', 'correct': False}, {'texte': 'ARRONDI', 'correct': False},
        ],
        'explication': "RECHERCHEV (VLOOKUP) — ou son successeur plus puissant XLOOKUP — recherche une valeur dans une colonne et renvoie une donnée associée d'une autre colonne, essentielle pour croiser des tableaux de données.",
        'mots_cles': 'RECHERCHEV, XLOOKUP, Excel intermédiaire',
    },
    {
        'categorie': 'Microsoft Excel', 'niveau': 'avance', 'type': 'analyse_excel',
        'enonce': "Une feuille Excel contient des ventes par mois. Quelle fonctionnalité permet d'analyser rapidement les totaux par région ET par produit, de façon interactive ?",
        'reponses': [
            {'texte': 'Un Tableau Croisé Dynamique (TCD)', 'correct': True}, {'texte': 'Le collage spécial', 'correct': False},
            {'texte': 'La mise en forme conditionnelle', 'correct': False}, {'texte': 'Le mode plan', 'correct': False},
        ],
        'explication': "Le Tableau Croisé Dynamique (TCD) permet de croiser et résumer instantanément de grandes quantités de données selon plusieurs axes (région, produit, période) sans écrire de formule complexe.",
        'mots_cles': 'tableau croisé dynamique, TCD, analyse de données',
    },
    {
        'categorie': 'Microsoft Excel', 'niveau': 'professionnel', 'type': 'analyse_excel',
        'enonce': "Une formule =SI(A1>1000;\"Élevé\";\"Normal\") retourne #NOM? au lieu du résultat attendu. Quelle est la cause la plus probable ?",
        'reponses': [
            {'texte': 'Les points-virgules devraient être des virgules selon la version régionale d\'Excel (US) ou inversement', 'correct': True},
            {'texte': 'La cellule A1 est vide', 'correct': False},
            {'texte': 'Excel ne supporte pas les fonctions SI', 'correct': False},
            {'texte': 'Le fichier est corrompu', 'correct': False},
        ],
        'explication': "L'erreur #NOM? apparaît souvent quand le séparateur d'arguments ne correspond pas aux paramètres régionaux d'Excel (virgule en anglais US, point-virgule en français) — un piège classique lors du partage de fichiers entre versions différentes.",
        'mots_cles': 'erreur #NOM?, diagnostic Excel, paramètres régionaux',
    },
    {
        'categorie': 'Microsoft PowerPoint', 'niveau': 'facile', 'type': 'qcm',
        'enonce': "Quel raccourci permet de lancer un diaporama PowerPoint depuis le début ?",
        'reponses': [
            {'texte': 'F5', 'correct': True}, {'texte': 'F2', 'correct': False},
            {'texte': 'Ctrl + P', 'correct': False}, {'texte': 'Alt + F4', 'correct': False},
        ],
        'explication': "F5 lance le diaporama depuis la première diapositive. Maj+F5 le lance depuis la diapositive actuellement sélectionnée.",
        'mots_cles': 'PowerPoint, raccourci, diaporama',
    },
    {
        'categorie': 'Microsoft PowerPoint', 'niveau': 'intermediaire', 'type': 'amelioration_ppt',
        'enonce': "Une diapositive contient 200 mots en petite police sur fond chargé. Quelle amélioration est prioritaire ?",
        'reponses': [
            {'texte': 'Réduire drastiquement le texte (règle 6x6), augmenter la taille de police, simplifier le fond', 'correct': True},
            {'texte': 'Ajouter encore plus de texte pour être complet', 'correct': False},
            {'texte': 'Changer uniquement la couleur du texte', 'correct': False},
            {'texte': 'Ajouter des animations complexes', 'correct': False},
        ],
        'explication': "La règle 6x6 (max 6 lignes, 6 mots par ligne) évite la surcharge visuelle. Une diapositive doit soutenir le discours oral, pas le remplacer par un mur de texte illisible.",
        'mots_cles': 'design présentation, règle 6x6, lisibilité',
    },
    {
        'categorie': 'Microsoft PowerPoint', 'niveau': 'avance', 'type': 'qcm',
        'enonce': "Quel outil PowerPoint permet d'appliquer un style visuel cohérent à TOUTES les diapositives d'un coup ?",
        'reponses': [
            {'texte': 'Le masque des diapositives', 'correct': True}, {'texte': 'Le mode trieuse', 'correct': False},
            {'texte': 'Les commentaires', 'correct': False}, {'texte': 'Le mode présentateur', 'correct': False},
        ],
        'explication': "Le masque des diapositives (Affichage > Masque des diapositives) permet de définir une seule fois la mise en forme (couleurs, polices, logo) appliquée automatiquement à toute la présentation.",
        'mots_cles': 'masque diapositives, cohérence visuelle, PowerPoint',
    },
    {
        'categorie': 'Gestion des fichiers', 'niveau': 'facile', 'type': 'qcm',
        'enonce': "Quel format est recommandé pour partager un document en garantissant que sa mise en page ne changera pas ?",
        'reponses': [
            {'texte': 'PDF', 'correct': True}, {'texte': '.docx modifiable', 'correct': False},
            {'texte': '.txt', 'correct': False}, {'texte': '.tmp', 'correct': False},
        ],
        'explication': "Le PDF fige la mise en page exactement telle qu'elle apparaît à l'auteur, indépendamment du logiciel ou de l'appareil du destinataire — idéal pour le partage final d'un document.",
        'mots_cles': 'PDF, format document, partage',
    },
    {
        'categorie': 'Raccourcis clavier', 'niveau': 'facile', 'type': 'association',
        'enonce': "Associez chaque raccourci clavier à son action (Windows/Office).",
        'reponses': [
            {'gauche': 'Ctrl + Z', 'droite': 'Annuler'}, {'gauche': 'Ctrl + S', 'droite': 'Enregistrer'},
            {'gauche': 'Ctrl + C', 'droite': 'Copier'}, {'gauche': 'Ctrl + V', 'droite': 'Coller'},
        ],
        'explication': "Ces raccourcis clavier universels dans la suite Office et la plupart des logiciels Windows permettent un gain de productivité important une fois maîtrisés.",
        'mots_cles': 'raccourcis clavier, productivité, Office',
    },
    {
        'categorie': 'Mise en page', 'niveau': 'intermediaire', 'type': 'qcm',
        'enonce': "Dans Word, comment insérer un saut de page SANS ajouter plusieurs lignes vides ?",
        'reponses': [
            {'texte': 'Ctrl + Entrée (insertion d\'un saut de page)', 'correct': True},
            {'texte': 'Appuyer sur Entrée plusieurs fois', 'correct': False},
            {'texte': 'Utiliser la barre d\'espace', 'correct': False},
            {'texte': 'Ce n\'est pas possible', 'correct': False},
        ],
        'explication': "Ctrl+Entrée insère un véritable saut de page — bien plus propre et stable qu'ajouter des lignes vides, qui se dérègle facilement lors de modifications ultérieures du document.",
        'mots_cles': 'saut de page, mise en page, Word',
    },
    {
        'categorie': 'Impression', 'niveau': 'facile', 'type': 'qcm',
        'enonce': "Avant d'imprimer un document long, quelle fonctionnalité permet de vérifier son rendu sans gaspiller de papier ?",
        'reponses': [
            {'texte': 'L\'aperçu avant impression', 'correct': True}, {'texte': 'Le correcteur orthographique', 'correct': False},
            {'texte': 'Le mode brouillon', 'correct': False}, {'texte': 'Le zoom', 'correct': False},
        ],
        'explication': "L'aperçu avant impression affiche exactement le rendu final sur papier — permettant de repérer les problèmes de mise en page (marges, sauts de page) avant de gaspiller du papier.",
        'mots_cles': 'aperçu impression, bureautique, bonnes pratiques',
    },
    {
        'categorie': 'Impression', 'niveau': 'intermediaire', 'type': 'qcm',
        'enonce': "Comment imprimer uniquement les pages 2 à 5 d'un document de 20 pages ?",
        'reponses': [
            {'texte': 'Dans les options d\'impression, indiquer la plage « 2-5 »', 'correct': True},
            {'texte': 'Supprimer les autres pages avant impression', 'correct': False},
            {'texte': 'Ce n\'est pas possible', 'correct': False},
            {'texte': 'Imprimer tout puis jeter les pages inutiles', 'correct': False},
        ],
        'explication': "La quasi-totalité des logiciels bureautiques permet de spécifier une plage de pages précise dans la boîte de dialogue d'impression, évitant tout gaspillage de papier.",
        'mots_cles': 'plage impression, options impression',
    },
    {
        'categorie': 'Productivité', 'niveau': 'avance', 'type': 'qcm',
        'enonce': "Quelle pratique améliore le plus la productivité lors de la création répétitive de documents similaires (factures, rapports) ?",
        'reponses': [
            {'texte': 'Créer et réutiliser un modèle (template)', 'correct': True},
            {'texte': 'Recréer chaque document depuis zéro', 'correct': False},
            {'texte': 'Copier un ancien email à chaque fois', 'correct': False},
            {'texte': 'Demander à un collègue de le refaire', 'correct': False},
        ],
        'explication': "Un modèle (template) préformaté avec la structure, les styles et les éléments récurrents déjà en place fait gagner un temps considérable et garantit une cohérence visuelle sur tous les documents produits.",
        'mots_cles': 'modèle, template, productivité bureautique',
    },
    {
        'categorie': 'Microsoft Excel', 'niveau': 'facile', 'type': 'vrai_faux',
        'enonce': "Dans Excel, la fonction MOYENNE() calcule la moyenne arithmétique des valeurs sélectionnées.",
        'reponses': [{'texte': 'Vrai', 'correct': True}, {'texte': 'Faux', 'correct': False}],
        'explication': "=MOYENNE(plage) additionne toutes les valeurs numériques de la plage sélectionnée et divise par leur nombre, ignorant automatiquement les cellules vides ou textuelles.",
        'mots_cles': 'MOYENNE, Excel, formule de base',
    },
    {
        'categorie': 'Gestion des fichiers', 'niveau': 'intermediaire', 'type': 'qcm',
        'enonce': "Quel est le principal risque de nommer ses fichiers « Document1 », « Document2 », « Nouveau document (2) » ?",
        'reponses': [
            {'texte': 'Impossible de retrouver rapidement le bon fichier, confusion et perte de temps', 'correct': True},
            {'texte': 'Le fichier sera automatiquement supprimé', 'correct': False},
            {'texte': 'Le fichier devient plus lourd', 'correct': False},
            {'texte': 'Aucun risque, c\'est une bonne pratique', 'correct': False},
        ],
        'explication': "Un nommage clair et structuré (ex: « Rapport_Ventes_Mars2026.xlsx ») permet de retrouver instantanément un fichier — une compétence essentielle d'organisation numérique en contexte professionnel.",
        'mots_cles': 'nommage fichiers, organisation, bonnes pratiques',
    },
    {
        'categorie': 'Microsoft Word', 'niveau': 'professionnel', 'type': 'correction_word',
        'enonce': "Un rapport professionnel de 15 pages n'a AUCUN style de titre appliqué (tout le texte utilise « Normal »), rendant la navigation difficile. Quelle est la conséquence principale et la correction recommandée ?",
        'reponses': [
            {'texte': 'Impossible de générer une table des matières automatique ni d\'utiliser le volet de navigation — appliquer les styles Titre 1/2/3 rétroactivement', 'correct': True},
            {'texte': 'Aucune conséquence, le document reste identique', 'correct': False},
            {'texte': 'Le document sera plus rapide à charger', 'correct': False},
            {'texte': 'Il faut absolument tout retaper', 'correct': False},
        ],
        'explication': "L'absence de styles de titre empêche toute automatisation (table des matières, navigation par le volet gauche, cohérence de mise en forme). Il suffit de sélectionner chaque titre existant et lui appliquer le style approprié — pas besoin de retaper le contenu.",
        'mots_cles': 'styles Word, structure document, correction professionnelle',
    },
]


class Command(BaseCommand):
    help = "Seed Batch 1 : 60 premières questions officielles (20 par module)"

    def handle(self, *args, **options):
        from academie.management.commands._helper_seed_idempotent import creer_question_si_absente

        modules = {
            'INT': (QUESTIONS_INTERNET, 'Internet, Recherche et Productivité'),
            'IA': (QUESTIONS_IA, 'Intelligence Artificielle'),
            'BUR': (QUESTIONS_BUREAUTIQUE, 'Bureautique Professionnelle'),
        }

        total_creees = 0
        total_ignorees = 0

        for code, (questions, nom_module) in modules.items():
            module = ModuleBanque.objects.filter(code=code).first()
            if not module:
                self.stdout.write(self.style.ERROR(f"❌ Module {code} introuvable"))
                continue

            for q in questions:
                categorie = CategorieBanque.objects.filter(module=module, nom=q['categorie']).first()
                if not categorie:
                    self.stdout.write(self.style.WARNING(f"⚠️ Catégorie '{q['categorie']}' introuvable pour {code}"))
                    continue

                try:
                    cree = creer_question_si_absente(module, categorie, q)
                    if cree:
                        total_creees += 1
                    else:
                        total_ignorees += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"❌ Erreur sur question '{q['enonce'][:50]}...' : {e}"))
                    continue

            self.stdout.write(self.style.SUCCESS(f"✅ {nom_module} : traité"))

        self.stdout.write(self.style.SUCCESS(
            f"\n🎉 BATCH 1 TERMINÉ : {total_creees} question(s) nouvellement créée(s), "
            f"{total_ignorees} déjà existante(s) ignorée(s) (aucun doublon)"
        ))