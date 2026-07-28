# ================================================
# BILLING/MODELS.PY — Modèles commerce/paiement extraits d'academie
# app_label='academie' + db_table explicite préserve toutes les tables
# ================================================

from django.db import models
from django.utils import timezone
import uuid


class MoyenPaiement(models.Model):
    CODES = [
        ('manuel', 'Paiement manuel (validation admin)'), ('moncash', 'MonCash'),
        ('natcash', 'NatCash'), ('stripe', 'Carte bancaire (Stripe)'),
        ('paypal', 'PayPal'), ('virement', 'Virement bancaire'),
    ]
    code = models.CharField(max_length=20, choices=CODES, unique=True)
    nom_affiche = models.CharField(max_length=100)
    icone = models.CharField(max_length=10, default='💳')
    actif = models.BooleanField(default=True)
    instructions = models.TextField(blank=True)
    ordre = models.IntegerField(default=0)

    class Meta:
        app_label = 'academie'
        db_table = 'academie_moyenpaiement'
        ordering = ['ordre']
        verbose_name = 'Moyen de paiement'
        verbose_name_plural = 'Moyens de paiement'

    def __str__(self):
        return f"{self.icone} {self.nom_affiche}"


class Coupon(models.Model):
    TYPES = [('fixe', 'Montant fixe'), ('pourcentage', 'Pourcentage')]
    code = models.CharField(max_length=30, unique=True)
    type_reduction = models.CharField(max_length=15, choices=TYPES, default='pourcentage')
    valeur = models.DecimalField(max_digits=10, decimal_places=2)
    formation_specifique = models.ForeignKey('academie.Formation', on_delete=models.SET_NULL, null=True, blank=True, related_name='coupons')
    ecole_specifique = models.ForeignKey('academie.Ecole', on_delete=models.SET_NULL, null=True, blank=True, related_name='coupons')
    parcours_specifique = models.ForeignKey('academie.Parcours', on_delete=models.SET_NULL, null=True, blank=True, related_name='coupons')
    utilisations_max = models.IntegerField(default=0)
    utilisations_actuelles = models.IntegerField(default=0)
    date_debut = models.DateTimeField(default=timezone.now)
    date_fin = models.DateTimeField(null=True, blank=True)
    actif = models.BooleanField(default=True)

    class Meta:
        app_label = 'academie'
        db_table = 'academie_coupon'
        verbose_name = 'Coupon'
        verbose_name_plural = 'Coupons'

    def __str__(self):
        return f"{self.code} ({self.get_type_reduction_display()})"

    def est_valide(self):
        maintenant = timezone.now()
        if not self.actif:
            return False, "Ce coupon n'est plus actif."
        if self.date_fin and maintenant > self.date_fin:
            return False, "Ce coupon a expiré."
        if self.utilisations_max > 0 and self.utilisations_actuelles >= self.utilisations_max:
            return False, "Ce coupon a atteint sa limite d'utilisation."
        return True, ""


class Promotion(models.Model):
    nom = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    pourcentage_reduction = models.IntegerField()
    ecoles_concernees = models.ManyToManyField('academie.Ecole', blank=True, related_name='promotions')
    formations_concernees = models.ManyToManyField('academie.Formation', blank=True, related_name='promotions')
    date_debut = models.DateTimeField()
    date_fin = models.DateTimeField()
    actif = models.BooleanField(default=True)
    bandeau_texte = models.CharField(max_length=200, blank=True)

    class Meta:
        app_label = 'academie'
        db_table = 'academie_promotion'
        verbose_name = 'Promotion'
        verbose_name_plural = 'Promotions'

    def __str__(self):
        return f"{self.nom} (-{self.pourcentage_reduction}%)"

    def est_active(self):
        maintenant = timezone.now()
        return self.actif and self.date_debut <= maintenant <= self.date_fin

    def s_applique_a(self, formation):
        if not self.est_active():
            return False
        if self.formations_concernees.filter(id=formation.id).exists():
            return True
        if formation.ecole and self.ecoles_concernees.filter(id=formation.ecole.id).exists():
            return True
        return False


