from django.db import models
from django_ckeditor_5.fields import CKEditor5Field
from simple_history.models import HistoricalRecords

class Ecole(models.Model):
    """Représente une École (catégorie de formations)."""

    nom = models.CharField(max_length=200)
    icone = models.CharField(max_length=10, default='🏫')
    description = models.TextField()
    ordre = models.IntegerField(default=0)

    class Meta:
        ordering = ['ordre', 'nom']
        verbose_name = 'École'
        verbose_name_plural = 'Écoles'

    def __str__(self):
        return f"{self.icone} {self.nom}"
    history = HistoricalRecords()   # ← AJOUTE À LA FIN, avant Meta/méthodes

    def progression_pour(self, utilisateur):
        """Calcule le % de progression d'un utilisateur sur cette formation."""
        if not utilisateur.is_authenticated:
            return 0

        toutes_lecons = Lecon.objects.filter(module__formation=self)
        total = toutes_lecons.count()

        if total == 0:
            return 0

        terminees = ProgressionLecon.objects.filter(
            utilisateur=utilisateur,
            lecon__in=toutes_lecons,
            terminee=True
        ).count()

        return round((terminees / total) * 100)
    
class Formation(models.Model):
    """Représente une formation proposée par BTA."""

    NIVEAUX = [
        ('debutant', 'Débutant'),
        ('intermediaire', 'Intermédiaire'),
        ('avance', 'Avancé'),
        ('professionnel', 'Professionnel'),
    ]

    ecole = models.ForeignKey(
        Ecole,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='formations'
    )
    nom = models.CharField(max_length=200)
    icone = models.CharField(max_length=10, default='📚')
    illustration = models.CharField(
        max_length=10,
        blank=True,
        default='',
        help_text="Émoji d'illustration moderne (ex: 💻, 📈, 🔐)"
    )
    description = models.TextField()
    duree_mois = models.IntegerField()
    prix = models.IntegerField()
    niveau = models.CharField(
        max_length=20,
        choices=NIVEAUX,
        default='debutant'
    )
    debouches = models.TextField(blank=True)
    prerequis = models.TextField(blank=True)
    certifications = models.TextField(blank=True)
    actif = models.BooleanField(default=True)
    message_partage = models.CharField(
        max_length=500,
        blank=True,
        default="",
        help_text="Message utilisé pour le partage automatique sur les réseaux sociaux. Laissez vide pour générer automatiquement."
    )
    date_creation = models.DateTimeField(auto_now_add=True)
    gratuit = models.BooleanField(
        default=False,
        help_text="Coche si c'est une formation gratuite (lead magnet)"
    )
    formation_upgrade = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='formations_gratuites',
        help_text="Formation payante recommandée à la fin de cette formation gratuite"
    )

    class Meta:
        ordering = ['nom']
        verbose_name = 'Formation'
        verbose_name_plural = 'Formations'
        indexes = [
            models.Index(fields=['actif']),
            models.Index(fields=['niveau']),
            models.Index(fields=['ecole', 'actif']),
        ]

    def __str__(self):
        return f"{self.icone} {self.nom} ({self.duree_mois} mois)"
    
    
    def progression_pour(self, utilisateur):
        """Calcule le % de progression d'un utilisateur sur cette formation."""
        if not utilisateur.is_authenticated:
            return 0

        toutes_lecons = Lecon.objects.filter(module__formation=self)
        total = toutes_lecons.count()

        if total == 0:
            return 0

        terminees = ProgressionLecon.objects.filter(
            utilisateur=utilisateur,
            lecon__in=toutes_lecons,
            terminee=True
        ).count()

        return round((terminees / total) * 100)
    history = HistoricalRecords()

class Inscription(models.Model):
    """Représente une demande d'inscription."""

    SUJETS = [
        ('inscription', "S'inscrire à une formation"),
        ('information', "Demande d'information"),
        ('partenariat', "Partenariat"),
        ('autre', "Autre"),
    ]

    prenom = models.CharField(max_length=100)
    nom = models.CharField(max_length=100)
    email = models.EmailField()
    telephone = models.CharField(max_length=20, blank=True)
    formation = models.ForeignKey(
        Formation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inscriptions'
    )
    sujet = models.CharField(
        max_length=20,
        choices=SUJETS,
        default='information'
    )
    message = models.TextField()
    date_inscription = models.DateTimeField(auto_now_add=True)
    traite = models.BooleanField(default=False)

    class Meta:
        ordering = ['-date_inscription']
        verbose_name = 'Inscription'
        verbose_name_plural = 'Inscriptions'

    def __str__(self):
        return f"{self.prenom} {self.nom} — {self.get_sujet_display()}"
    
