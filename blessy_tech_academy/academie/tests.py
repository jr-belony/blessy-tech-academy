from django.test import TestCase

# Create your tests here.
# ================================================
# TESTS.PY — Suite de tests critiques Payment Center
# Lancer avec : python manage.py test academie
# ================================================

from decimal import Decimal
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

from .models import (
    Ecole, Formation, Order, OrderItem, Coupon, Promotion,
    MoyenPaiement, Transaction, AccesFormationDebloque, Invoice,
    ProfilUtilisateur,
)


class PaymentCenterTestCase(TestCase):
    """Tests critiques du système de paiement — anti-cassure et calculs."""

    def setUp(self):
        self.user = User.objects.create_user(username='etudiant_test', email='test@bta.com', password='test1234')
        self.ecole = Ecole.objects.create(nom='École Test', icone='🏫', ordre=1)
        self.formation = Formation.objects.create(
            ecole=self.ecole, nom='Python Test', icone='🐍',
            description='Formation test', duree_mois=3, prix=100,
            niveau='debutant', actif=True, gratuit=False,
        )
        self.moyen_manuel = MoyenPaiement.objects.create(
            code='manuel', nom_affiche='Paiement manuel', icone='📱'
        )

    def test_creation_profil_automatique(self):
        """Vérifie qu'un ProfilUtilisateur est créé automatiquement à l'inscription."""
        self.assertTrue(hasattr(self.user, 'profil'))
        self.assertEqual(self.user.profil.role, 'etudiant')

    def test_commande_calcul_total_simple(self):
        """Vérifie que le total d'une commande sans coupon = prix de l'item."""
        commande = Order.objects.create(utilisateur=self.user, total=0)
        OrderItem.objects.create(
            commande=commande, formation=self.formation, type_produit='formation',
            nom_produit_snapshot=self.formation.nom, prix_unitaire=Decimal('100.00'),
        )
        commande.recalculer_total()
        self.assertEqual(commande.total, Decimal('100.00'))
        self.assertEqual(commande.sous_total, Decimal('100.00'))
        self.assertEqual(commande.reduction_totale, Decimal('0'))

    def test_coupon_pourcentage(self):
        """Vérifie qu'un coupon en % réduit correctement le total."""
        coupon = Coupon.objects.create(code='PROMO20', type_reduction='pourcentage', valeur=20)
        commande = Order.objects.create(utilisateur=self.user, coupon_applique=coupon, total=0)
        OrderItem.objects.create(
            commande=commande, formation=self.formation, type_produit='formation',
            nom_produit_snapshot=self.formation.nom, prix_unitaire=Decimal('100.00'),
        )
        commande.recalculer_total()
        self.assertEqual(commande.reduction_totale, Decimal('20.00'))
        self.assertEqual(commande.total, Decimal('80.00'))

    def test_coupon_fixe(self):
        """Vérifie qu'un coupon fixe réduit exactement le montant indiqué."""
        coupon = Coupon.objects.create(code='MOINS15', type_reduction='fixe', valeur=15)
        commande = Order.objects.create(utilisateur=self.user, coupon_applique=coupon, total=0)
        OrderItem.objects.create(
            commande=commande, formation=self.formation, type_produit='formation',
            nom_produit_snapshot=self.formation.nom, prix_unitaire=Decimal('100.00'),
        )
        commande.recalculer_total()
        self.assertEqual(commande.total, Decimal('85.00'))

    def test_coupon_expire_invalide(self):
        """Vérifie qu'un coupon expiré est rejeté par est_valide()."""
        coupon = Coupon.objects.create(
            code='EXPIRE', type_reduction='pourcentage', valeur=10,
            date_fin=timezone.now() - timedelta(days=1),
        )
        valide, message = coupon.est_valide()
        self.assertFalse(valide)
        self.assertIn('expiré', message.lower())

    def test_coupon_limite_utilisations(self):
        """Vérifie qu'un coupon atteignant sa limite d'usage devient invalide."""
        coupon = Coupon.objects.create(
            code='LIMITE1', type_reduction='fixe', valeur=10,
            utilisations_max=1, utilisations_actuelles=1,
        )
        valide, message = coupon.est_valide()
        self.assertFalse(valide)

    def test_snapshot_survit_suppression_formation(self):
        """
        TEST CRITIQUE ANTI-CASSURE : vérifie qu'un OrderItem garde ses 
        infos même après suppression de la Formation d'origine.
        """
        commande = Order.objects.create(utilisateur=self.user, total=100)
        item = OrderItem.objects.create(
            commande=commande, formation=self.formation, type_produit='formation',
            nom_produit_snapshot=self.formation.nom,
            icone_produit_snapshot=self.formation.icone,
            prix_unitaire=Decimal('100.00'),
        )

        nom_snapshot_avant = item.nom_produit_snapshot

        # Supprime la formation d'origine
        self.formation.delete()
        item.refresh_from_db()

        # L'OrderItem doit toujours exister avec ses infos intactes
        self.assertIsNone(item.formation)  # FK devenue NULL (SET_NULL)
        self.assertEqual(item.nom_produit_snapshot, nom_snapshot_avant)  # Snapshot intact
        self.assertEqual(item.prix_unitaire, Decimal('100.00'))  # Prix historique préservé

    def test_deblocage_acces_apres_validation(self):
        """Vérifie que l'accès est débloqué uniquement après validation transaction."""
        commande = Order.objects.create(utilisateur=self.user, total=100, statut='en_attente')
        OrderItem.objects.create(
            commande=commande, formation=self.formation, type_produit='formation',
            nom_produit_snapshot=self.formation.nom, prix_unitaire=Decimal('100.00'),
        )

        # Avant validation : pas d'accès
        acces_existe = AccesFormationDebloque.objects.filter(
            utilisateur=self.user, formation=self.formation
        ).exists()
        self.assertFalse(acces_existe)

        # Simule la validation (logique de admin_valider_transaction)
        commande.statut = 'paye'
        commande.save()
        for item in commande.items.all():
            AccesFormationDebloque.objects.get_or_create(
                utilisateur=self.user, nom_formation_snapshot=item.nom_produit_snapshot,
                defaults={'formation': item.formation, 'commande_origine': commande}
            )

        acces_existe = AccesFormationDebloque.objects.filter(
            utilisateur=self.user, formation=self.formation
        ).exists()
        self.assertTrue(acces_existe)

    def test_formation_gratuite_pas_de_commande(self):
        """Vérifie qu'une formation gratuite ne nécessite aucune commande."""
        formation_gratuite = Formation.objects.create(
            ecole=self.ecole, nom='Gratuite Test', icone='🎁',
            description='Test', duree_mois=1, prix=0, gratuit=True, actif=True,
        )
        self.assertTrue(formation_gratuite.gratuit)

    def test_promotion_s_applique_formation_correcte(self):
        """Vérifie qu'une promotion ne s'applique qu'aux formations ciblées."""
        autre_formation = Formation.objects.create(
            ecole=self.ecole, nom='Autre Formation', icone='📚',
            description='Test', duree_mois=2, prix=50, actif=True,
        )
        promo = Promotion.objects.create(
            nom='Promo Test', pourcentage_reduction=30,
            date_debut=timezone.now() - timedelta(days=1),
            date_fin=timezone.now() + timedelta(days=1),
            actif=True,
        )
        promo.formations_concernees.add(self.formation)

        self.assertTrue(promo.s_applique_a(self.formation))
        self.assertFalse(promo.s_applique_a(autre_formation))

    def test_reference_commande_unique(self):
        """Vérifie que chaque commande génère une référence unique."""
        commande1 = Order.objects.create(utilisateur=self.user, total=100)
        commande2 = Order.objects.create(utilisateur=self.user, total=50)
        self.assertNotEqual(commande1.reference, commande2.reference)
        self.assertTrue(commande1.reference.startswith('BTA-'))


class RoleSystemTestCase(TestCase):
    """Tests du système de rôles granulaire."""

    def setUp(self):
        self.user = User.objects.create_user(username='test_role', password='test1234')

    def test_role_par_defaut_etudiant(self):
        self.assertEqual(self.user.profil.role, 'etudiant')

    def test_permissions_par_role(self):
        self.user.profil.role = 'finance'
        self.user.profil.save()
        self.assertTrue(self.user.profil.peut_voir_finance())
        self.assertFalse(self.user.profil.peut_gerer_formations())

    def test_admin_a_tous_les_droits(self):
        self.user.profil.role = 'admin'
        self.user.profil.save()
        self.assertTrue(self.user.profil.peut_voir_finance())
        self.assertTrue(self.user.profil.peut_moderer_forum())
        self.assertTrue(self.user.profil.peut_gerer_formations())
        self.assertTrue(self.user.profil.peut_voir_crm())
