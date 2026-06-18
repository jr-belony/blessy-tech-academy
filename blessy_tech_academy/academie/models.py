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

    def __str__(self):
        return f"{self.icone} {self.nom} ({self.duree_mois} mois)"


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