class Quiz(models.Model):
    """Représente un quiz lié à une formation."""

    formation = models.ForeignKey(
        Formation,
        on_delete=models.CASCADE,
        related_name='quiz_set'
    )
    titre = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    actif = models.BooleanField(default=True)
    limite_temps_minutes = models.IntegerField(default=0, help_text="0 = pas de limite")
    tentatives_max = models.IntegerField(default=0, help_text="0 = illimité")
    melanger_questions = models.BooleanField(default=True)
    melanger_reponses = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_creation']
        verbose_name = 'Quiz'
        verbose_name_plural = 'Quiz'

    def __str__(self):
        return f"{self.titre} ({self.formation.nom})"

    def nombre_questions(self):
        return self.questions.count()

class Question(models.Model):
    """Représente une question à choix multiples dans un quiz."""

    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name='questions'
    )
    texte = models.TextField()
    choix_a = models.CharField(max_length=300)
    choix_b = models.CharField(max_length=300)
    choix_c = models.CharField(max_length=300)
    choix_d = models.CharField(max_length=300)
    bonne_reponse = models.CharField(
        max_length=1,
        choices=[('a', 'A'), ('b', 'B'), ('c', 'C'), ('d', 'D')]
    )
    explication = models.TextField(blank=True)
    ordre = models.IntegerField(default=0)

    class Meta:
        ordering = ['ordre']
        verbose_name = 'Question'
        verbose_name_plural = 'Questions'

    def __str__(self):
        return f"Q{self.ordre}: {self.texte[:50]}"


class ResultatQuiz(models.Model):
    """Enregistre le résultat d'un étudiant à un quiz."""

    utilisateur = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='resultats_quiz'
    )
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name='resultats'
    )
    score = models.IntegerField()  # nombre de bonnes réponses
    total_questions = models.IntegerField()
    date_passage = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_passage']
        verbose_name = 'Résultat de quiz'
        verbose_name_plural = 'Résultats de quiz'

    def __str__(self):
        return f"{self.utilisateur.username} - {self.quiz.titre} - {self.score}/{self.total_questions}"

    def pourcentage(self):
        if self.total_questions == 0:
            return 0
        return round((self.score / self.total_questions) * 100)
    
class Module(models.Model):
    """Un module = un chapitre/section d'une formation."""

    formation = models.ForeignKey(
        Formation,
        on_delete=models.CASCADE,
        related_name='modules'
    )
    titre = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    ordre = models.IntegerField(default=0)

    class Meta:
        ordering = ['ordre']
        verbose_name = 'Module'
        verbose_name_plural = 'Modules'

    def __str__(self):
        return f"{self.formation.nom} — Module {self.ordre}: {self.titre}"

    def nombre_lecons(self):
        return self.lecons.count()


class Lecon(models.Model):
    """Une leçon = un contenu pédagogique précis dans un module."""

    module = models.ForeignKey(
        Module,
        on_delete=models.CASCADE,
        related_name='lecons'
    )
    titre = models.CharField(max_length=200)
    resume = models.CharField(
        max_length=300,
        blank=True,
        help_text="Court résumé visible publiquement (sans connexion)"
    )
    contenu = CKEditor5Field(
    blank=True,
    config_name='default',
    help_text="Contenu complet du cours — visible uniquement aux étudiants connectés"
)
    duree_minutes = models.IntegerField(default=15)
    ordre = models.IntegerField(default=0)

    class Meta:
        ordering = ['ordre']
        verbose_name = 'Leçon'
        verbose_name_plural = 'Leçons'

    def __str__(self):
        return f"{self.module.titre} — {self.titre}"
        history = HistoricalRecords()   # ← AJOUTE À LA FIN

class ProgressionLecon(models.Model):
    """Suit la progression d'un étudiant sur une leçon."""

    utilisateur = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='progressions'
    )
    lecon = models.ForeignKey(
        Lecon,
        on_delete=models.CASCADE,
        related_name='progressions'
    )
    terminee = models.BooleanField(default=False)
    date_completion = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['utilisateur', 'lecon']
        verbose_name = 'Progression de leçon'
        verbose_name_plural = 'Progressions de leçons'

    def __str__(self):
        statut = "✅" if self.terminee else "⏳"
        return f"{statut} {self.utilisateur.username} — {self.lecon.titre}"
    
