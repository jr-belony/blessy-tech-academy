from django.db import models


class Formation(models.Model):
    """Représente une formation proposée par BTA."""

    # Champs de base
    nom = models.CharField(max_length=200)
    icone = models.CharField(max_length=10, default='📚')
    description = models.TextField()
    duree_mois = models.IntegerField()
    prix = models.IntegerField()
    actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['nom']           # tri alphabétique par défaut
        verbose_name = 'Formation'
        verbose_name_plural = 'Formations'

    def __str__(self):
        return f"{self.nom} ({self.duree_mois} mois)"


class Inscription(models.Model):
    """Représente une demande d'inscription."""

    # Informations personnelles
    prenom = models.CharField(max_length=100)
    nom = models.CharField(max_length=100)
    email = models.EmailField()
    telephone = models.CharField(max_length=20, blank=True)

    # Formation choisie (clé étrangère)
    formation = models.ForeignKey(
        Formation,
        on_delete=models.SET_NULL,
        null=True,
        related_name='inscriptions'
    )

    # Sujet et message
    sujet = models.CharField(max_length=200)
    message = models.TextField()

    # Métadonnées
    date_inscription = models.DateTimeField(auto_now_add=True)
    traite = models.BooleanField(default=False)

    class Meta:
        ordering = ['-date_inscription']   # plus récent en premier
        verbose_name = 'Inscription'
        verbose_name_plural = 'Inscriptions'

    def __str__(self):
        return f"{self.prenom} {self.nom} — {self.formation}"