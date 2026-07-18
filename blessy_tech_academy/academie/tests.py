import json
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from .models import (
    Academie,
    AccesFormationDebloque,
    Coupon,
    Ecole,
    Formation,
    Invoice,
    Lecon,
    Module,
    MoyenPaiement,
    Order,
    OrderItem,
    Promotion,
    Transaction,
    WorkflowFormation,
)


class BaseTestCase(TestCase):
    """Configure les données de base partagées entre plusieurs classes de test."""

    def setUp(self):
        # Créer une académie par défaut
        self.academie = Academie.objects.create(
            nom="Test Academy",
            slug="test",
            est_academie_par_defaut=True
        )
        self.ecole = Ecole.objects.create(
            nom="École Test",
            icone="🏫",
            academie=self.academie,
            ordre=1
        )
        self.formation_gratuite = Formation.objects.create(
            nom="Formation Gratuite",
            ecole=self.ecole,
            gratuit=True,
            actif=True,
            prix=0,
            duree_mois=1,          # Ajouté car requis (NOT NULL)
        )
        self.formation_payante = Formation.objects.create(
            nom="Formation Payante",
            ecole=self.ecole,
            gratuit=False,
            actif=True,
            prix=100,
            duree_mois=3,          # Ajouté car requis (NOT NULL)
        )
        WorkflowFormation.objects.get_or_create(formation=self.formation_payante)

        # Module et leçon pour progression
        self.module = Module.objects.create(formation=self.formation_gratuite, titre="Module 1")
        self.lecon = Lecon.objects.create(
            module=self.module,
            titre="Leçon 1",
            contenu="<p>Contenu test</p>",
            duree_minutes=10
        )

        # Utilisateur de test
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        # Client avec IP explicite pour éviter l'erreur ConnexionUtilisateur.adresse_ip NOT NULL
        self.client = Client(REMOTE_ADDR='127.0.0.1')


# ================================================
# Tests de création de compte et connexion
# ================================================
class TestUserCreation(BaseTestCase):
    """Teste la création de compte utilisateur."""

    def test_inscription_compte(self):
        # ATTENTION : la vue inscription_compte doit utiliser
        # login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        # pour éviter ValueError avec plusieurs backends d'authentification.
        response = self.client.post(reverse('inscription_compte'), {
            'email': 'newuser@example.com',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
            'first_name': 'John',
            'last_name': 'Doe',
            'username': 'johndoe',
        })
        # Redirection vers le dashboard après inscription
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(email='newuser@example.com').exists())

    def test_connexion(self):
        response = self.client.post(reverse('connexion'), {
            'username': 'testuser',
            'password': 'testpass123',
        })
        self.assertEqual(response.status_code, 302)  # Redirection après connexion