class Parcours(models.Model):
    """Un parcours professionnel = combinaison de plusieurs formations."""

    titre = models.CharField(max_length=200)
    icone = models.CharField(max_length=10, default='🎓')
    description = models.TextField(blank=True)
    duree_mois = models.IntegerField()
    prix = models.IntegerField()
    formations = models.ManyToManyField(
        Formation,
        related_name='parcours',
        blank=True
    )
    actif = models.BooleanField(default=True)
    ordre = models.IntegerField(default=0)

    class Meta:
        ordering = ['ordre', 'titre']
        verbose_name = 'Parcours professionnel'
        verbose_name_plural = 'Parcours professionnels'

    def __str__(self):
        return f"{self.icone} {self.titre} ({self.duree_mois} mois)"

    def nombre_formations(self):
        return self.formations.count()
    

class Sujet(models.Model):
    """Un sujet de discussion dans le forum."""

    CATEGORIES = [
        ('general', 'Général'),
        ('question', 'Question'),
        ('partage', 'Partage de projet'),
        ('aide', 'Demande d\'aide'),
        ('annonce', 'Annonce'),
    ]

    titre = models.CharField(max_length=300)
    contenu = CKEditor5Field(config_name='default')
    auteur = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='sujets_forum'
    )
    formation = models.ForeignKey(
        Formation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sujets_forum'
    )
    categorie = models.CharField(
        max_length=20,
        choices=CATEGORIES,
        default='general'
    )
    vues = models.IntegerField(default=0)
    epingle = models.BooleanField(default=False)
    resolu = models.BooleanField(default=False)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-epingle', '-date_creation']
        verbose_name = 'Sujet'
        verbose_name_plural = 'Sujets'

    def __str__(self):
        return self.titre

    def nombre_reponses(self):
        return self.reponses.count()

    def nombre_likes(self):
        return self.reactions.count()


class Reponse(models.Model):
    """Une réponse à un sujet du forum."""

    sujet = models.ForeignKey(
        Sujet,
        on_delete=models.CASCADE,
        related_name='reponses'
    )
    contenu = models.TextField()
    auteur = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='reponses_forum'
    )
    acceptee = models.BooleanField(default=False)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['date_creation']
        verbose_name = 'Réponse'
        verbose_name_plural = 'Réponses'

    def __str__(self):
        return f"Réponse de {self.auteur.username} sur {self.sujet.titre[:30]}"

    def nombre_likes(self):
        return self.reactions.count()


class Reaction(models.Model):
    """Un like sur un sujet ou une réponse."""

    utilisateur = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='reactions_forum'
    )
    sujet = models.ForeignKey(
        Sujet,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='reactions'
    )
    reponse = models.ForeignKey(
        Reponse,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='reactions'
    )
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [
            ['utilisateur', 'sujet'],
            ['utilisateur', 'reponse'],
        ]
        verbose_name = 'Réaction'
        verbose_name_plural = 'Réactions'

    def __str__(self):
        cible = self.sujet or self.reponse
        return f"❤️ {self.utilisateur.username} → {cible}"
    

class BadgeForum(models.Model):
    """Badge attribué à un membre du forum."""

    TYPES_BADGES = [
    # Badges Forum (existants)
    ('premier_post', '✍️ Premier Post'),
    ('premiere_reponse', '💬 Première Réponse'),
    ('solution_acceptee', '✅ Solution Acceptée'),
    ('dix_reponses', '🔥 10 Réponses'),
    ('cinquante_reponses', '⭐ 50 Réponses'),
    ('cent_likes', '❤️ 100 Likes reçus'),
    ('sujet_populaire', '🏆 Sujet Populaire'),

    # Badges Apprentissage (existants)
    ('premier_quiz', '🏅 Premier Quiz Réussi'),
    ('cinq_quiz', '📝 5 Quiz Réussis'),
    ('dix_heures', '⏰ 10 Heures d\'Apprentissage'),
    ('cinquante_heures', '🎯 50 Heures d\'Apprentissage'),
    ('premiere_formation', '🎓 Première Formation Complétée'),
    ('trois_formations', '🏆 3 Formations Complétées'),

    # Badges Apprentissage (nouveaux)
    ('premier_cours_termine', '🏅 Premier cours terminé'),
    ('cinq_lecons', '📚 5 leçons terminées'),
    ('dix_lecons', '📘 10 leçons terminées'),

    # Badges Compétences (existants)
    ('expert_python', '🐍 Expert Python'),
    ('expert_web', '🌐 Expert Web'),
    ('expert_data', '📊 Expert Données'),
    ('expert_cyber', '🔒 Expert Cybersécurité'),
    ('expert_design', '🎨 Expert Design'),

    # Badges Compétences (nouveaux)
    ('expert_excel', '📊 Expert Excel'),
    ('expert_ia', '🤖 Expert IA'),

    # Badges Projet (existants)
    ('projet_termine', '🚀 Projet Terminé'),
    ('trois_projets', '💼 3 Projets Livrés'),

    # Badges Social (existants)
    ('profile_complet', '👤 Profil Complété'),
    ('premier_certificat', '📜 Premier Certificat'),
    ('membre_actif', '🌟 Membre Actif'),
    ('membre_actif_forum', '💬 Membre actif du forum'),
]
    utilisateur = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='badges_forum'
    )
    type_badge = models.CharField(max_length=30, choices=TYPES_BADGES)
    date_obtention = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['utilisateur', 'type_badge']
        ordering = ['-date_obtention']
        verbose_name = 'Badge Forum'
        verbose_name_plural = 'Badges Forum'

    def __str__(self):
        return f"{self.get_type_badge_display()} — {self.utilisateur.username}"
    

