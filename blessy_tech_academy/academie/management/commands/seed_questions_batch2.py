# ================================================
# SEED_QUESTIONS_BATCH2.PY — Deuxième lot de questions officielles BTA
# Usage : python manage.py seed_questions_batch2
# 45 questions (15 Internet, 15 IA, 15 Bureautique)
# Complète les catégories sous-représentées du Batch 1
# ================================================

from django.core.management.base import BaseCommand
from academie.models_banque import ModuleBanque, CategorieBanque, QuestionBanque


QUESTIONS_INTERNET = [
    {
        'categorie': 'Navigation Web', 'niveau': 'avance', 'type': 'qcm',
        'enonce': "À quoi sert le mode navigation privée d'un navigateur ?",
        'reponses': [
            {'texte': "Ne pas enregistrer l'historique, les cookies et les données de session localement", 'correct': True},
            {'texte': "Rendre l'utilisateur totalement anonyme sur Internet", 'correct': False},
            {'texte': "Bloquer tous les virus automatiquement", 'correct': False},
            {'texte': "Accélérer la connexion Internet", 'correct': False},
        ],
        'explication': "La navigation privée empêche l'enregistrement local (historique, cookies) mais NE rend PAS anonyme — le fournisseur d'accès Internet et les sites visités peuvent toujours identifier l'utilisateur.",
        'mots_cles': 'navigation privée, confidentialité, navigateur',
    },
    {
        'categorie': 'Recherche avancée', 'niveau': 'facile', 'type': 'qcm',
        'enonce': "Quel type de résultat privilégier pour une recherche d'information fiable sur un sujet scientifique ?",
        'reponses': [
            {'texte': 'Sites institutionnels, universitaires ou publications reconnues', 'correct': True},
            {'texte': 'Le premier résultat, peu importe la source', 'correct': False},
            {'texte': 'Les réseaux sociaux uniquement', 'correct': False},
            {'texte': 'Les forums anonymes', 'correct': False},
        ],
        'explication': "Pour une information fiable, privilégier les sources institutionnelles (.edu, .gouv), universitaires ou les publications reconnues plutôt que des sources non vérifiées.",
        'mots_cles': 'fiabilité source, recherche information, esprit critique',
    },
    {
        'categorie': 'Recherche avancée', 'niveau': 'professionnel', 'type': 'scenario_pro',
        'enonce': "Vous devez rédiger un rapport citant des statistiques économiques haïtiennes récentes. Quelle démarche de recherche est la plus rigoureuse ?",
        'reponses': [
            {'texte': 'Croiser plusieurs sources officielles (IHSI, Banque Mondiale) et noter la date de publication', 'correct': True},
            {'texte': 'Utiliser le premier chiffre trouvé sur un blog', 'correct': False},
            {'texte': 'Demander à une IA générative sans vérification', 'correct': False},
            {'texte': 'Estimer les chiffres soi-même', 'correct': False},
        ],
        'explication': "La rigueur professionnelle exige de croiser plusieurs sources officielles reconnues (IHSI pour Haïti, institutions internationales) et de toujours noter la date, car les statistiques économiques évoluent rapidement.",
        'mots_cles': 'rigueur recherche, sources officielles, statistiques',
    },
    {
        'categorie': 'Opérateurs de recherche', 'niveau': 'intermediaire', 'type': 'qcm',
        'enonce': "Quel opérateur permet de chercher un fichier PDF spécifique sur un sujet donné ?",
        'reponses': [
            {'texte': 'sujet filetype:pdf', 'correct': True}, {'texte': 'sujet type=pdf', 'correct': False},
            {'texte': 'sujet .pdf uniquement', 'correct': False}, {'texte': 'sujet format:pdf', 'correct': False},
        ],
        'explication': "L'opérateur « filetype: » restreint les résultats de recherche à un format de fichier précis (pdf, doc, xls...) — très utile pour trouver des documents officiels ou des rapports.",
        'mots_cles': 'filetype, opérateur recherche, documents',
    },
    {
        'categorie': 'Sécurité numérique', 'niveau': 'facile', 'type': 'qcm',
        'enonce': "Que signifie l'acronyme « VPN » ?",
        'reponses': [
            {'texte': 'Virtual Private Network (Réseau Privé Virtuel)', 'correct': True},
            {'texte': 'Very Personal Network', 'correct': False}, {'texte': 'Verified Public Node', 'correct': False},
            {'texte': 'Virtual Public Network', 'correct': False},
        ],
        'explication': "Un VPN (Réseau Privé Virtuel) chiffre la connexion Internet et masque l'adresse IP réelle, renforçant la confidentialité, notamment sur les réseaux Wi-Fi publics non sécurisés.",
        'mots_cles': 'VPN, sécurité réseau, confidentialité',
    },
    {
        'categorie': 'Sécurité numérique', 'niveau': 'avance', 'type': 'etude_cas',
        'enonce': "Un employé reçoit un SMS urgent prétendant venir de sa banque, demandant de cliquer sur un lien pour « débloquer son compte ». Comment nommer cette technique et quelle réaction adopter ?",
        'reponses': [
            {'texte': "C'est du « smishing » (phishing par SMS) — ne pas cliquer, contacter directement la banque via son numéro officiel", 'correct': True},
            {'texte': "C'est normal, cliquer immédiatement", 'correct': False},
            {'texte': "C'est un bug du téléphone", 'correct': False},
            {'texte': "Répondre au SMS pour demander des précisions", 'correct': False},
        ],
        'explication': "Le « smishing » est une variante du phishing par SMS. Les banques ne demandent jamais d'urgence par SMS de cliquer sur un lien — toujours contacter l'institution via ses canaux officiels connus.",
        'mots_cles': 'smishing, phishing SMS, vigilance',
    },
    {
        'categorie': 'Sécurité numérique', 'niveau': 'intermediaire', 'type': 'reponse_courte',
        'enonce': "Quel terme désigne un logiciel malveillant qui chiffre les fichiers d'une victime et exige une rançon pour les débloquer ?",
        'reponses': [],
        'reponse_texte_courte': 'rançongiciel|ransomware',
        'explication': "Un rançongiciel (ransomware) chiffre les fichiers de la victime et exige un paiement (souvent en cryptomonnaie) pour fournir la clé de déchiffrement — la meilleure protection reste des sauvegardes régulières hors ligne.",
        'mots_cles': 'ransomware, rançongiciel, cybersécurité',
    },
    {
        'categorie': 'Google Workspace', 'niveau': 'facile', 'type': 'qcm',
        'enonce': "Quelle application Google Workspace correspond à un tableur (feuilles de calcul) ?",
        'reponses': [
            {'texte': 'Google Sheets', 'correct': True}, {'texte': 'Google Docs', 'correct': False},
            {'texte': 'Google Slides', 'correct': False}, {'texte': 'Google Drive', 'correct': False},
        ],
        'explication': "Google Sheets est l'équivalent en ligne d'Excel — tableur collaboratif avec formules, graphiques et partage en temps réel.",
        'mots_cles': 'Google Sheets, tableur, Google Workspace',
    },
    {
        'categorie': 'Google Workspace', 'niveau': 'professionnel', 'type': 'scenario_pro',
        'enonce': "Votre équipe de 8 personnes doit co-rédiger un rapport en temps réel, avec des commentaires et suivi des modifications. Quelle configuration Google Docs recommandez-vous ?",
        'reponses': [
            {'texte': 'Partage en mode « Éditeur » pour l\'équipe, utilisation des commentaires et du mode suggestion pour tracer les changements', 'correct': True},
            {'texte': 'Envoyer le document par email à chaque personne séparément', 'correct': False},
            {'texte': 'Donner uniquement les droits « Lecteur »', 'correct': False},
            {'texte': 'Créer 8 copies du document', 'correct': False},
        ],
        'explication': "Le mode « Suggestion » de Google Docs (équivalent du suivi des modifications) permet de proposer des changements traçables sans écraser le travail des autres, idéal pour une co-rédaction structurée en équipe.",
        'mots_cles': 'mode suggestion, co-rédaction, gestion équipe',
    },
    {
        'categorie': 'Organisation des fichiers', 'niveau': 'avance', 'type': 'qcm',
        'enonce': "Pourquoi est-il recommandé d'éviter les espaces et accents dans les noms de fichiers destinés à être partagés en ligne ?",
        'reponses': [
            {'texte': 'Certains systèmes/URLs peuvent mal interpréter ces caractères et générer des erreurs de lien', 'correct': True},
            {'texte': "C'est une légende urbaine, aucun impact réel", 'correct': False},
            {'texte': 'Cela rend le fichier plus lourd', 'correct': False},
            {'texte': 'Cela ralentit l\'ordinateur', 'correct': False},
        ],
        'explication': "Les espaces sont souvent remplacés par « %20 » dans les URLs et certains systèmes ne gèrent pas bien les accents — utiliser des underscores ou tirets et éviter les accents évite des erreurs de liens cassés.",
        'mots_cles': 'nommage fichiers, compatibilité, bonnes pratiques web',
    },
    {
        'categorie': 'Collaboration', 'niveau': 'facile', 'type': 'vrai_faux',
        'enonce': "Un cloud (comme Google Drive) permet d'accéder à ses fichiers depuis n'importe quel appareil connecté à Internet.",
        'reponses': [{'texte': 'Vrai', 'correct': True}, {'texte': 'Faux', 'correct': False}],
        'explication': "C'est l'avantage principal du stockage cloud : les fichiers sont hébergés en ligne et accessibles depuis tout appareil connecté, avec les identifiants appropriés.",
        'mots_cles': 'cloud, accessibilité, Google Drive',
    },
    {
        'categorie': 'Collaboration', 'niveau': 'avance', 'type': 'qcm',
        'enonce': "Quelle est la meilleure pratique pour gérer les accès à un dossier partagé quand un collaborateur quitte l'équipe ?",
        'reponses': [
            {'texte': 'Révoquer immédiatement ses droits d\'accès au dossier', 'correct': True},
            {'texte': "Ne rien faire, ce n'est pas important", 'correct': False},
            {'texte': 'Supprimer tout le dossier partagé', 'correct': False},
            {'texte': 'Changer le mot de passe de tous les comptes', 'correct': False},
        ],
        'explication': "Révoquer promptement les accès d'un collaborateur qui quitte l'équipe est une pratique essentielle de sécurité de l'information — évite tout accès non autorisé après son départ.",
        'mots_cles': 'gestion des accès, sécurité collaborative, offboarding',
    },
    {
        'categorie': 'Productivité', 'niveau': 'intermediaire', 'type': 'qcm',
        'enonce': "Quel principe de gestion du temps consiste à traiter un email dès sa lecture (répondre, archiver ou planifier) plutôt que de le laisser en attente ?",
        'reponses': [
            {'texte': 'La règle des 2 minutes / Inbox Zero', 'correct': True}, {'texte': 'La méthode Pomodoro', 'correct': False},
            {'texte': 'La matrice Eisenhower', 'correct': False}, {'texte': 'Le multitâche', 'correct': False},
        ],
        'explication': "Le principe « Inbox Zero » (ou la règle des 2 minutes) consiste à traiter immédiatement chaque email plutôt que de le laisser s'accumuler — améliore significativement la productivité et réduit le stress numérique.",
        'mots_cles': 'gestion emails, Inbox Zero, productivité',
    },
    {
        'categorie': 'Navigation Web', 'niveau': 'intermediaire', 'type': 'qcm',
        'enonce': "Que se passe-t-il généralement quand vous videz le cache de votre navigateur ?",
        'reponses': [
            {'texte': 'Les fichiers temporaires stockés localement sont supprimés, les pages peuvent se recharger plus lentement au prochain accès', 'correct': True},
            {'texte': 'Tous vos mots de passe sont automatiquement changés', 'correct': False},
            {'texte': 'Votre ordinateur redémarre', 'correct': False},
            {'texte': 'Internet devient plus rapide définitivement', 'correct': False},
        ],
        'explication': "Le cache stocke temporairement des éléments de pages déjà visitées (images, scripts) pour accélérer les visites futures. Le vider libère de l'espace et résout parfois des problèmes d'affichage, mais ralentit temporairement le premier chargement.",
        'mots_cles': 'cache navigateur, maintenance, performance web',
    },
    {
        'categorie': 'Productivité', 'niveau': 'professionnel', 'type': 'scenario_pro',
        'enonce': "Votre équipe utilise 5 outils différents (email, chat, tableur partagé, agenda, stockage cloud) sans centralisation. Quelle amélioration structurelle recommandez-vous ?",
        'reponses': [
            {'texte': 'Adopter une suite intégrée (comme Google Workspace ou Microsoft 365) pour centraliser communication et documents', 'correct': True},
            {'texte': 'Ajouter un 6e outil séparé', 'correct': False},
            {'texte': 'Revenir au papier pour simplifier', 'correct': False},
            {'texte': 'Ne rien changer, ça fonctionne déjà', 'correct': False},
        ],
        'explication': "La dispersion d'outils non intégrés génère de la perte d'information et de temps. Une suite intégrée (Google Workspace, Microsoft 365) centralise communication, documents et agenda, réduisant les frictions organisationnelles.",
        'mots_cles': 'suite collaborative, centralisation outils, efficacité organisationnelle',
    },
]


