# ================================================
# USERS/MODELS.PY — Modèles utilisateur extraits d'academie
# IMPORTANT : Meta.app_label reste 'academie' pour préserver 
# la table PostgreSQL existante (academie_profilutilisateur, etc.)
# ================================================

from django.db import models
from django.utils import timezone
import uuid


class ProfilUtilisateur(models.Model):
    """Profil étendu de l'utilisateur avec XP et niveau."""

    utilisateur = models.OneToOneField("auth.User", on_delete=models.CASCADE, related_name="profil")
    xp = models.IntegerField(default=0)
    streak = models.IntegerField(default=0)  # jours consécutifs
    derniere_activite = models.DateField(null=True, blank=True)
    # === RBAC — Rôle utilisateur ===
    ROLE_CHOICES = [
        ("etudiant", "Étudiant"),
        ("parent", "Parent"),
        ("formateur", "Formateur"),
        ("asst_formateur", "Assistant Formateur"),
        ("resp_academique", "Responsable Académique"),
        ("examinateur", "Examinateur"),
        ("correcteur", "Correcteur"),
        ("marketing", "Marketing"),
        ("support", "Support"),
        ("finance", "Finance"),
        ("direction", "Direction"),
        ("admin", "Administrateur"),
        ("super_admin", "Super Administrateur"),
        ("api_client", "API Client"),
    ]
    role = models.CharField(max_length=30, choices=ROLE_CHOICES, default="etudiant")
    # === Multi-appartenance Academie (multi-tenant) ===
    academies = models.ManyToManyField(
        "Academie",
        blank=True,
        related_name="membres",
        help_text="Académies auxquelles cet utilisateur a accès (étudiant multi-académie ou formateur multi-académie)",
    )
    # === Champs additionnels ===
    bio_formateur = models.TextField(blank=True)
    specialites = models.CharField(
        max_length=300, blank=True, help_text="Séparées par des virgules"
    )
    taux_remuneration = models.DecimalField(
        max_digits=5, decimal_places=2, default=0, help_text="% des ventes reversé"
    )
    telephone = models.CharField(max_length=20, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    NIVEAUX = [
        (0, "Débutant"),
        (500, "Explorateur"),
        (1000, "Apprenant"),
        (2500, "Praticien"),
        (5000, "Professionnel"),
        (10000, "Expert"),
        (20000, "Master Tech"),
    ]

    # === Méthodes de vérification rapide ===
    def peut_voir_finance(self):
        return self.role in ["admin", "super_admin", "finance", "direction"]

    def peut_moderer_forum(self):
        return self.role in ["admin", "super_admin", "support"]

    def peut_gerer_formations(self):
        return self.role in ["admin", "super_admin", "formateur", "resp_academique"]

    def peut_voir_crm(self):
        return self.role in ["admin", "super_admin", "marketing", "support", "direction"]

    class Meta:
        app_label = 'academie'
        db_table = 'academie_profilutilisateur'
        verbose_name = "Profil utilisateur"
        verbose_name_plural = "Profils utilisateurs"

    def __str__(self):
        return f"Profil de {self.utilisateur.username}"

    def niveau_actuel(self):
        """Retourne le nom du niveau actuel."""
        niveau = "Débutant"
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
        return (
            round(((self.xp - seuil_actuel) / (prochain - seuil_actuel)) * 100)
            if prochain > seuil_actuel
            else 0
        )


class LogAudit(models.Model):
    ACTIONS = [
        ('validation_paiement', 'Validation de paiement'), ('suppression', 'Suppression'),
        ('modification_role', 'Modification de rôle'), ('remboursement', 'Remboursement'),
        ('publication', 'Publication de contenu'), ('connexion_admin', 'Connexion admin'),
    ]
    utilisateur = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, related_name='logs_audit')
    action = models.CharField(max_length=30, choices=ACTIONS)
    description = models.TextField()
    objet_type = models.CharField(max_length=100, blank=True)
    objet_id = models.IntegerField(null=True, blank=True)
    adresse_ip = models.GenericIPAddressField(null=True, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'academie'
        db_table = 'academie_logaudit'
        ordering = ['-date_creation']
        verbose_name = "Log d'audit"
        verbose_name_plural = "Logs d'audit"


class Enseignant(models.Model):
    STATUTS = [('actif', '✅ Actif'), ('en_attente', '⏳ En attente validation'), ('suspendu', '⛔ Suspendu')]
    profil = models.OneToOneField(ProfilUtilisateur, on_delete=models.CASCADE, related_name='enseignant')
    formations_attribuees = models.ManyToManyField('academie.Formation', blank=True, related_name='enseignants')
    statut = models.CharField(max_length=15, choices=STATUTS, default='en_attente')
    date_recrutement = models.DateTimeField(auto_now_add=True)
    numero_contrat = models.CharField(max_length=50, blank=True)
    document_cv = models.FileField(upload_to='enseignants/cv/', null=True, blank=True)

    class Meta:
        app_label = 'academie'
        db_table = 'academie_enseignant'
        verbose_name = 'Enseignant'
        verbose_name_plural = 'Enseignants'

    def __str__(self):
        return f"{self.profil.utilisateur.get_full_name() or self.profil.utilisateur.username}"

    def revenus_generes(self):
        from django.db.models import Sum
        from academie.models import OrderItem
        total = OrderItem.objects.filter(
            formation__in=self.formations_attribuees.all(), commande__statut='paye'
        ).aggregate(t=Sum('prix_unitaire'))['t'] or 0
        return total

    def part_remuneration(self):
        taux = self.profil.taux_remuneration or 0
        return round(self.revenus_generes() * (taux / 100), 2)

    def nb_etudiants_formes(self):
        from django.contrib.auth.models import User
        from academie.models import AccesFormationDebloque
        return User.objects.filter(
            acces_debloques__formation__in=self.formations_attribuees.all()
        ).distinct().count()


class HistoriqueConversationIA(models.Model):
    utilisateur = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='historique_ia')
    role = models.CharField(max_length=10, choices=[('user', 'Utilisateur'), ('assistant', 'Blessy AI')])
    contenu = models.TextField()
    contexte_lecon = models.ForeignKey('academie.Lecon', on_delete=models.SET_NULL, null=True, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'academie'
        db_table = 'academie_historiqueconversationia'
        ordering = ['date_creation']
        indexes = [models.Index(fields=['utilisateur', 'date_creation'])]


class PushSubscription(models.Model):
    utilisateur = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='push_subscriptions')
    endpoint = models.URLField(max_length=500)
    cle_p256dh = models.CharField(max_length=200)
    cle_auth = models.CharField(max_length=200)
    navigateur = models.CharField(max_length=100, blank=True)
    actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'academie'
        db_table = 'academie_pushsubscription'
        unique_together = ['utilisateur', 'endpoint']


class NotificationPushEnvoyee(models.Model):
    TYPES = [
        ('badge', '🎖️ Badge'), ('certificat', '🎓 Certificat'), ('forum_reponse', '💬 Réponse forum'),
        ('rappel_inactivite', '⏰ Rappel'), ('promotion', '🔥 Promotion'), ('systeme', '⚙️ Système'),
    ]
    utilisateur = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='push_recues')
    type_notification = models.CharField(max_length=20, choices=TYPES)
    titre = models.CharField(max_length=100)
    corps = models.CharField(max_length=200)
    url_cible = models.CharField(max_length=200, blank=True)
    envoyee_avec_succes = models.BooleanField(default=False)
    date_envoi = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'academie'
        db_table = 'academie_notificationpushenvoyee'
        ordering = ['-date_envoi']