class ProjetEtudiant(models.Model):
    """Projet réalisé par un étudiant pour son portfolio."""
    auteur = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='projets'
    )
    titre = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to='projets/', blank=True, null=True)
    lien = models.URLField(blank=True, null=True)
    technologies = models.CharField(max_length=300, blank=True, help_text="Ex: Python, Django, React")
    niveau_difficulte = models.CharField(
        max_length=20,
        choices=[('debutant','Débutant'),('intermediaire','Intermédiaire'),('avance','Avancé')],
        default='debutant', blank=True
    )
    competences_developpees = models.CharField(max_length=300, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_creation']
        verbose_name = 'Projet étudiant'
        verbose_name_plural = 'Projets étudiants'

    def __str__(self):
        return f"{self.titre} par {self.auteur.username}"
class Certificat(models.Model):
    """Certificat émis à un étudiant après complétion d'une formation."""
    utilisateur = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='certificats'
    )
    formation = models.ForeignKey(
        Formation,
        on_delete=models.CASCADE,
        related_name='certificats'
    )
    numero = models.CharField(max_length=20, unique=True)
    date_emission = models.DateTimeField(auto_now_add=True)
    verifie = models.BooleanField(default=False)  # pour usage futur

    class Meta:
        unique_together = ['utilisateur', 'formation']
        ordering = ['-date_emission']
        verbose_name = 'Certificat'
        verbose_name_plural = 'Certificats'

    def __str__(self):
        return f"Certificat {self.numero} - {self.utilisateur.username} ({self.formation.nom})"
    

class Notification(models.Model):
    """Notification envoyée à un utilisateur."""
    utilisateur = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    titre = models.CharField(max_length=200)
    message = models.TextField()
    lien = models.URLField(blank=True, default='')
    lue = models.BooleanField(default=False)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_creation']
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'

    def __str__(self):
        statut = "✓" if self.lue else "●"
        return f"{statut} {self.titre} — {self.utilisateur.username}"
    

class ProfilUtilisateur(models.Model):
    """Profil étendu de l'utilisateur avec XP et niveau."""
    utilisateur = models.OneToOneField(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='profil'
    )
    xp = models.IntegerField(default=0)
    streak = models.IntegerField(default=0)  # jours consécutifs
    derniere_activite = models.DateField(null=True, blank=True)

    NIVEAUX = [
        (0, 'Débutant'),
        (500, 'Explorateur'),
        (1000, 'Apprenant'),
        (2500, 'Praticien'),
        (5000, 'Professionnel'),
        (10000, 'Expert'),
        (20000, 'Master Tech'),
    ]

    class Meta:
        verbose_name = 'Profil utilisateur'
        verbose_name_plural = 'Profils utilisateurs'

    def __str__(self):
        return f"Profil de {self.utilisateur.username}"

    def niveau_actuel(self):
        """Retourne le nom du niveau actuel."""
        niveau = 'Débutant'
        for seuil, nom in sorted(self.NIVEAUX, reverse=True):
            if self.xp >= seuil:
                niveau = nom
                break
        return niveau

    def xp_prochain_niveau(self):
        """Retourne le XP nécessaire pour le prochain niveau."""
        for seuil, nom in sorted(self.NIVEAUX):
            if self.xp < seuil:
                return seuil
        return self.xp  # déjà au max

    def pourcentage_progression(self):
        """Pourcentage vers le prochain niveau."""
        prochain = self.xp_prochain_niveau()
        if prochain == self.xp:
            return 100
        # Trouver le seuil précédent
        seuils = [s for s, _ in self.NIVEAUX]
        seuil_actuel = max([s for s in seuils if s <= self.xp])
        return round(((self.xp - seuil_actuel) / (prochain - seuil_actuel)) * 100) if prochain > seuil_actuel else 0
    