class Order(models.Model):
    STATUTS = [
        ('en_attente', '⏳ En attente de paiement'), ('paye', '✅ Payée'),
        ('annule', '❌ Annulée'), ('rembourse', '↩️ Remboursée'),
    ]
    reference = models.CharField(max_length=20, unique=True, editable=False, db_index=True)
    utilisateur = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='commandes')
    sous_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    reduction_totale = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    devise = models.CharField(max_length=3, choices=[('USD', 'USD'), ('HTG', 'HTG')], default='USD')
    coupon_applique = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)
    moyen_paiement = models.ForeignKey(MoyenPaiement, on_delete=models.SET_NULL, null=True, blank=True)
    affilie_origine = models.ForeignKey('Affilie', on_delete=models.SET_NULL, null=True, blank=True, related_name='commandes_generees')
    statut = models.CharField(max_length=15, choices=STATUTS, default='en_attente')
    date_creation = models.DateTimeField(auto_now_add=True)
    date_paiement = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = 'academie'
        db_table = 'academie_order'
        ordering = ['-date_creation']
        verbose_name = 'Commande'
        verbose_name_plural = 'Commandes'
        indexes = [
            models.Index(fields=['statut', 'date_creation']),
            models.Index(fields=['utilisateur', 'statut']),
        ]

    def __str__(self):
        return f"Commande #{self.reference} — {self.utilisateur.username}"

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = f"BTA-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def recalculer_total(self):
        from decimal import Decimal
        from django.db.models import Sum
        self.sous_total = self.items.aggregate(t=Sum('prix_unitaire'))['t'] or Decimal('0')
        if self.coupon_applique:
            if self.coupon_applique.type_reduction == 'pourcentage':
                self.reduction_totale = self.sous_total * (Decimal(str(self.coupon_applique.valeur)) / 100)
            else:
                self.reduction_totale = min(Decimal(str(self.coupon_applique.valeur)), self.sous_total)
        else:
            self.reduction_totale = Decimal('0')
        self.total = self.sous_total - self.reduction_totale
        self.save()


class OrderItem(models.Model):
    TYPES_PRODUIT = [('formation', 'Formation'), ('parcours', 'Parcours Professionnel')]
    commande = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    formation = models.ForeignKey('academie.Formation', on_delete=models.SET_NULL, null=True, blank=True)
    parcours = models.ForeignKey('academie.Parcours', on_delete=models.SET_NULL, null=True, blank=True)
    type_produit = models.CharField(max_length=15, choices=TYPES_PRODUIT)
    nom_produit_snapshot = models.CharField(max_length=200)
    icone_produit_snapshot = models.CharField(max_length=10, default='📚')
    ecole_nom_snapshot = models.CharField(max_length=200, blank=True)
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        app_label = 'academie'
        db_table = 'academie_orderitem'
        verbose_name = 'Article de commande'
        verbose_name_plural = 'Articles de commande'

    def __str__(self):
        return f"{self.nom_produit_snapshot} — {self.prix_unitaire}$"

    def obtenir_lien_produit(self):
        if self.formation:
            return f"/formation/{self.formation.id}/"
        return None


class Invoice(models.Model):
    commande = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='facture')
    numero_facture = models.CharField(max_length=30, unique=True, editable=False, db_index=True)
    date_emission = models.DateTimeField(auto_now_add=True)
    fichier_pdf = models.FileField(upload_to='factures/', null=True, blank=True)

    class Meta:
        app_label = 'academie'
        db_table = 'academie_invoice'
        verbose_name = 'Facture'
        verbose_name_plural = 'Factures'

    def save(self, *args, **kwargs):
        if not self.numero_facture:
            annee = timezone.now().year
            self.numero_facture = f"FACT-{annee}-{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.numero_facture


class Transaction(models.Model):
    STATUTS = [
        ('initiee', 'Initiée'), ('reussie', 'Réussie'),
        ('echouee', 'Échouée'), ('en_verification', 'En vérification manuelle'),
    ]
    commande = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='transactions')
    moyen_paiement = models.ForeignKey(MoyenPaiement, on_delete=models.SET_NULL, null=True)
    reference_externe = models.CharField(max_length=100, blank=True)
    preuve_paiement = models.ImageField(upload_to='preuves_paiement/', null=True, blank=True)
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    statut = models.CharField(max_length=20, choices=STATUTS, default='initiee')
    notes_admin = models.TextField(blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    valide_par = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions_validees')

    class Meta:
        app_label = 'academie'
        db_table = 'academie_transaction'
        ordering = ['-date_creation']
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'
        indexes = [
            models.Index(fields=['statut']),
            models.Index(fields=['commande', 'statut']),
        ]

    def __str__(self):
        return f"Transaction {self.commande.reference} — {self.get_statut_display()}"


class Refund(models.Model):
    commande = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='remboursements')
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    raison = models.TextField()
    approuve_par = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    date_demande = models.DateTimeField(auto_now_add=True)
    date_traitement = models.DateTimeField(null=True, blank=True)
    statut = models.CharField(max_length=15, choices=[('demande', 'Demandé'), ('approuve', 'Approuvé'), ('rejete', 'Rejeté')], default='demande')

    class Meta:
        app_label = 'academie'
        db_table = 'academie_refund'
        verbose_name = 'Remboursement'
        verbose_name_plural = 'Remboursements'

    def __str__(self):
        return f"Remboursement {self.commande.reference} — {self.montant}$"