QUESTIONS_IA = [
    {
        'categorie': 'Fondamentaux', 'niveau': 'avance', 'type': 'qcm',
        'enonce': "Quelle affirmation décrit le mieux le « Machine Learning » (apprentissage automatique) ?",
        'reponses': [
            {'texte': 'Une branche de l\'IA où le système apprend des motifs à partir de données, sans être explicitement programmé pour chaque cas', 'correct': True},
            {'texte': 'Un logiciel qui suit uniquement des instructions fixes codées manuellement', 'correct': False},
            {'texte': 'Un type de virus informatique', 'correct': False},
            {'texte': 'Une technique de sauvegarde de données', 'correct': False},
        ],
        'explication': "Le Machine Learning permet à un système d'apprendre à reconnaître des motifs à partir de grandes quantités de données, sans que chaque règle soit codée manuellement — c'est le fondement des IA génératives modernes.",
        'mots_cles': 'machine learning, apprentissage automatique, fondamentaux IA',
    },
    {
        'categorie': 'Fondamentaux', 'niveau': 'professionnel', 'type': 'qcm',
        'enonce': "Quelle est la différence essentielle entre une IA générative et un système expert traditionnel basé sur des règles fixes ?",
        'reponses': [
            {'texte': 'L\'IA générative apprend des motifs statistiques à partir de données, le système expert applique des règles logiques explicitement codées', 'correct': True},
            {'texte': 'Il n\'y a aucune différence', 'correct': False},
            {'texte': 'Le système expert est toujours plus récent', 'correct': False},
            {'texte': 'L\'IA générative ne peut traiter que des images', 'correct': False},
        ],
        'explication': "Un système expert applique des règles « SI...ALORS » définies par des humains. Une IA générative apprend des motifs statistiques complexes à partir de vastes ensembles de données, ce qui la rend plus flexible mais moins prévisible.",
        'mots_cles': 'système expert vs IA générative, distinction technique',
    },
    {
        'categorie': 'IA générative', 'niveau': 'avance', 'type': 'qcm',
        'enonce': "Pourquoi une IA générative peut-elle donner des réponses différentes à la MÊME question posée deux fois ?",
        'reponses': [
            {'texte': 'Un certain degré d\'aléatoire (température) est souvent intégré au modèle pour varier les réponses', 'correct': True},
            {'texte': 'C\'est toujours un bug logiciel', 'correct': False},
            {'texte': 'L\'IA change de version à chaque question', 'correct': False},
            {'texte': 'C\'est impossible, la réponse est toujours identique', 'correct': False},
        ],
        'explication': "Les IA génératives utilisent un paramètre de « température » qui introduit un degré contrôlé d'aléatoire dans le choix des mots, permettant des réponses variées et plus naturelles plutôt que toujours identiques.",
        'mots_cles': 'température, aléatoire IA, variabilité réponses',
    },
    {
        'categorie': 'Prompt Engineering', 'niveau': 'facile', 'type': 'qcm',
        'enonce': "Que signifie le terme « prompt » en intelligence artificielle ?",
        'reponses': [
            {'texte': "L'instruction ou question donnée à l'IA pour obtenir une réponse", 'correct': True},
            {'texte': 'Un type de virus informatique', 'correct': False},
            {'texte': 'Le nom d\'un logiciel spécifique', 'correct': False},
            {'texte': 'Une erreur système', 'correct': False},
        ],
        'explication': "Un « prompt » est simplement l'instruction, la question ou le texte fourni à une IA pour obtenir une réponse — la qualité du prompt influence directement la qualité de la réponse.",
        'mots_cles': 'prompt, définition, base IA',
    },
    {
        'categorie': 'Prompt Engineering', 'niveau': 'intermediaire', 'type': 'completer',
        'enonce': "Compléter : Assigner à l'IA un ______ précis (ex: « Tu es un expert-comptable ») avant la question aide souvent à obtenir une réponse plus adaptée au contexte souhaité.",
        'reponses': [],
        'reponse_texte_courte': 'rôle|persona',
        'explication': "Attribuer un « rôle » (technique dite du « persona prompting ») aide l'IA à adopter un ton, un vocabulaire et une perspective adaptés — une technique de prompt engineering efficace et simple à appliquer.",
        'mots_cles': 'persona prompting, rôle IA, technique prompt',
    },
    {
        'categorie': 'Éthique', 'niveau': 'avance', 'type': 'scenario_pro',
        'enonce': "Une entreprise utilise l'IA pour générer automatiquement des avis clients positifs sur ses produits. Quel est le problème éthique majeur ?",
        'reponses': [
            {'texte': 'Tromperie des consommateurs — des faux avis nuisent à la confiance et peuvent être illégaux', 'correct': True},
            {'texte': "Aucun problème, c'est du marketing normal", 'correct': False},
            {'texte': 'Le seul risque est technique, pas éthique', 'correct': False},
            {'texte': "C'est encouragé par la loi", 'correct': False},
        ],
        'explication': "Générer de faux avis clients est une pratique trompeuse, souvent illégale (législation sur la protection des consommateurs), qui nuit à la confiance du marché — un usage clairement contraire à l'éthique de l'IA.",
        'mots_cles': 'faux avis, éthique marketing, tromperie IA',
    },
    {
        'categorie': 'Éthique', 'niveau': 'professionnel', 'type': 'etude_cas',
        'enonce': "Un enseignant détecte qu'un devoir semble entièrement généré par IA sans déclaration. Quelle approche pédagogique est la plus constructive ?",
        'reponses': [
            {'texte': 'Discuter ouvertement avec l\'étudiant, expliquer l\'importance de la transparence et encadrer un usage responsable futur de l\'IA', 'correct': True},
            {'texte': 'Sanctionner immédiatement sans discussion', 'correct': False},
            {'texte': 'Ignorer complètement la situation', 'correct': False},
            {'texte': 'Interdire tout usage futur d\'ordinateur', 'correct': False},
        ],
        'explication': "Une approche pédagogique constructive privilégie le dialogue et l'éducation à un usage responsable et transparent de l'IA, plutôt qu'une sanction punitive pure — cohérent avec la philosophie « apprendre à démontrer ses compétences ».",
        'mots_cles': 'pédagogie IA, dialogue éducatif, usage responsable',
    },
    {
        'categorie': 'Vérification des réponses', 'niveau': 'facile', 'type': 'vrai_faux',
        'enonce': "Une IA générative peut se tromper même si sa réponse semble très confiante et bien rédigée.",
        'reponses': [{'texte': 'Vrai', 'correct': True}, {'texte': 'Faux', 'correct': False}],
        'explication': "C'est vrai — et c'est justement le piège : le ton assuré d'une IA n'est en rien une garantie d'exactitude. La vérification systématique reste indispensable, particulièrement pour des faits, chiffres ou dates précis.",
        'mots_cles': 'fiabilité, esprit critique, vérification IA',
    },
    {
        'categorie': 'Vérification des réponses', 'niveau': 'professionnel', 'type': 'analyse_prompt_ia',
        'enonce': "Une IA cite « une étude de l'Université de Paris de 2019 » pour justifier une affirmation, sans lien ni référence précise. Quelle démarche professionnelle adopter ?",
        'reponses': [
            {'texte': 'Tenter de retrouver cette étude via une recherche indépendante ; si introuvable, considérer l\'affirmation comme non vérifiée', 'correct': True},
            {'texte': 'Faire confiance car le nom sonne académique et sérieux', 'correct': False},
            {'texte': 'Citer directement cette référence sans vérification dans son propre rapport', 'correct': False},
            {'texte': 'Ignorer complètement l\'affirmation sans chercher', 'correct': False},
        ],
        'explication': "Les IA peuvent halluciner des références académiques plausibles mais inexistantes. Une référence non vérifiable indépendamment ne doit jamais être citée telle quelle dans un document professionnel ou académique.",
        'mots_cles': 'hallucination référence, vérification académique, rigueur',
    },
    {
        'categorie': 'Cas professionnels', 'niveau': 'facile', 'type': 'qcm',
        'enonce': "Comment une IA peut-elle aider un employé à préparer une réunion ?",
        'reponses': [
            {'texte': 'En résumant des documents longs ou en proposant un ordre du jour structuré', 'correct': True},
            {'texte': 'En remplaçant complètement la présence humaine', 'correct': False},
            {'texte': 'En prenant les décisions finales à la place de l\'équipe', 'correct': False},
            {'texte': 'Elle ne peut pas être utile pour cela', 'correct': False},
        ],
        'explication': "L'IA excelle pour synthétiser rapidement des informations (résumés, ordres du jour, comptes-rendus) — un gain de temps utile en préparation de réunion, tout en laissant les décisions aux humains.",
        'mots_cles': 'assistance réunion, productivité IA, cas d\'usage',
    },
    {
        'categorie': 'Automatisation', 'niveau': 'intermediaire', 'type': 'qcm',
        'enonce': "Quel terme désigne l'enchaînement automatique de plusieurs tâches numériques sans intervention manuelle répétée (ex: recevoir un email → créer une tâche → notifier l'équipe) ?",
        'reponses': [
            {'texte': 'Un workflow automatisé', 'correct': True}, {'texte': 'Un antivirus', 'correct': False},
            {'texte': 'Un pare-feu', 'correct': False}, {'texte': 'Une sauvegarde', 'correct': False},
        ],
        'explication': "Un workflow automatisé (via des outils comme Zapier, Make, ou les automatisations natives de certains logiciels) enchaîne plusieurs actions déclenchées automatiquement, réduisant les tâches manuelles répétitives.",
        'mots_cles': 'workflow, automatisation, efficacité',
    },
    {
        'categorie': 'IA générative', 'niveau': 'facile', 'type': 'qcm',
        'enonce': "Quel outil d'IA générative est spécialisé dans la création d'images à partir d'une description textuelle ?",
        'reponses': [
            {'texte': 'Midjourney ou DALL-E', 'correct': True}, {'texte': 'Excel', 'correct': False},
            {'texte': 'Gmail', 'correct': False}, {'texte': 'Zoom', 'correct': False},
        ],
        'explication': "Midjourney et DALL-E sont des IA génératives spécialisées dans la création d'images à partir de descriptions textuelles (« text-to-image »).",
        'mots_cles': 'génération image, Midjourney, DALL-E',
    },
    {
        'categorie': 'Cas professionnels', 'niveau': 'avance', 'type': 'scenario_pro',
        'enonce': "Un service client reçoit 500 messages similaires par jour. Comment l'IA peut-elle améliorer ce processus SANS supprimer la relation humaine essentielle ?",
        'reponses': [
            {'texte': 'Un chatbot IA traite les questions simples et répétitives, tout en transférant les cas complexes ou sensibles à un agent humain', 'correct': True},
            {'texte': 'Remplacer complètement le service client par un chatbot', 'correct': False},
            {'texte': 'Ignorer les messages en trop grand nombre', 'correct': False},
            {'texte': 'Répondre uniquement une fois par semaine', 'correct': False},
        ],
        'explication': "Le modèle hybride (chatbot pour les questions fréquentes/simples + humain pour les cas complexes ou émotionnellement sensibles) optimise l'efficacité tout en préservant la qualité de la relation client là où elle compte le plus.",
        'mots_cles': 'chatbot service client, hybride humain-IA, cas d\'usage avancé',
    },
    {
        'categorie': 'Automatisation', 'niveau': 'professionnel', 'type': 'etude_cas',
        'enonce': "Une PME automatise entièrement sa facturation avec l'IA sans aucune supervision humaine. Quel risque principal cette entreprise prend-elle ?",
        'reponses': [
            {'texte': 'Des erreurs non détectées (montants, destinataires) pouvant avoir des conséquences financières ou légales importantes', 'correct': True},
            {'texte': 'Aucun risque, l\'automatisation est toujours fiable à 100%', 'correct': False},
            {'texte': 'Les factures seront plus lentes à générer', 'correct': False},
            {'texte': 'Les clients ne recevront jamais leurs factures', 'correct': False},
        ],
        'explication': "Toute automatisation critique (facturation, paiements) nécessite une supervision humaine minimale (contrôle périodique, seuils d'alerte) pour détecter les erreurs avant qu'elles n'aient des conséquences financières ou légales.",
        'mots_cles': 'supervision automatisation, risques IA, gouvernance',
    },
    {
        'categorie': 'Fondamentaux', 'niveau': 'intermediaire', 'type': 'vrai_faux',
        'enonce': "Toutes les intelligences artificielles sont des IA génératives.",
        'reponses': [{'texte': 'Vrai', 'correct': False}, {'texte': 'Faux', 'correct': True}],
        'explication': "C'est faux : l'IA générative n'est qu'une CATÉGORIE d'IA parmi d'autres (IA de classification, de recommandation, de reconnaissance d'image, de robotique...). Le terme « IA » est beaucoup plus large.",
        'mots_cles': 'catégories IA, terminologie, distinction',
    },
]


