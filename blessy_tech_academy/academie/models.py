from django.db import models


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
    date_creation = models.DateTimeField(auto_now_add=True)

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
    
    # academie/models.py — ajoute ces 2 classes À LA FIN du fichier

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
    contenu = models.TextField(
        blank=True,
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