class AccesFormationDebloque(models.Model):
    utilisateur = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='acces_debloques')
    formation = models.ForeignKey('academie.Formation', on_delete=models.SET_NULL, null=True, blank=True)
    nom_formation_snapshot = models.CharField(max_length=200)
    commande_origine = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True)
    date_deblocage = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'academie'
        db_table = 'academie_accesformationdebloque'
        unique_together = ['utilisateur', 'nom_formation_snapshot']
        verbose_name = "Accès formation débloqué"
        verbose_name_plural = "Accès formations débloqués"
        indexes = [models.Index(fields=['utilisateur']), models.Index(fields=['formation'])]

    def __str__(self):
        return f"{self.utilisateur.username} → {self.nom_formation_snapshot}"


class PlanAbonnement(models.Model):
    PERIODICITES = [('mensuel', 'Mensuel'), ('annuel', 'Annuel')]
    nom = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    prix = models.DecimalField(max_digits=10, decimal_places=2)
    periodicite = models.CharField(max_length=10, choices=PERIODICITES, default='mensuel')
    avantages = models.TextField()
    actif = models.BooleanField(default=True)
    stripe_price_id = models.CharField(max_length=100, blank=True)

    class Meta:
        app_label = 'academie'
        db_table = 'academie_planabonnement'
        verbose_name = "Plan d'abonnement"
        verbose_name_plural = "Plans d'abonnement"

    def __str__(self):
        return f"{self.nom} — {self.prix}$/{self.get_periodicite_display()}"


class Subscription(models.Model):
    STATUTS = [('actif', 'Actif'), ('annule', 'Annulé'), ('expire', 'Expiré'), ('en_echec', 'Paiement échoué')]
    utilisateur = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='abonnements')
    plan = models.ForeignKey(PlanAbonnement, on_delete=models.SET_NULL, null=True)
    plan_nom_snapshot = models.CharField(max_length=100)
    prix_snapshot = models.DecimalField(max_digits=10, decimal_places=2)
    stripe_subscription_id = models.CharField(max_length=100, blank=True)
    stripe_customer_id = models.CharField(max_length=100, blank=True)
    statut = models.CharField(max_length=15, choices=STATUTS, default='actif')
    date_debut = models.DateTimeField(auto_now_add=True)
    date_prochain_renouvellement = models.DateTimeField()
    date_annulation = models.DateTimeField(null=True, blank=True)
    renouvellement_auto = models.BooleanField(default=True)

    class Meta:
        app_label = 'academie'
        db_table = 'academie_subscription'
        verbose_name = 'Abonnement'
        verbose_name_plural = 'Abonnements'

    def __str__(self):
        return f"{self.utilisateur.username} — {self.plan_nom_snapshot} ({self.get_statut_display()})"

    def est_actif(self):
        return self.statut == 'actif' and self.date_prochain_renouvellement > timezone.now()


class Affilie(models.Model):
    utilisateur = models.OneToOneField('auth.User', on_delete=models.CASCADE, related_name='affiliation')
    code_affiliation = models.CharField(max_length=20, unique=True)
    taux_commission = models.DecimalField(max_digits=5, decimal_places=2, default=10)
    actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'academie'
        db_table = 'academie_affilie'
        verbose_name = 'Affilié'
        verbose_name_plural = 'Affiliés'

    def __str__(self):
        return f"{self.utilisateur.username} ({self.code_affiliation})"

    def save(self, *args, **kwargs):
        if not self.code_affiliation:
            self.code_affiliation = f"AFF-{self.utilisateur.username[:6].upper()}{uuid.uuid4().hex[:4].upper()}"
        super().save(*args, **kwargs)

    def commission_totale(self):
        from django.db.models import Sum
        ventes = OrderItem.objects.filter(commande__affilie_origine=self, commande__statut='paye').aggregate(t=Sum('prix_unitaire'))['t'] or 0
        return round(ventes * (self.taux_commission / 100), 2)


class CommissionAffiliation(models.Model):
    STATUTS = [('en_attente', 'En attente'), ('payee', 'Payée')]
    affilie = models.ForeignKey(Affilie, on_delete=models.CASCADE, related_name='commissions')
    commande = models.ForeignKey(Order, on_delete=models.CASCADE)
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    statut = models.CharField(max_length=15, choices=STATUTS, default='en_attente')
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'academie'
        db_table = 'academie_commissionaffiliation'
        verbose_name = 'Commission affiliation'
        verbose_name_plural = 'Commissions affiliation'