class Article(models.Model):
    """Article ou guide publié dans la page Ressources."""

    CATEGORIES = [
        ('guide', '📖 Guide'),
        ('tutoriel', '🎓 Tutoriel'),
        ('actualite', '📰 Actualité'),
        ('conseil', '💡 Conseil'),
        ('outil', '🛠️ Outil'),
    ]

    titre = models.CharField(max_length=300)
    slug = models.SlugField(max_length=300, unique=True, blank=True)
    resume = models.TextField(max_length=500)
    contenu = CKEditor5Field(
        config_name='default',
        blank=True
    )
    categorie = models.CharField(
        max_length=20,
        choices=CATEGORIES,
        default='guide'
    )
    formation_liee = models.ForeignKey(
        Formation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='articles'
    )
    auteur = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='articles'
    )
    en_vedette = models.BooleanField(default=False)
    publie = models.BooleanField(default=False)
    temps_lecture = models.IntegerField(
        default=5,
        help_text="Temps de lecture estimé en minutes"
    )
    date_publication = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    # Champs SEO
    meta_titre = models.CharField(
        max_length=70, blank=True,
        help_text="Titre SEO (60-70 caractères recommandés)"
    )
    meta_description = models.CharField(
        max_length=160, blank=True,
        help_text="Description SEO (150-160 caractères recommandés)"
    )
    mots_cles = models.CharField(max_length=255, blank=True, help_text="Mots-clés séparés par des virgules")
    noindex = models.BooleanField(default=False, help_text="Empêcher l'indexation Google")
    class Meta:
        ordering = ['-en_vedette', '-date_publication']
        verbose_name = 'Article'
        verbose_name_plural = 'Articles'

    def __str__(self):
        return self.titre
        history = HistoricalRecords()   # ← AJOUTE À LA FIN

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.titre)
        super().save(*args, **kwargs)

    def temps_lecture_estime(self):
        """Calcule le temps de lecture basé sur le nombre de mots (200 mots/min)."""
        import re
        texte_brut = re.sub('<[^<]+?>', '', self.contenu or '')
        nb_mots = len(texte_brut.split())
        return max(1, round(nb_mots / 200))
class OutilRecommande(models.Model):
    """Outil numérique recommandé aux étudiants."""

    CATEGORIES = [
        ('developpement', '💻 Développement'),
        ('design', '🎨 Design'),
        ('ia', '🤖 Intelligence Artificielle'),
        ('productivite', '⚡ Productivité'),
        ('collaboration', '👥 Collaboration'),
        ('securite', '🔐 Sécurité'),
    ]

    nom = models.CharField(max_length=200)
    description = models.TextField(max_length=400)
    url = models.URLField()
    icone = models.CharField(max_length=10, default='🛠️')
    categorie = models.CharField(
        max_length=20,
        choices=CATEGORIES,
        default='developpement'
    )
    gratuit = models.BooleanField(default=True)
    recommande_par_bta = models.BooleanField(default=True)
    ordre = models.IntegerField(default=0)

    class Meta:
        ordering = ['ordre', 'nom']
        verbose_name = 'Outil recommandé'
        verbose_name_plural = 'Outils recommandés'

    def __str__(self):
        return f"{self.icone} {self.nom}"


class Temoignage(models.Model):
    """Témoignage d'un étudiant BTA."""

    prenom_nom = models.CharField(max_length=200)
    formation_suivie = models.ForeignKey(
        Formation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='temoignages'
    )
    texte = models.TextField()
    note = models.IntegerField(
        default=5,
        choices=[(i, f"{i} étoile{'s' if i > 1 else ''}") for i in range(1, 6)]
    )
    initiales = models.CharField(
        max_length=3,
        help_text="Ex: JRB pour Jean Raymond BELONY"
    )
    titre_professionnel = models.CharField(
        max_length=200,
        blank=True,
        help_text="Ex: Développeur Web Freelance"
    )
    en_vedette = models.BooleanField(default=False)
    approuve = models.BooleanField(default=False)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-en_vedette', '-date_creation']
        verbose_name = 'Témoignage'
        verbose_name_plural = 'Témoignages'

    def __str__(self):
        return f"{self.prenom_nom} — {self.note}⭐"