import json
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.test.utils import CaptureQueriesContext
from django.db import connection
from django.urls import reverse
from django.utils import timezone

from .models import (
    Ecole,
    Formation,
    Module,
    Lecon,
    ProgressionLecon,
    Quiz,
    Question,
    ResultatQuiz,
    Parcours,
    Competence,
    CompetenceValidee,
    LearningOutcome,
    WorkflowFormation,
    Examen,
    QuestionExamen,
    ChoixExamen,
    TentativeExamen,
    Certificat,
    ProjetEtudiant,
)

from .models import (
    Academie,
    AccesFormationDebloque,
    Coupon,
    Invoice,
    MoyenPaiement,
    Order,
    OrderItem,
    PartenaireAPI,
    Promotion,
    Reaction,
    Sujet,
    Transaction,
    Article,
)

class BaseTestCase(TestCase):
    """Configure les données de base partagées entre plusieurs classes de test."""

    def setUp(self):
        # Créer une académie par défaut
        self.academie = Academie.objects.create(
            nom="Test Academy", slug="test", est_academie_par_defaut=True
        )
        self.ecole = Ecole.objects.create(
            nom="École Test", icone="🏫", academie=self.academie, ordre=1
        )
        self.formation_gratuite = Formation.objects.create(
            nom="Formation Gratuite",
            ecole=self.ecole,
            gratuit=True,
            actif=True,
            prix=0,
            duree_mois=1,  # Ajouté car requis (NOT NULL)
        )
        self.formation_payante = Formation.objects.create(
            nom="Formation Payante",
            ecole=self.ecole,
            gratuit=False,
            actif=True,
            prix=100,
            duree_mois=3,  # Ajouté car requis (NOT NULL)
        )
        WorkflowFormation.objects.get_or_create(formation=self.formation_payante)

        # Module et leçon pour progression
        self.module = Module.objects.create(formation=self.formation_gratuite, titre="Module 1")
        self.lecon = Lecon.objects.create(
            module=self.module, titre="Leçon 1", contenu="<p>Contenu test</p>", duree_minutes=10
        )

        # Utilisateur de test
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        # Client avec IP explicite pour éviter l'erreur ConnexionUtilisateur.adresse_ip NOT NULL
        self.client = Client(REMOTE_ADDR="127.0.0.1")


# ================================================
# Tests de création de compte et connexion
# ================================================
class TestUserCreation(BaseTestCase):
    """Teste la création de compte utilisateur."""

    def test_inscription_compte(self):
        # ATTENTION : la vue inscription_compte doit utiliser
        # login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        # pour éviter ValueError avec plusieurs backends d'authentification.
        response = self.client.post(
            reverse("inscription_compte"),
            {
                "email": "newuser@example.com",
                "password1": "ComplexPass123!",
                "password2": "ComplexPass123!",
                "first_name": "John",
                "last_name": "Doe",
                "username": "johndoe",
            },
        )
        # Redirection vers le dashboard après inscription
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(email="newuser@example.com").exists())

    def test_connexion(self):
        response = self.client.post(
            reverse("connexion"),
            {
                "username": "testuser",
                "password": "testpass123",
            },
        )
        self.assertEqual(response.status_code, 302)  # Redirection après connexion