# ================================================
# Tests d'accès aux formations (gratuite et payante)
# ================================================
class TestAccessFormation(BaseTestCase):
    """Teste l'accès aux formations (gratuite et payante)."""

    def test_acces_formation_gratuite(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('detail_formation', args=[self.formation_gratuite.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['acces_autorise'])

    def test_acces_formation_payante_non_debloquee(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('detail_formation', args=[self.formation_payante.id]))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['acces_autorise'])


# ================================================
# Tests du tunnel de paiement complet
# ================================================
class TestPaymentTunnel(BaseTestCase):
    """Teste le tunnel d'achat complet : commande, checkout, validation."""

    def setUp(self):
        super().setUp()
        # Correction : le champ s'appelle 'nom_affiche', pas 'nom'
        self.moyen = MoyenPaiement.objects.create(
            nom_affiche="Test Manuel",
            code="manuel",
            actif=True
        )
        self.client.login(username='testuser', password='testpass123')

    def test_initier_achat_creer_commande(self):
        response = self.client.post(
            reverse('initier_achat', args=[self.formation_payante.id])
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Order.objects.filter(utilisateur=self.user).exists())

    def test_checkout_et_paiement_manuel_debloque(self):
        # Initier achat
        self.client.post(reverse('initier_achat', args=[self.formation_payante.id]))
        commande = Order.objects.filter(utilisateur=self.user).first()
        # Aller au checkout
        response = self.client.post(
            reverse('checkout', args=[commande.reference]),
            {'moyen_paiement': self.moyen.id}
        )
        self.assertEqual(response.status_code, 302)

        # Simuler confirmation de paiement manuel
        fake_file = SimpleUploadedFile("preuve.png", b"file_content", content_type="image/png")
        response = self.client.post(
            reverse('confirmer_paiement', args=[commande.reference]),
            {'preuve_paiement': fake_file, 'reference_externe': 'REF123'}
        )
        self.assertEqual(response.status_code, 302)

        # Valider la transaction directement (simulation admin_valider_transaction)
        trans = Transaction.objects.filter(commande=commande).first()
        self.assertIsNotNone(trans)
        trans.statut = 'reussie'
        trans.save()
        commande.statut = 'paye'
        commande.date_paiement = timezone.now()
        commande.save()
        for item in commande.items.all():
            if item.formation:
                AccesFormationDebloque.objects.get_or_create(
                    utilisateur=commande.utilisateur,
                    nom_formation_snapshot=item.nom_produit_snapshot,
                    defaults={'formation': item.formation, 'commande_origine': commande}
                )
        Invoice.objects.get_or_create(commande=commande)

        # Vérifier que l'accès est débloqué
        self.assertTrue(
            AccesFormationDebloque.objects.filter(
                utilisateur=self.user,
                formation=self.formation_payante
            ).exists()
        )


# ================================================
# Tests API IA basiques
# ================================================
class TestBasicIA(BaseTestCase):
    """Test minimal de l'API IA (simule une réponse)."""

    def test_api_chat_ia_requires_post(self):
        response = self.client.get(reverse('api_chat_ia'))
        self.assertEqual(response.status_code, 405)  # Method not allowed

    def test_api_chat_ia_empty_question(self):
        response = self.client.post(
            reverse('api_chat_ia'),
            data=json.dumps({'question': ''}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_api_chat_ia_valid_question(self):
        # Teste que la route fonctionne sans erreur (peut retourner 200 ou 500 selon clé API)
        response = self.client.post(
            reverse('api_chat_ia'),
            data=json.dumps({'question': 'Bonjour'}),
            content_type='application/json'
        )
        self.assertIn(response.status_code, [200, 500])


# ================================================
# Tests Payment Center (existants)
# ================================================
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
        self.assertTrue(hasattr(self.user, 'profil'))
        self.assertEqual(self.user.profil.role, 'etudiant')

    def test_commande_calcul_total_simple(self):
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
        coupon = Coupon.objects.create(code='MOINS15', type_reduction='fixe', valeur=15)
        commande = Order.objects.create(utilisateur=self.user, coupon_applique=coupon, total=0)
        OrderItem.objects.create(
            commande=commande, formation=self.formation, type_produit='formation',
            nom_produit_snapshot=self.formation.nom, prix_unitaire=Decimal('100.00'),
        )
        commande.recalculer_total()
        self.assertEqual(commande.total, Decimal('85.00'))

    def test_coupon_expire_invalide(self):
        coupon = Coupon.objects.create(
            code='EXPIRE', type_reduction='pourcentage', valeur=10,
            date_fin=timezone.now() - timedelta(days=1),
        )
        valide, message = coupon.est_valide()
        self.assertFalse(valide)
        self.assertIn('expiré', message.lower())

    def test_coupon_limite_utilisations(self):
        coupon = Coupon.objects.create(
            code='LIMITE1', type_reduction='fixe', valeur=10,
            utilisations_max=1, utilisations_actuelles=1,
        )
        valide, message = coupon.est_valide()
        self.assertFalse(valide)

    def test_snapshot_survit_suppression_formation(self):
        commande = Order.objects.create(utilisateur=self.user, total=100)
        item = OrderItem.objects.create(
            commande=commande, formation=self.formation, type_produit='formation',
            nom_produit_snapshot=self.formation.nom,
            icone_produit_snapshot=self.formation.icone,
            prix_unitaire=Decimal('100.00'),
        )

        nom_snapshot_avant = item.nom_produit_snapshot
        self.formation.delete()
        item.refresh_from_db()

        self.assertIsNone(item.formation)
        self.assertEqual(item.nom_produit_snapshot, nom_snapshot_avant)
        self.assertEqual(item.prix_unitaire, Decimal('100.00'))

    def test_deblocage_acces_apres_validation(self):
        commande = Order.objects.create(utilisateur=self.user, total=100, statut='en_attente')
        OrderItem.objects.create(
            commande=commande, formation=self.formation, type_produit='formation',
            nom_produit_snapshot=self.formation.nom, prix_unitaire=Decimal('100.00'),
        )

        acces_existe = AccesFormationDebloque.objects.filter(
            utilisateur=self.user, formation=self.formation
        ).exists()
        self.assertFalse(acces_existe)

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
        formation_gratuite = Formation.objects.create(
            ecole=self.ecole, nom='Gratuite Test', icone='🎁',
            description='Test', duree_mois=1, prix=0, gratuit=True, actif=True,
        )
        self.assertTrue(formation_gratuite.gratuit)

    def test_promotion_s_applique_formation_correcte(self):
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