QUESTIONS_BUREAUTIQUE = [
    {
        'categorie': 'Microsoft Excel', 'niveau': 'intermediaire', 'type': 'qcm',
        'enonce': "Quelle fonction Excel compte le nombre de cellules répondant à une condition (ex: compter les ventes > 1000) ?",
        'reponses': [
            {'texte': 'NB.SI', 'correct': True}, {'texte': 'SOMME.SI', 'correct': False},
            {'texte': 'MOYENNE.SI', 'correct': False}, {'texte': 'RECHERCHEV', 'correct': False},
        ],
        'explication': "NB.SI (COUNTIF) compte le nombre de cellules répondant à un critère donné. SOMME.SI additionne les valeurs répondant à un critère — souvent confondues, elles ont des usages distincts.",
        'mots_cles': 'NB.SI, COUNTIF, Excel conditionnel',
    },
    {
        'categorie': 'Microsoft Excel', 'niveau': 'professionnel', 'type': 'qcm',
        'enonce': "Quelle est la différence entre une référence de cellule relative (A1) et absolue ($A$1) dans une formule Excel ?",
        'reponses': [
            {'texte': 'La référence absolue reste fixe lors de la copie de la formule, la relative s\'ajuste automatiquement', 'correct': True},
            {'texte': 'Aucune différence pratique', 'correct': False},
            {'texte': 'La référence absolue est toujours plus rapide à calculer', 'correct': False},
            {'texte': 'La référence relative ne fonctionne que sur la première ligne', 'correct': False},
        ],
        'explication': "Le symbole $ fige une référence (ligne, colonne ou les deux) pour qu'elle ne change pas lors de la copie/glissement d'une formule — essentiel pour des calculs impliquant une valeur fixe (ex: un taux de TVA constant).",
        'mots_cles': 'référence absolue, référence relative, formules Excel',
    },
    {
        'categorie': 'Microsoft Excel', 'niveau': 'facile', 'type': 'qcm',
        'enonce': "Quel symbole doit précéder toute formule dans Excel ?",
        'reponses': [
            {'texte': '=', 'correct': True}, {'texte': '#', 'correct': False},
            {'texte': '@', 'correct': False}, {'texte': '&', 'correct': False},
        ],
        'explication': "Le signe égal (=) indique à Excel que le contenu de la cellule est une formule à calculer, et non simplement du texte ou un nombre statique.",
        'mots_cles': 'formule Excel, syntaxe de base',
    },
    {
        'categorie': 'Microsoft Word', 'niveau': 'intermediaire', 'type': 'qcm',
        'enonce': "Quelle fonctionnalité Word permet de fusionner une lettre type avec une liste de destinataires (nom, adresse) issue d'un tableur ?",
        'reponses': [
            {'texte': 'Le publipostage (Mailing/Mail Merge)', 'correct': True}, {'texte': 'Le suivi des modifications', 'correct': False},
            {'texte': 'Les styles rapides', 'correct': False}, {'texte': 'Le mode plan', 'correct': False},
        ],
        'explication': "Le publipostage permet de générer automatiquement des dizaines/centaines de documents personnalisés (lettres, étiquettes, emails) à partir d'un modèle et d'une source de données (Excel, contacts).",
        'mots_cles': 'publipostage, mailing, personnalisation documents',
    },
    {
        'categorie': 'Microsoft Word', 'niveau': 'avance', 'type': 'qcm',
        'enonce': "Comment insérer une note de bas de page dans Word ?",
        'reponses': [
            {'texte': 'Références > Insérer une note de bas de page', 'correct': True},
            {'texte': 'Taper le texte manuellement en bas de chaque page', 'correct': False},
            {'texte': 'Insertion > Zone de texte', 'correct': False},
            {'texte': 'Ce n\'est pas possible dans Word', 'correct': False},
        ],
        'explication': "L'onglet Références > Insérer une note de bas de page ajoute automatiquement une numérotation cohérente et gère le placement en bas de page, même si le contenu du document change.",
        'mots_cles': 'note de bas de page, références, Word avancé',
    },
    {
        'categorie': 'Microsoft PowerPoint', 'niveau': 'facile', 'type': 'qcm',
        'enonce': "Quel est le rôle du « mode présentateur » dans PowerPoint ?",
        'reponses': [
            {'texte': "Afficher les notes du présentateur sur son écran tout en montrant uniquement le diaporama à l'audience", 'correct': True},
            {'texte': 'Ajouter automatiquement des animations', 'correct': False},
            {'texte': 'Imprimer la présentation', 'correct': False},
            {'texte': 'Compter le nombre de diapositives', 'correct': False},
        ],
        'explication': "Le mode présentateur affiche sur l'écran du présentateur les notes, la diapositive suivante et un chronomètre, tandis que l'audience ne voit que le diaporama en plein écran — un outil précieux pour des présentations professionnelles fluides.",
        'mots_cles': 'mode présentateur, présentation orale, PowerPoint',
    },
    {
        'categorie': 'Microsoft PowerPoint', 'niveau': 'professionnel', 'type': 'amelioration_ppt',
        'enonce': "Une présentation commerciale utilise 6 polices différentes et 8 couleurs différentes sur 10 diapositives. Quel est le problème principal et la correction ?",
        'reponses': [
            {'texte': 'Manque de cohérence visuelle nuisant au professionnalisme — limiter à 2 polices et une palette de 3-4 couleurs maximum via le masque des diapositives', 'correct': True},
            {'texte': 'Aucun problème, la diversité est positive', 'correct': False},
            {'texte': 'Il faut ajouter encore plus de couleurs', 'correct': False},
            {'texte': 'Le nombre de diapositives est le vrai problème', 'correct': False},
        ],
        'explication': "La cohérence visuelle (police limitée, palette de couleurs restreinte, alignement avec la charte de l'entreprise) renforce le professionnalisme perçu et la lisibilité — principe fondamental du design de présentation.",
        'mots_cles': 'cohérence visuelle, charte graphique, design présentation',
    },
    {
        'categorie': 'Gestion des fichiers', 'niveau': 'avance', 'type': 'qcm',
        'enonce': "Quelle est la différence principale entre « Enregistrer » et « Enregistrer sous » dans un logiciel Office ?",
        'reponses': [
            {'texte': '« Enregistrer sous » permet de créer une copie sous un nouveau nom/emplacement, « Enregistrer » écrase le fichier existant', 'correct': True},
            {'texte': 'Aucune différence', 'correct': False},
            {'texte': '« Enregistrer sous » supprime le fichier original', 'correct': False},
            {'texte': '« Enregistrer » crée toujours une copie', 'correct': False},
        ],
        'explication': "« Enregistrer sous » (Ctrl+Maj+S) ouvre une boîte de dialogue pour choisir un nouveau nom/emplacement/format, créant une copie distincte. « Enregistrer » (Ctrl+S) écrase simplement le fichier existant avec les modifications actuelles.",
        'mots_cles': 'enregistrer sous, gestion versions, bonnes pratiques',
    },
    {
        'categorie': 'Raccourcis clavier', 'niveau': 'intermediaire', 'type': 'qcm',
        'enonce': "Quel raccourci permet de rechercher un mot précis dans un long document Word ou une feuille Excel ?",
        'reponses': [
            {'texte': 'Ctrl + F', 'correct': True}, {'texte': 'Ctrl + R', 'correct': False},
            {'texte': 'Ctrl + L', 'correct': False}, {'texte': 'Ctrl + E', 'correct': False},
        ],
        'explication': "Ctrl+F (Find) ouvre la barre de recherche dans quasiment tous les logiciels — un raccourci universel extrêmement utile pour naviguer rapidement dans un document long.",
        'mots_cles': 'Ctrl+F, recherche document, raccourci universel',
    },
    {
        'categorie': 'Raccourcis clavier', 'niveau': 'avance', 'type': 'qcm',
        'enonce': "Dans Excel, quel raccourci sélectionne instantanément toute une colonne de données jusqu'à la dernière cellule remplie ?",
        'reponses': [
            {'texte': 'Ctrl + Maj + Flèche bas', 'correct': True}, {'texte': 'Ctrl + A', 'correct': False},
            {'texte': 'Alt + Flèche bas', 'correct': False}, {'texte': 'F4', 'correct': False},
        ],
        'explication': "Ctrl+Maj+Flèche (dans la direction voulue) sélectionne rapidement une plage continue de données jusqu'à la première cellule vide rencontrée — un gain de temps précieux sur de grands tableaux.",
        'mots_cles': 'sélection rapide, Excel avancé, raccourcis productivité',
    },
    {
        'categorie': 'Mise en page', 'niveau': 'facile', 'type': 'qcm',
        'enonce': "Quelle orientation de page choisir pour un document contenant un tableau très large ?",
        'reponses': [
            {'texte': 'Paysage (horizontal)', 'correct': True}, {'texte': 'Portrait (vertical)', 'correct': False},
            {'texte': 'Carrée', 'correct': False}, {'texte': 'Aucune importance', 'correct': False},
        ],
        'explication': "L'orientation Paysage offre plus de largeur — idéale pour les tableaux larges, graphiques étendus ou présentations, évitant que le contenu soit coupé ou illisible.",
        'mots_cles': 'orientation page, paysage, mise en page',
    },
    {
        'categorie': 'Mise en page', 'niveau': 'professionnel', 'type': 'qcm',
        'enonce': "Un rapport professionnel doit avoir des marges différentes pour l'impression recto-verso avec reliure. Quelle option Word utiliser ?",
        'reponses': [
            {'texte': 'Marges « Miroir » (option Pages dans Mise en page)', 'correct': True},
            {'texte': 'Marges normales identiques partout', 'correct': False},
            {'texte': 'Aucune option n\'existe pour cela', 'correct': False},
            {'texte': 'Insérer des espaces manuellement', 'correct': False},
        ],
        'explication': "Les marges « Miroir » ajustent automatiquement les marges intérieures/extérieures selon que la page est paire ou impaire — essentiel pour les documents reliés (livres, rapports imprimés recto-verso).",
        'mots_cles': 'marges miroir, impression professionnelle, reliure',
    },
    {
        'categorie': 'Impression', 'niveau': 'avance', 'type': 'qcm',
        'enonce': "Pourquoi imprimer un long tableau Excel peut-il produire des pages coupées de façon illisible ?",
        'reponses': [
            {'texte': 'Les sauts de page automatiques ne correspondent pas à la largeur du tableau — utiliser l\'aperçu des sauts de page pour ajuster', 'correct': True},
            {'texte': "C'est un bug irréparable d'Excel", 'correct': False},
            {'texte': 'L\'imprimante est en panne', 'correct': False},
            {'texte': 'Il faut changer d\'ordinateur', 'correct': False},
        ],
        'explication': "Excel place des sauts de page automatiques qui ignorent souvent la logique du tableau. L'onglet Affichage > Aperçu des sauts de page permet de les ajuster manuellement, ou d'utiliser « Ajuster » dans Mise en page pour tenir sur une largeur de page.",
        'mots_cles': 'sauts de page Excel, impression tableau, diagnostic',
    },
    {
        'categorie': 'Productivité', 'niveau': 'facile', 'type': 'qcm',
        'enonce': "Quel avantage offre l'utilisation de styles (Titre, Sous-titre) plutôt que de mettre le texte en gras/grande taille manuellement ?",
        'reponses': [
            {'texte': 'Cohérence automatique et possibilité de modifier tout le document en changeant un seul style', 'correct': True},
            {'texte': 'Aucun avantage réel', 'correct': False},
            {'texte': 'Cela rend le fichier plus lourd', 'correct': False},
            {'texte': 'Cela ralentit l\'ordinateur', 'correct': False},
        ],
        'explication': "Utiliser des styles prédéfinis permet de modifier l'apparence de TOUS les titres d'un document en une seule modification du style, garantissant cohérence et gain de temps considérable sur les documents longs.",
        'mots_cles': 'styles, cohérence document, efficacité mise en forme',
    },
    {
        'categorie': 'Gestion des fichiers', 'niveau': 'professionnel', 'type': 'scenario_pro',
        'enonce': "Une entreprise perd un rapport important car le fichier n'existait qu'en un seul exemplaire sur un ordinateur qui est tombé en panne. Quelle pratique aurait évité ce problème ?",
        'reponses': [
            {'texte': 'Sauvegarde régulière sur le cloud (Drive, OneDrive) en plus du stockage local', 'correct': True},
            {'texte': 'Imprimer systématiquement tous les documents', 'correct': False},
            {'texte': 'Ne jamais utiliser d\'ordinateur', 'correct': False},
            {'texte': 'Ce risque est impossible à éviter', 'correct': False},
            
        ],
        'explication': "La règle de sauvegarde 3-2-1 (3 copies, 2 supports différents, 1 hors site) reste la meilleure protection contre la perte de données — le cloud offre une solution simple et accessible pour la majorité des besoins professionnels courants.",
        'mots_cles': 'sauvegarde, règle 3-2-1, prévention perte de données',
    },
]


class Command(BaseCommand):
    help = "Seed Batch 2 : 45 questions supplémentaires (15 par module) — 105/150 au total"

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

        self.stdout.write(self.style.SUCCESS(f"\n🎉 BATCH 2 TERMINÉ : {total_creees} questions créées (105/150 au total)"))