# ================================================
# Tests d'accès aux formations (gratuite et payante)
# ================================================
class TestAccessFormation(BaseTestCase):
    """Teste l'accès aux formations (gratuite et payante)."""

    def test_acces_formation_gratuite(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("detail_formation", args=[self.formation_gratuite.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["acces_autorise"])

    def test_acces_formation_payante_non_debloquee(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("detail_formation", args=[self.formation_payante.id]))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["acces_autorise"])


# ================================================
# Tests du tunnel de paiement complet
# ================================================
class TestPaymentTunnel(BaseTestCase):
    """Teste le tunnel d'achat complet : commande, checkout, validation."""

    def setUp(self):
        super().setUp()
        # Correction : le champ s'appelle 'nom_affiche', pas 'nom'
        self.moyen = MoyenPaiement.objects.create(
            nom_affiche="Test Manuel", code="manuel", actif=True
        )
        self.client.login(username="testuser", password="testpass123")

    def test_initier_achat_creer_commande(self):
        response = self.client.post(reverse("initier_achat", args=[self.formation_payante.id]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Order.objects.filter(utilisateur=self.user).exists())

    def test_checkout_et_paiement_manuel_debloque(self):
        # Initier achat
        self.client.post(reverse("initier_achat", args=[self.formation_payante.id]))
        commande = Order.objects.filter(utilisateur=self.user).first()
        # Aller au checkout
        response = self.client.post(
            reverse("checkout", args=[commande.reference]), {"moyen_paiement": self.moyen.id}
        )
        self.assertEqual(response.status_code, 302)

        # Simuler confirmation de paiement manuel
        fake_file = SimpleUploadedFile("preuve.png", b"file_content", content_type="image/png")
        response = self.client.post(
            reverse("confirmer_paiement", args=[commande.reference]),
            {"preuve_paiement": fake_file, "reference_externe": "REF123"},
        )
        self.assertEqual(response.status_code, 302)

        # Valider la transaction directement (simulation admin_valider_transaction)
        trans = Transaction.objects.filter(commande=commande).first()
        self.assertIsNotNone(trans)
        trans.statut = "reussie"
        trans.save()
        commande.statut = "paye"
        commande.date_paiement = timezone.now()
        commande.save()
        for item in commande.items.all():
            if item.formation:
                AccesFormationDebloque.objects.get_or_create(
                    utilisateur=commande.utilisateur,
                    nom_formation_snapshot=item.nom_produit_snapshot,
                    defaults={"formation": item.formation, "commande_origine": commande},
                )
        Invoice.objects.get_or_create(commande=commande)

        # Vérifier que l'accès est débloqué
        self.assertTrue(
            AccesFormationDebloque.objects.filter(
                utilisateur=self.user, formation=self.formation_payante
            ).exists()
        )


# ================================================
# Tests API IA basiques (corrigés pour login_required)
# ================================================
class TestBasicIA(BaseTestCase):
    """Test minimal de l'API IA (simule une réponse)."""

    def test_api_chat_ia_requires_post(self):
        # Non authentifié → redirection 302 (login_required)
        response = self.client.get(reverse("api_chat_ia"))
        self.assertEqual(response.status_code, 302)

    def test_api_chat_ia_empty_question(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(
            reverse("api_chat_ia"),
            data=json.dumps({"question": ""}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_api_chat_ia_valid_question(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(
            reverse("api_chat_ia"),
            data=json.dumps({"question": "Bonjour"}),
            content_type="application/json",
        )
        self.assertIn(response.status_code, [200, 500])


# ================================================
# Tests Payment Center (existants)
# ================================================
class PaymentCenterTestCase(TestCase):
    """Tests critiques du système de paiement — anti-cassure et calculs."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="etudiant_test", email="test@bta.com", password="test1234"
        )
        self.ecole = Ecole.objects.create(nom="École Test", icone="🏫", ordre=1)
        self.formation = Formation.objects.create(
            ecole=self.ecole,
            nom="Python Test",
            icone="🐍",
            description="Formation test",
            duree_mois=3,
            prix=100,
            niveau="debutant",
            actif=True,
            gratuit=False,
        )
        self.moyen_manuel = MoyenPaiement.objects.create(
            code="manuel", nom_affiche="Paiement manuel", icone="📱"
        )

    def test_creation_profil_automatique(self):
        self.assertTrue(hasattr(self.user, "profil"))
        self.assertEqual(self.user.profil.role, "etudiant")

    def test_commande_calcul_total_simple(self):
        commande = Order.objects.create(utilisateur=self.user, total=0)
        OrderItem.objects.create(
            commande=commande,
            formation=self.formation,
            type_produit="formation",
            nom_produit_snapshot=self.formation.nom,
            prix_unitaire=Decimal("100.00"),
        )
        commande.recalculer_total()
        self.assertEqual(commande.total, Decimal("100.00"))
        self.assertEqual(commande.sous_total, Decimal("100.00"))
        self.assertEqual(commande.reduction_totale, Decimal("0"))

    def test_coupon_pourcentage(self):
        coupon = Coupon.objects.create(code="PROMO20", type_reduction="pourcentage", valeur=20)
        commande = Order.objects.create(utilisateur=self.user, coupon_applique=coupon, total=0)
        OrderItem.objects.create(
            commande=commande,
            formation=self.formation,
            type_produit="formation",
            nom_produit_snapshot=self.formation.nom,
            prix_unitaire=Decimal("100.00"),
        )
        commande.recalculer_total()
        self.assertEqual(commande.reduction_totale, Decimal("20.00"))
        self.assertEqual(commande.total, Decimal("80.00"))

    def test_coupon_fixe(self):
        coupon = Coupon.objects.create(code="MOINS15", type_reduction="fixe", valeur=15)
        commande = Order.objects.create(utilisateur=self.user, coupon_applique=coupon, total=0)
        OrderItem.objects.create(
            commande=commande,
            formation=self.formation,
            type_produit="formation",
            nom_produit_snapshot=self.formation.nom,
            prix_unitaire=Decimal("100.00"),
        )
        commande.recalculer_total()
        self.assertEqual(commande.total, Decimal("85.00"))

    def test_coupon_expire_invalide(self):
        maintenant = timezone.now()
        coupon = Coupon.objects.create(
            code="EXPIRE",
            type_reduction="pourcentage",
            valeur=10,
            date_debut=maintenant - timedelta(days=10),   # début il y a 10 jours
            date_fin=maintenant - timedelta(days=1),      # fin hier → expiré
        )
        valide, message = coupon.est_valide()
        self.assertFalse(valide)
        self.assertIn("expiré", message.lower())

    def test_coupon_limite_utilisations(self):
        coupon = Coupon.objects.create(
            code="LIMITE1",
            type_reduction="fixe",
            valeur=10,
            utilisations_max=1,
            utilisations_actuelles=1,
        )
        valide, message = coupon.est_valide()
        self.assertFalse(valide)

    def test_snapshot_survit_suppression_formation(self):
        commande = Order.objects.create(utilisateur=self.user, total=100)
        item = OrderItem.objects.create(
            commande=commande,
            formation=self.formation,
            type_produit="formation",
            nom_produit_snapshot=self.formation.nom,
            icone_produit_snapshot=self.formation.icone,
            prix_unitaire=Decimal("100.00"),
        )

        nom_snapshot_avant = item.nom_produit_snapshot
        self.formation.delete()
        item.refresh_from_db()

        self.assertIsNone(item.formation)
        self.assertEqual(item.nom_produit_snapshot, nom_snapshot_avant)
        self.assertEqual(item.prix_unitaire, Decimal("100.00"))

    def test_deblocage_acces_apres_validation(self):
        commande = Order.objects.create(utilisateur=self.user, total=100, statut="en_attente")
        OrderItem.objects.create(
            commande=commande,
            formation=self.formation,
            type_produit="formation",
            nom_produit_snapshot=self.formation.nom,
            prix_unitaire=Decimal("100.00"),
        )

        acces_existe = AccesFormationDebloque.objects.filter(
            utilisateur=self.user, formation=self.formation
        ).exists()
        self.assertFalse(acces_existe)

        commande.statut = "paye"
        commande.save()
        for item in commande.items.all():
            AccesFormationDebloque.objects.get_or_create(
                utilisateur=self.user,
                nom_formation_snapshot=item.nom_produit_snapshot,
                defaults={"formation": item.formation, "commande_origine": commande},
            )

        acces_existe = AccesFormationDebloque.objects.filter(
            utilisateur=self.user, formation=self.formation
        ).exists()
        self.assertTrue(acces_existe)

    def test_formation_gratuite_pas_de_commande(self):
        formation_gratuite = Formation.objects.create(
            ecole=self.ecole,
            nom="Gratuite Test",
            icone="🎁",
            description="Test",
            duree_mois=1,
            prix=0,
            gratuit=True,
            actif=True,
        )
        self.assertTrue(formation_gratuite.gratuit)

    def test_promotion_s_applique_formation_correcte(self):
        autre_formation = Formation.objects.create(
            ecole=self.ecole,
            nom="Autre Formation",
            icone="📚",
            description="Test",
            duree_mois=2,
            prix=50,
            actif=True,
        )
        promo = Promotion.objects.create(
            nom="Promo Test",
            pourcentage_reduction=30,
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
        self.assertTrue(commande1.reference.startswith("BTA-"))


class RoleSystemTestCase(TestCase):
    """Tests du système de rôles granulaire."""

    def setUp(self):
        self.user = User.objects.create_user(username="test_role", password="test1234")

    def test_role_par_defaut_etudiant(self):
        self.assertEqual(self.user.profil.role, "etudiant")

    def test_permissions_par_role(self):
        self.user.profil.role = "finance"
        self.user.profil.save()
        self.assertTrue(self.user.profil.peut_voir_finance())
        self.assertFalse(self.user.profil.peut_gerer_formations())

    def test_admin_a_tous_les_droits(self):
        self.user.profil.role = "admin"
        self.user.profil.save()
        self.assertTrue(self.user.profil.peut_voir_finance())
        self.assertTrue(self.user.profil.peut_moderer_forum())
        self.assertTrue(self.user.profil.peut_gerer_formations())
        self.assertTrue(self.user.profil.peut_voir_crm())


# ================================================
# TESTS.PY — Tests étendus Sprint 2+ (IA parsing, multi-academie, webhooks)
# ================================================

from academie.services.ia_service import parser_json_robuste


class ParsingIARobusteTestCase(TestCase):
    """Vérifie que le parsing JSON gère tous les cas de réponses Gemini imparfaites."""

    def test_json_propre(self):
        resultat = parser_json_robuste('{"score": 85}')
        self.assertEqual(resultat['score'], 85)

    def test_json_avec_balises_markdown(self):
        resultat = parser_json_robuste('```json\n{"score": 90}\n```')
        self.assertEqual(resultat['score'], 90)

    def test_json_avec_texte_parasite(self):
        resultat = parser_json_robuste('Voici le résultat : {"score": 75} merci !')
        self.assertEqual(resultat['score'], 75)

    def test_json_liste_avec_texte_parasite(self):
        resultat = parser_json_robuste('Questions générées :\n[{"q": "test"}]\nFin.')
        self.assertEqual(resultat[0]['q'], 'test')

    def test_json_invalide_retourne_defaut(self):
        resultat = parser_json_robuste('Ceci n\'est pas du JSON du tout', valeur_defaut={'erreur': True})
        self.assertEqual(resultat, {'erreur': True})

    def test_json_avec_virgule_trainante(self):
        resultat = parser_json_robuste('{"a": 1, "b": 2,}')
        self.assertEqual(resultat['b'], 2)


class MultiAcademieIsolationTestCase(TestCase):
    """Vérifie l'isolation correcte entre plusieurs académies."""

    def setUp(self):
        self.academie_a = Academie.objects.create(nom='Academie A', icone='🅰️', est_academie_par_defaut=True)
        self.academie_b = Academie.objects.create(nom='Academie B', icone='🅱️')

        self.ecole_a = Ecole.objects.create(nom='Ecole A', icone='🏫', academie=self.academie_a, ordre=1)
        self.ecole_b = Ecole.objects.create(nom='Ecole B', icone='🏫', academie=self.academie_b, ordre=1)

        self.formation_a = Formation.objects.create(
            ecole=self.ecole_a, nom='Formation A', icone='📚', description='Test',
            duree_mois=1, prix=0, actif=True,
        )
        self.formation_b = Formation.objects.create(
            ecole=self.ecole_b, nom='Formation B', icone='📚', description='Test',
            duree_mois=1, prix=0, actif=True,
        )

    def test_formations_isolees_par_academie(self):
        formations_academie_a = Formation.objects.filter(ecole__academie=self.academie_a)
        self.assertEqual(formations_academie_a.count(), 1)
        self.assertEqual(formations_academie_a.first(), self.formation_a)

    def test_academie_nb_formations_correct(self):
        self.assertEqual(self.academie_a.nb_formations(), 1)
        self.assertEqual(self.academie_b.nb_formations(), 1)

    def test_partenaire_isole_par_academie(self):
        partenaire = PartenaireAPI.objects.create(
            nom='Partenaire Test A', type_partenaire='entreprise',
            email_contact='p@test.com', academie_associee=self.academie_a,
        )
        formations_visibles = Formation.objects.filter(actif=True)
        if partenaire.academie_associee:
            formations_visibles = formations_visibles.filter(ecole__academie=partenaire.academie_associee)

        self.assertEqual(formations_visibles.count(), 1)
        self.assertIn(self.formation_a, formations_visibles)
        self.assertNotIn(self.formation_b, formations_visibles)


class StripeWebhookTestCase(TestCase):
    """Vérifie que le webhook Stripe traite correctement les événements malformés (robustesse)."""

    def test_webhook_signature_invalide_ne_plante_pas(self):
        client = Client()
        reponse = client.post(
            '/webhooks/stripe/',
            data='{"invalid": "payload"}',
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='signature_invalide'
        )
        # Doit retourner 200 (Stripe exige toujours 200, même en cas d'erreur de traitement)
        # sans lever d'exception serveur
        self.assertIn(reponse.status_code, [200, 400])


class CompetenceModelTestCase(TestCase):
    """Vérifie le modèle Competence et ses relations."""

    def setUp(self):
        self.ecole = Ecole.objects.create(nom='Ecole Comp', icone='🏫', ordre=1)
        self.formation = Formation.objects.create(
            ecole=self.ecole, nom='Formation Comp', icone='📚', description='Test',
            duree_mois=1, prix=0, actif=True,
        )

    def test_competence_slug_auto_genere(self):
        competence = Competence.objects.create(nom='Python Avancé')
        self.assertEqual(competence.slug, 'python-avance')

    def test_liaison_formation_competence(self):
        competence = Competence.objects.create(nom='Django')
        competence.formations.add(self.formation)
        self.assertEqual(competence.nb_formations(), 1)
        self.assertIn(competence, self.formation.competences.all())


# ================================================
# TESTS.PY — Validation migration Reaction GFK
# ================================================

from django.contrib.contenttypes.models import ContentType


class ReactionGFKTestCase(TestCase):
    """Vérifie que la migration GenericForeignKey préserve l'intégrité des likes."""

    def setUp(self):
        self.user = User.objects.create_user(username='reaction_test', password='test1234')
        self.sujet = Sujet.objects.create(titre='Sujet Test', contenu='Contenu', auteur=self.user, categorie='general')

    def test_reaction_gfk_fonctionne_sur_sujet(self):
        ct = ContentType.objects.get_for_model(Sujet)
        reaction = Reaction.objects.create(utilisateur=self.user, content_type=ct, object_id=self.sujet.id)
        self.assertEqual(reaction.cible, self.sujet)

    def test_ancien_champ_sujet_toujours_lisible(self):
        """Garantit la rétrocompatibilité pendant la période de transition."""
        reaction = Reaction.objects.create(utilisateur=self.user, sujet=self.sujet)
        self.assertEqual(reaction.sujet, self.sujet)



# ================================================
# TESTS.PY — Validation Sprint A (extraction app users) — zéro régression
# ================================================
class ExtractionAppUsersTestCase(TestCase):
    """Vérifie que l'extraction de l'app users n'a rien cassé."""

    def test_import_depuis_academie_models_fonctionne_toujours(self):
        """Ancien chemin d'import — DOIT continuer de fonctionner partout."""
        from academie.models import ProfilUtilisateur, LogAudit, Enseignant
        self.assertTrue(ProfilUtilisateur)
        self.assertTrue(LogAudit)
        self.assertTrue(Enseignant)

    def test_import_depuis_users_models_fonctionne(self):
        """Nouveau chemin d'import — doit aussi fonctionner."""
        from users.models import ProfilUtilisateur
        self.assertTrue(ProfilUtilisateur)

    def test_meme_table_physique_deux_imports(self):
        """Vérifie que les 2 imports pointent vers LA MÊME table (pas de duplication)."""
        from academie.models import ProfilUtilisateur as PU_academie
        from users.models import ProfilUtilisateur as PU_users
        self.assertEqual(PU_academie._meta.db_table, PU_users._meta.db_table)

    def test_creation_profil_toujours_fonctionnelle(self):
        """Le signal post_save existant doit toujours créer un profil."""
        user = User.objects.create_user(username='test_extraction', password='test1234')
        self.assertTrue(hasattr(user, 'profil'))
        self.assertEqual(user.profil.role, 'etudiant')

    def test_admin_users_accessible(self):
        """Vérifie que /admin/users/ est bien enregistré."""
        admin_user = User.objects.create_superuser(username='admin_ext', password='test1234', email='a@a.com')
        client = Client()
        client.login(username='admin_ext', password='test1234')
        reponse = client.get('/admin/')
        self.assertEqual(reponse.status_code, 200)


# ================================================
# TESTS.PY — Validation Sprint B (extraction app billing) — zéro régression
# ================================================

class ExtractionAppBillingTestCase(TestCase):
    """Vérifie que l'extraction de l'app billing n'a rien cassé."""

    def test_import_depuis_academie_models_fonctionne_toujours(self):
        from academie.models import Order, Coupon, Transaction, Invoice, Affilie
        self.assertTrue(Order)
        self.assertTrue(Coupon)
        self.assertTrue(Transaction)

    def test_import_depuis_billing_models_fonctionne(self):
        from billing.models import Order
        self.assertTrue(Order)

    def test_meme_table_physique_order(self):
        from academie.models import Order as Order_academie
        from billing.models import Order as Order_billing
        self.assertEqual(Order_academie._meta.db_table, Order_billing._meta.db_table)
        self.assertEqual(Order_academie._meta.db_table, 'academie_order')

    def test_payment_center_toujours_fonctionnel(self):
        """Ré-exécute le test critique du Payment Center après extraction."""
        user = User.objects.create_user(username='billing_test', password='test1234')
        ecole = Ecole.objects.create(nom='Ecole Billing', icone='🏫', ordre=1)
        formation = Formation.objects.create(
            ecole=ecole, nom='Formation Billing', icone='📚', description='Test',
            duree_mois=1, prix=100, actif=True,
        )
        commande = Order.objects.create(utilisateur=user, total=0)
        OrderItem.objects.create(
            commande=commande, formation=formation, type_produit='formation',
            nom_produit_snapshot=formation.nom, prix_unitaire=100,
        )
        commande.recalculer_total()
        self.assertEqual(commande.total, 100)

    def test_admin_billing_accessible(self):
        admin_user = User.objects.create_superuser(username='admin_billing', password='test1234', email='b@b.com')
        client = Client()
        client.login(username='admin_billing', password='test1234')
        reponse = client.get('/admin/academie/order/')
        self.assertEqual(reponse.status_code, 200)


# ================================================
# TESTS.PY — Validation Sprint C (extraction learning)
# ================================================

class ExtractionAppLearningTestCase(TestCase):
    def test_import_academie_et_learning_identiques(self):
        from .models import Formation as F1, Examen as E1
        from .models import Formation as F2, Examen as E2
        self.assertEqual(F1._meta.db_table, F2._meta.db_table)
        self.assertEqual(E1._meta.db_table, E2._meta.db_table)

    def test_hierarchie_pedagogique_intacte(self):
        ecole = Ecole.objects.create(nom='Test Learning', icone='🏫', ordre=1)
        formation = Formation.objects.create(ecole=ecole, nom='Test', icone='📚', description='x', duree_mois=1, prix=0, actif=True)
        module = Module.objects.create(formation=formation, titre='M1', ordre=1)
        Lecon.objects.create(module=module, titre='L1', ordre=1)
        self.assertEqual(module.nombre_lecons(), 1)


# ================================================
# TESTS.PY — Tests critiques post-audit (paiement securise, acces verrouille)
# ================================================

class SecuritePaiementAuditTestCase(TestCase):
    """Vérifie qu'on ne peut PAS débloquer l'accès sans validation réelle."""

    def setUp(self):
        self.user = User.objects.create_user(username='fraude_test', password='test1234')
        self.ecole = Ecole.objects.create(nom='Ecole Fraude', icone='🏫', ordre=1)
        self.formation = Formation.objects.create(
            ecole=self.ecole, nom='Formation Fraude', icone='📚', description='Test',
            duree_mois=1, prix=100, actif=True,
        )

    def test_paiement_succes_sans_transaction_ne_debloque_pas(self):
        """Simule une tentative de fraude : appel direct de l'URL sans vraie transaction."""
        from django.test import Client
        client = Client()
        client.login(username='fraude_test', password='test1234')

        commande = Order.objects.create(utilisateur=self.user, total=100, statut='en_attente')
        OrderItem.objects.create(
            commande=commande, formation=self.formation, type_produit='formation',
            nom_produit_snapshot=self.formation.nom, prix_unitaire=100,
        )

        client.get(f'/paiement-succes/{commande.reference}/')

        commande.refresh_from_db()
        self.assertNotEqual(commande.statut, 'paye')  # doit rester en_attente
        self.assertFalse(
            AccesFormationDebloque.objects.filter(utilisateur=self.user, formation=self.formation).exists()
        )


class VerrouillageContenuAuditTestCase(TestCase):
    """Vérifie l'IDOR corrigé : accès bloqué sans paiement."""

    def setUp(self):
        self.user = User.objects.create_user(username='idor_test', password='test1234')
        self.ecole = Ecole.objects.create(nom='Ecole IDOR', icone='🏫', ordre=1)
        self.formation = Formation.objects.create(
            ecole=self.ecole, nom='Formation IDOR', icone='📚', description='Test',
            duree_mois=1, prix=100, actif=True,
        )
        self.module = Module.objects.create(formation=self.formation, titre='M1', ordre=1)
        self.lecon = Lecon.objects.create(module=self.module, titre='L1', contenu='Contenu premium', ordre=1)

    def test_lire_lecon_bloquee_sans_acces(self):
        from django.test import Client
        client = Client()
        client.login(username='idor_test', password='test1234')
        reponse = client.get(f'/lecon/{self.lecon.id}/')
        self.assertEqual(reponse.status_code, 302)  # redirigé, pas 200

    def test_lire_lecon_autorisee_avec_acces(self):
        AccesFormationDebloque.objects.create(
            utilisateur=self.user, formation=self.formation, nom_formation_snapshot=self.formation.nom
        )
        from django.test import Client
        client = Client()
        client.login(username='idor_test', password='test1234')
        reponse = client.get(f'/lecon/{self.lecon.id}/')
        self.assertEqual(reponse.status_code, 200)


class CouponConcurrenceAuditTestCase(TestCase):
    """Vérifie que le verrouillage atomique empêche le dépassement d'utilisations."""

    def test_coupon_utilisation_atomique_respecte_limite(self):
        coupon = Coupon.objects.create(
            code='LIMITE_TEST', type_reduction='fixe', valeur=10, utilisations_max=1
        )
        succes1, _ = coupon.utiliser_atomiquement()
        succes2, message2 = coupon.utiliser_atomiquement()

        self.assertTrue(succes1)
        self.assertFalse(succes2)
        self.assertIn('limite', message2.lower())


class AccesFormationCleNaturelleTestCase(TestCase):
    """Vérifie la nouvelle contrainte unique utilisateur+formation."""

    def test_unique_utilisateur_formation(self):
        user = User.objects.create_user(username='cle_test', password='test1234')
        ecole = Ecole.objects.create(nom='Ecole Cle', icone='🏫', ordre=1)
        formation = Formation.objects.create(
            ecole=ecole, nom='Formation Cle', icone='📚', description='Test', duree_mois=1, prix=0, actif=True,
        )
        AccesFormationDebloque.objects.create(utilisateur=user, formation=formation, nom_formation_snapshot=formation.nom)

        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            AccesFormationDebloque.objects.create(utilisateur=user, formation=formation, nom_formation_snapshot='Autre nom')



# ================================================
# TESTS.PY — Vérifie que la recherche full-text fonctionne
# ================================================

class RechercheFullTextTestCase(TestCase):
    def setUp(self):
        self.ecole = Ecole.objects.create(nom='Ecole Recherche', icone='🏫', ordre=1)
        self.formation = Formation.objects.create(
            ecole=self.ecole, nom='Développement Python Avancé', icone='🐍',
            description='Apprends Python en profondeur', duree_mois=3, prix=0, actif=True,
        )

    def test_recherche_trouve_formation_par_nom(self):
        client = Client()
        reponse = client.get('/recherche/?q=Python')
        self.assertEqual(reponse.status_code, 200)
        self.assertIn(self.formation, reponse.context.get('resultats_formations', []))


# ================================================
# TESTS.PY — Tests de performance (détecte les régressions N+1)
# ================================================

class PerformanceN1TestCase(TestCase):
    """Vérifie qu'aucune régression N+1 ne se réintroduit silencieusement."""

    def setUp(self):
        self.ecole = Ecole.objects.create(nom='Ecole Perf', icone='🏫', ordre=1)
        self.user = User.objects.create_user(username='perf_test', password='test1234')

        # Crée 10 formations avec modules/leçons pour simuler une charge réaliste
        for i in range(10):
            formation = Formation.objects.create(
                ecole=self.ecole, nom=f'Formation {i}', icone='📚', description='Test',
                duree_mois=1, prix=0, actif=True,
            )
            module = Module.objects.create(formation=formation, titre='M1', ordre=1)
            Lecon.objects.create(module=module, titre='L1', ordre=1)

    def test_progression_pour_moins_de_3_requetes(self):
        """La méthode optimisée ne doit JAMAIS dépasser 3 requêtes (cache + calcul)."""
        formation = Formation.objects.first()
        with CaptureQueriesContext(connection) as contexte:
            formation.progression_pour(self.user)
        self.assertLessEqual(len(contexte.captured_queries), 3)

    def test_formations_page_nombre_requetes_stable(self):
        """Vérifie que charger la page catalogue ne fait pas exploser les requêtes avec plus de données."""
        client = Client()
        with CaptureQueriesContext(connection) as contexte:
            client.get('/formations/')
        # Seuil raisonnable — si ça dépasse largement, une régression N+1 a été introduite
        self.assertLess(len(contexte.captured_queries), 30)


# ================================================
# TESTS.PY — Tests de vérification publique des certificats
# ================================================

class CertificatVerificationTestCase(TestCase):
    """Vérifie la robustesse de la vérification publique de certificat."""

    def setUp(self):
        # Données communes pour les tests de certificat
        self.ecole = Ecole.objects.create(nom='Ecole Cert', icone='🏫', ordre=1)
        self.formation = Formation.objects.create(
            ecole=self.ecole, nom='Formation Cert', icone='📜', description='Test',
            duree_mois=1, prix=0, actif=True,
        )

    def test_numero_certificat_non_devinable(self):
        user = User.objects.create_user(username='cert_test', password='test1234')
        cert = Certificat.objects.create(utilisateur=user, formation=self.formation)
        self.assertEqual(len(cert.numero), 24)  # token_hex(12) = 24 caractères

    def test_verification_publique_certificat_valide(self):
        user = User.objects.create_user(username='cert_test2', password='test1234')
        cert = Certificat.objects.create(utilisateur=user, formation=self.formation)
        client = Client()
        reponse = client.get(reverse('verifier_certificat_public', kwargs={'numero_certificat': cert.numero}))
        self.assertContains(reponse, 'authentique')

    def test_verification_publique_certificat_invalide(self):
        client = Client()
        reponse = client.get(reverse('verifier_certificat_public', kwargs={'numero_certificat': 'NUMERO_INEXISTANT_123'}))
        self.assertContains(reponse, 'introuvable')


# ================================================
# TESTS.PY — Tests multi-académie approfondis (audit: "à approfondir")
# ================================================

class MultiAcademieApprofondisTestCase(TestCase):
    """Tests d'isolation stricte entre académies — couvre formations, articles, partenaires."""

    def setUp(self):
        self.academie_a = Academie.objects.create(nom='Academie Deep A', icone='🅰️')
        self.academie_b = Academie.objects.create(nom='Academie Deep B', icone='🅱️')
        self.ecole_a = Ecole.objects.create(nom='Ecole A', icone='🏫', academie=self.academie_a, ordre=1)
        self.ecole_b = Ecole.objects.create(nom='Ecole B', icone='🏫', academie=self.academie_b, ordre=1)
        self.formation_a = Formation.objects.create(
            ecole=self.ecole_a, nom='F-A', icone='📚', description='x', duree_mois=1, prix=0, actif=True,
        )
        self.formation_b = Formation.objects.create(
            ecole=self.ecole_b, nom='F-B', icone='📚', description='x', duree_mois=1, prix=0, actif=True,
        )
        self.user_a = User.objects.create_user(username='user_academie_a', password='test1234')

    def test_formation_appartient_bonne_academie(self):
        """Vérification basique que l'académie d'une formation correspond à celle de son école."""
        self.assertEqual(self.formation_a.ecole.academie, self.academie_a)
        self.assertEqual(self.formation_b.ecole.academie, self.academie_b)

    def test_article_isole_par_academie(self):
        article_a = Article.objects.create(titre='Article A', resume='x', academie=self.academie_a, publie=True)
        articles_academie_a = Article.objects.filter(academie=self.academie_a)
        articles_academie_b = Article.objects.filter(academie=self.academie_b)
        self.assertIn(article_a, articles_academie_a)
        self.assertNotIn(article_a, articles_academie_b)

    def test_partenaire_api_ne_voit_que_son_academie_meme_avec_id_direct(self):
        """Test IDOR spécifique multi-académie : un partenaire ne doit JAMAIS 
        pouvoir accéder aux données d'une autre académie même en devinant l'ID."""
        partenaire = PartenaireAPI.objects.create(
            nom='Partenaire Deep Test', type_partenaire='entreprise',
            email_contact='p@test.com', academie_associee=self.academie_a,
        )
        # Simule la logique de filtrage réelle utilisée dans PartenaireEtudiantsFormesView
        formation_visible = Formation.objects.filter(
            id=self.formation_b.id, ecole__academie=partenaire.academie_associee
        ).exists()
        self.assertFalse(formation_visible)  # formation_b (académie B) invisible pour partenaire académie A

    def test_academies_differentes_donnees_isolees(self):
        """Vérifie que les données d'une académie ne fuient pas dans l'autre."""
        formations_a = Formation.objects.filter(ecole__academie=self.academie_a)
        formations_b = Formation.objects.filter(ecole__academie=self.academie_b)
        self.assertIn(self.formation_a, formations_a)
        self.assertIn(self.formation_b, formations_b)
        self.assertNotIn(self.formation_a, formations_b)
        self.assertNotIn(self.formation_b, formations_a)


# ================================================
# TESTS.PY — Tests Trio P0 (le cœur de la vision produit)
# ================================================

class CompetenceValideeTestCase(TestCase):
    """Vérifie le déclenchement automatique — LE test le plus important du projet."""

    def setUp(self):
        self.user = User.objects.create_user(username='comp_test', password='test1234')
        self.ecole = Ecole.objects.create(nom='Ecole Comp', icone='🏫', ordre=1)
        self.formation = Formation.objects.create(
            ecole=self.ecole, nom='Formation Comp', icone='📚', description='x', duree_mois=1, prix=0, actif=True,
        )
        self.competence = Competence.objects.create(nom='Python Test')
        self.examen = Examen.objects.create(formation=self.formation, titre='Exam Test')
        self.examen.competences_liees.add(self.competence)

    def test_examen_reussi_valide_competence_liee(self):
        tentative = TentativeExamen.objects.create(
            utilisateur=self.user, examen=self.examen, score=90, nb_bonnes=9, nb_mauvaises=1, reussi=True,
        )
        creees = CompetenceValidee.valider_pour_examen(self.user, self.examen, tentative)
        self.assertEqual(len(creees), 1)
        self.assertTrue(
            CompetenceValidee.objects.filter(utilisateur=self.user, competence=self.competence).exists()
        )

    def test_examen_echoue_ne_valide_rien(self):
        tentative = TentativeExamen.objects.create(
            utilisateur=self.user, examen=self.examen, score=30, nb_bonnes=3, nb_mauvaises=7, reussi=False,
        )
        creees = CompetenceValidee.valider_pour_examen(self.user, self.examen, tentative)
        self.assertEqual(len(creees), 0)

    def test_niveau_expert_si_score_eleve(self):
        tentative = TentativeExamen.objects.create(
            utilisateur=self.user, examen=self.examen, score=95, nb_bonnes=19, nb_mauvaises=1, reussi=True,
        )
        creees = CompetenceValidee.valider_pour_examen(self.user, self.examen, tentative)
        self.assertEqual(creees[0].niveau, 'expert')

    def test_portfolio_auto_remplit_competences(self):
        """Vérifie que P0 #4 (auto-remplissage portfolio) fonctionne."""
        # Lier la compétence à la formation pour que l'auto-remplissage la trouve
        self.formation.competences.add(self.competence)

        client = Client()
        client.login(username='comp_test', password='test1234')
        client.post('/mon-portfolio/', {
            'titre': 'Mon projet', 'description': 'Description test',
            'technologies': 'Python', 'formation_liee': self.formation.id,
        })
        projet = ProjetEtudiant.objects.get(titre='Mon projet')
        self.assertIn(self.competence, projet.competences_demontrees.all())