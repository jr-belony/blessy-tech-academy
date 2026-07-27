# ================================================
# FORUM/MODELS.PY — Sujet, Reponse, Reaction, BadgeForum
# app_label='academie' → tables existantes academie_*
# ================================================
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.conf import settings


class Sujet(models.Model):
    CATEGORIES = [
        ('general', 'Général'),
        ('aide', 'Aide'),
        ('projet', 'Projet'),
        ('emploi', 'Emploi'),
    ]
    titre = models.CharField(max_length=200)
    contenu = models.TextField()
    auteur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sujets')
    formation = models.ForeignKey('academie.Formation', on_delete=models.SET_NULL, null=True, blank=True)
    categorie = models.CharField(max_length=20, choices=CATEGORIES, default='general')
    vues = models.IntegerField(default=0)
    epingle = models.BooleanField(default=False)
    resolu = models.BooleanField(default=False)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'academie'
        db_table = 'academie_sujet'
        ordering = ['-epingle', '-date_creation']
        indexes = [
            models.Index(fields=['categorie', 'date_creation']),
            models.Index(fields=['formation']),
        ]
        verbose_name = "Sujet"
        verbose_name_plural = "Sujets"

    def __str__(self):
        return self.titre

    @property
    def nombre_reponses(self):
        return self.reponses.count()

    @property
    def nombre_likes(self):
        ct = ContentType.objects.get_for_model(Sujet)
        return Reaction.objects.filter(content_type=ct, object_id=self.id).count()


class Reponse(models.Model):
    sujet = models.ForeignKey(Sujet, on_delete=models.CASCADE, related_name='reponses')
    contenu = models.TextField()
    auteur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    acceptee = models.BooleanField(default=False)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'academie'
        db_table = 'academie_reponse'
        ordering = ['date_creation']
        verbose_name = "Réponse"
        verbose_name_plural = "Réponses"


class Reaction(models.Model):
    utilisateur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    # Relations directes pour les contraintes d'unicité
    sujet = models.ForeignKey(Sujet, on_delete=models.CASCADE, null=True, blank=True)
    reponse = models.ForeignKey(Reponse, on_delete=models.CASCADE, null=True, blank=True)
    # Relation générique pour supporter d'autres types de contenu
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveBigIntegerField(null=True, blank=True)
    cible = GenericForeignKey('content_type', 'object_id')
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'academie'
        db_table = 'academie_reaction'
        # Contraintes d'unicité pour éviter les doublons (un utilisateur ne peut réagir qu'une fois par cible)
        unique_together = [
            ['utilisateur', 'sujet'],
            ['utilisateur', 'reponse'],
        ]
        verbose_name = "Réaction"
        verbose_name_plural = "Réactions"


class BadgeForum(models.Model):
    TYPES_BADGE = [
        ('premier_post', '✍️ Premier Post'),
        ('premiere_reponse', '💬 Première Réponse'),
        ('solution_acceptee', '✅ Solution Acceptée'),
        ('actif_10', '🔥 10 Réponses'),
        ('expert_50', '⭐ 50 Réponses'),
        ('populaire_100', '❤️ 100 Likes'),
    ]
    utilisateur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='badges_forum')
    type_badge = models.CharField(max_length=30, choices=TYPES_BADGE)
    date_obtention = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'academie'
        db_table = 'academie_badgeforum'
        unique_together = ['utilisateur', 'type_badge']
        ordering = ['-date_obtention']
        verbose_name = "Badge Forum"
        verbose_name_plural = "Badges Forum"