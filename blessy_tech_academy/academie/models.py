# ================================================
# ACADEMIE/MODELS.PY — Modèles racines + pédagogiques
# Réexporte les modèles déplacés vers CRM, FORUM et CONTENT
# pour assurer la compatibilité.
# ================================================

import uuid
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django_ckeditor_5.fields import CKEditor5Field
from simple_history.models import HistoricalRecords
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

# --- Réexport des modèles déplacés vers CRM et FORUM ---
from crm.models import Inscription, InteractionCRM
from forum.models import Sujet, Reponse, Reaction, BadgeForum

# --- Réexport des modèles déplacés vers CONTENT ---
from content.models import Article, OutilRecommande, Temoignage, ProjetEtudiant, Certificat

# --- Imports des autres apps (users, billing) ---
from users.models import ProfilUtilisateur, LogAudit, Enseignant, HistoriqueConversationIA, PushSubscription, NotificationPushEnvoyee
from billing.models import (
    MoyenPaiement, Coupon, Promotion, Order, OrderItem, Invoice,
    Transaction, Refund, AccesFormationDebloque, PlanAbonnement,
    Subscription, Affilie, CommissionAffiliation,
)
from academie.validators import valider_image

# ================================================
# CONSTANTES PARTAGÉES
# ================================================

TYPES_EVALUATION = [
    ('formative', '📝 Formative (auto-évaluation, sans impact certificat)'),
    ('sommative', '🎯 Sommative (compte pour la validation de compétence)'),
    ('finale', '🏆 Examen final (déclenche la certification)'),
]

# ================================================
# MODÈLE : ConnexionUtilisateur
# ================================================
class ConnexionUtilisateur(models.Model):
    utilisateur = models.ForeignKey(
        "auth.User", on_delete=models.CASCADE, related_name="connexions"
    )
    adresse_ip = models.GenericIPAddressField()
    navigateur = models.CharField(max_length=300)
    pays = models.CharField(max_length=100, blank=True)
    ville = models.CharField(max_length=100, blank=True)
    suspecte = models.BooleanField(default=False)
    date_connexion = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'academie'
        db_table = 'academie_connexionutilisateur'
        ordering = ["-date_connexion"]
        verbose_name = "Connexion utilisateur"
        verbose_name_plural = "Connexions utilisateurs"

    def __str__(self):
        return f"{self.utilisateur.username} - {self.date_connexion}"


# ================================================
# MODÈLE — Academie (racine Enterprise Multi-Academy)
# ================================================
class Academie(models.Model):
    nom = models.CharField(max_length=150, unique=True)
    slug = models.SlugField(max_length=150, unique=True, blank=True)
    sous_titre = models.CharField(
        max_length=250, blank=True, help_text="Ex: L'école de la haute technologie moderne d'Haïti"
    )
    icone = models.CharField(max_length=10, default="🎓")
    logo = models.ImageField(
        upload_to='logos/',
        null=True,
        blank=True,
        validators=[valider_image]
    )
    couleur_principale = models.CharField(max_length=7, default="#0B2447")
    couleur_accent = models.CharField(max_length=7, default="#00B4D8")
    domaine_personnalise = models.CharField(
        max_length=200,
        blank=True,
        help_text="Ex: business.blessytechacademy.com (optionnel — sous-domaine dédié)",
    )
    actif = models.BooleanField(default=True)
    est_academie_par_defaut = models.BooleanField(
        default=False,
        help_text="Une seule Academie doit avoir ce champ à True — utilisée en fallback",
    )
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'academie'
        db_table = 'academie_academie'
        verbose_name = "Académie"
        verbose_name_plural = "Académies"
        ordering = ["nom"]

    def __str__(self):
        return f"{self.icone} {self.nom}"

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.nom)
        super().save(*args, **kwargs)

    def nb_ecoles(self):
        return self.ecoles.count()

    def nb_formations(self):
        from academie.models import Formation
        return Formation.objects.filter(ecole__academie=self).count()

    def nb_etudiants(self):
        return ProfilUtilisateur.objects.filter(academies=self, role="etudiant").count()


# ================================================
# MODÈLE — PartenaireAPI
# ================================================
class PartenaireAPI(models.Model):
    nom = models.CharField(max_length=150)
    email_contact = models.EmailField()
    cle_api = models.CharField(max_length=64, unique=True)
    type_partenaire = models.CharField(
        max_length=30,
        choices=[
            ("universite", "Université"),
            ("entreprise", "Entreprise"),
            ("ong", "ONG"),
            ("gouvernement", "Gouvernement"),
        ],
        default="entreprise",
    )
    academie_associee = models.ForeignKey(
        "Academie",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="partenaires_api",
        help_text="Si défini, ce partenaire n'accède qu'aux données de cette académie. Vide = accès toutes académies.",
    )
    scopes = models.JSONField(
        default=list,
        help_text="Liste des permissions accordées à ce partenaire, ex: ['formations.lire']"
    )
    # --- NOUVEAUX CHAMPS ---
    limite_requetes_heure = models.IntegerField(
        default=100,
        help_text="Nombre max de requêtes par heure"
    )
    date_expiration = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date d'expiration de la clé API"
    )
    actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'academie'
        db_table = 'academie_partenaireapi'
        verbose_name = "Partenaire API"
        verbose_name_plural = "Partenaires API"

    def __str__(self):
        return self.nom

    # ================================================
    # MÉTHODES DÉJÀ AJOUTÉES
    # ================================================

    def a_le_scope(self, scope):
        """Vérifie qu'un partenaire a explicitement le droit d'accéder à cette ressource."""
        return scope in (self.scopes or [])

    def faire_tourner_la_cle(self):
        """Génère une nouvelle clé API — invalide immédiatement l'ancienne."""
        import uuid
        self.cle_api = f"bta_{uuid.uuid4().hex}"
        self.save(update_fields=['cle_api'])

    # ================================================
    # NOUVELLES MÉTHODES
    # ================================================

    def a_le_scope(self, scope):
        """Vérifie qu'un partenaire a explicitement le droit d'accéder à cette ressource."""
        return scope in (self.scopes or [])

    def faire_tourner_la_cle(self):
        """Génère une nouvelle clé API — invalide immédiatement l'ancienne."""
        import uuid
        self.cle_api = f"bta_{uuid.uuid4().hex}"
        self.save(update_fields=['cle_api'])
class LogRequetePartenaire(models.Model):
    partenaire = models.ForeignKey(
        PartenaireAPI,
        on_delete=models.CASCADE,
        related_name='requetes',
        help_text="Partenaire ayant effectué l'appel"
    )
    date_creation = models.DateTimeField(
        auto_now_add=True,
        help_text="Date et heure de la requête"
    )
    statut_reponse = models.IntegerField(
        default=200,
        help_text="Code HTTP de la réponse (200, 400, 403, 500...)"
    )
    endpoint = models.CharField(
        max_length=200,
        blank=True,
        help_text="URL de l'endpoint appelé"
    )
    ip_source = models.CharField(
        max_length=45,
        blank=True,
        help_text="Adresse IP d'origine de la requête"
    )
    class Meta:
        app_label = 'academie'
        db_table = 'academie_logrequetepartenaire'
        ordering = ['-date_creation']
        verbose_name = "Log Requête Partenaire"
        verbose_name_plural = "Logs Requêtes Partenaires"

    def __str__(self):
        return f"{self.partenaire.nom} — {self.statut_reponse} ({self.date_creation})"


# ================================================
# MODÈLE — Notification
# ================================================
class Notification(models.Model):
    utilisateur = models.ForeignKey(
        "auth.User", on_delete=models.CASCADE, related_name="notifications"
    )
    titre = models.CharField(max_length=200)
    message = models.TextField()
    lien = models.URLField(blank=True, default="")
    lue = models.BooleanField(default=False)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'academie'
        db_table = 'academie_notification'
        ordering = ["-date_creation"]
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"

    def __str__(self):
        statut = "✓" if self.lue else "●"
        return f"{statut} {self.titre} — {self.utilisateur.username}"

    # ================================================
    # CORRECTIF : Purge automatique (max 100 notifications par utilisateur)
    # ================================================
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        max_notifications = 100
        ids = Notification.objects.filter(utilisateur=self.utilisateur).values_list('id', flat=True).order_by('-date_creation')[max_notifications:]
        if ids:
            Notification.objects.filter(id__in=list(ids)).delete()


# ================================================
# MODÈLES PÉDAGOGIQUES (learning)
# ================================================

class Ecole(models.Model):
    nom = models.CharField(max_length=200)
    icone = models.CharField(max_length=10, default='🏫')
    description = models.TextField(blank=True)
    ordre = models.IntegerField(default=0)
    academie = models.ForeignKey('academie.Academie', on_delete=models.CASCADE, null=True, blank=True, related_name='ecoles')
    # --- NOUVEAUX CHAMPS ---
    est_ecole_phare = models.BooleanField(
        default=False,
        help_text="Écoles à mettre en avant dans la navigation, le SEO et la page d'accueil (IA, Dev, Logistique)"
    )
    description_courte = models.CharField(
        max_length=200, blank=True,
        help_text="Phrase d'accroche pour la page Nos Écoles"
    )

    class Meta:
        app_label = 'academie'
        db_table = 'academie_ecole'
        ordering = ['ordre']
        verbose_name = 'École'
        verbose_name_plural = 'Écoles'

    def __str__(self):
        return f"{self.icone} {self.nom}"


class Formation(models.Model):
    NIVEAUX = [
        ('debutant', 'Débutant'),
        ('intermediaire', 'Intermédiaire'),
        ('avance', 'Avancé'),
        ('professionnel', 'Professionnel'),
        ('expert', 'Expert'),
        ('debutant_avance', 'Débutant → Avancé'),
        ('intermediaire_expert', 'Intermédiaire → Expert'),
    ]

    ecole = models.ForeignKey(Ecole, on_delete=models.CASCADE, related_name='formations', null=True, blank=True)
    nom = models.CharField(max_length=200)
    slug = models.SlugField(max_length=250, unique=True, null=True, blank=True, db_index=True)
    icone = models.CharField(max_length=10, default='📚')
    illustration = models.CharField(max_length=10, blank=True, default='', help_text="Émoji d'illustration (💻 🤖 🔐 📈 ...)")
    description = models.TextField(blank=True)
    duree = models.IntegerField(default=1, help_text="Valeur numérique de la durée")
    duree_unite = models.CharField(
        max_length=10,
        choices=[('heures', 'Heures'), ('jours', 'Jours'), ('semaines', 'Semaines'), ('mois', 'Mois')],
        default='mois'
    )
    prix = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    niveau = models.CharField(max_length=30, choices=NIVEAUX, default='debutant')
    debouches = models.TextField(blank=True)
    prerequis = models.TextField(blank=True)
    certifications = models.TextField(blank=True)
    actif = models.BooleanField(default=True)
    gratuit = models.BooleanField(default=False)
    sequentiel_obligatoire = models.BooleanField(
        default=False,
        help_text="Si activé, l'étudiant doit terminer chaque leçon dans l'ordre avant d'accéder à la suivante"
    )
    formation_upgrade = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    salaire_haiti = models.CharField(max_length=50, blank=True)
    salaire_international = models.CharField(max_length=50, blank=True)
    competences_acquises = models.TextField(blank=True)
    # --- Nouveaux champs pour la page de vente ---
    methode_pedagogique = models.TextField(blank=True, help_text="Ex: 100% pratique, projets réels, feedback formateur")
    criteres_evaluation = models.TextField(blank=True, help_text="Ex: Quiz formatifs, projet pratique, examen final sommatif")
    public_cible = models.CharField(max_length=300, blank=True, help_text="Ex: Débutants, professionnels en reconversion")
    badge_associe = models.CharField(max_length=100, blank=True, help_text="Badge attribué à 100%")
    delivre_certificat = models.BooleanField(default=True, help_text="Cocher si cette formation délivre un certificat")

    class Meta:
        app_label = 'academie'
        db_table = 'academie_formation'
        verbose_name = 'Formation'
        verbose_name_plural = 'Formations'
        indexes = [
            models.Index(fields=['actif', 'niveau']),
            models.Index(fields=['ecole']),
        ]
        # AJOUT : Permissions personnalisées pour Formation
        permissions = [
            ("view_formation_detail", "Peut voir le détail d'une formation"),
            ("edit_formation", "Peut modifier une formation"),
            ("can_delete_formation", "Peut supprimer une formation"),  # ← renommé
            ("publish_formation", "Peut publier une formation"),
            ("manage_formation_content", "Peut gérer le contenu d'une formation (modules, leçons)"),
            ("view_formation_stats", "Peut voir les statistiques d'une formation"),
        ]

    def __str__(self):
        return self.nom

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            base_slug = slugify(self.nom)
            slug_candidat = base_slug
            i = 1
            while Formation.objects.filter(slug=slug_candidat).exclude(pk=self.pk).exists():
                slug_candidat = f"{base_slug}-{i}"
                i += 1
            self.slug = slug_candidat
        super().save(*args, **kwargs)

    def progression_pour(self, utilisateur):
        """Version optimisée — 1 seule requête au lieu de 2, avec cache."""
        from django.core.cache import cache
        from django.db.models import Count, Q

        cache_key = f"progression_formation_{self.id}_user_{utilisateur.id}"
        resultat_cache = cache.get(cache_key)
        if resultat_cache is not None:
            return resultat_cache

        stats = Module.objects.filter(formation=self).aggregate(
            total_lecons=Count('lecons', distinct=True),
            lecons_terminees=Count(
                'lecons',
                filter=Q(
                    lecons__progressions__utilisateur=utilisateur,
                    lecons__progressions__terminee=True
                ),
                distinct=True
            )
        )

        total = stats['total_lecons'] or 0
        if total == 0:
            pourcentage = 0
        else:
            pourcentage = round((stats['lecons_terminees'] / total) * 100)

        cache.set(cache_key, pourcentage, 300)  # 5 minutes
        return pourcentage

    def prix_htg(self):
        """Retourne le prix en HTG arrondi à l'entier."""
        from django.conf import settings
        return int(self.prix * settings.TAUX_USD_HTG)

    def prix_formate(self, devise='USD'):
        """Retourne le prix formaté selon la devise choisie."""
        if devise == 'HTG':
            return f"{self.prix_htg():,} HTG".replace(',', ' ')
        return f"{self.prix:.2f} USD"


class Module(models.Model):
    formation = models.ForeignKey(Formation, on_delete=models.CASCADE, related_name='modules')
    titre = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    ordre = models.IntegerField(default=0)

    class Meta:
        app_label = 'academie'
        db_table = 'academie_module'
        ordering = ['ordre']
        verbose_name = 'Module'
        verbose_name_plural = 'Modules'

    def __str__(self):
        return self.titre

    def nombre_lecons(self):
        return self.lecons.count()


class Lecon(models.Model):
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='lecons')
    titre = models.CharField(max_length=200)
    resume = models.TextField(
        blank=True,
        help_text="1-2 phrases — apparaît dans le programme de la formation"
    )
    contenu = models.TextField(
        blank=True,
        help_text="Contenu complet de la leçon — CKEditor : texte, images, code, tableaux"
    )
    duree_minutes = models.IntegerField(default=10)
    ordre = models.IntegerField(default=0)

    class Meta:
        app_label = 'academie'
        db_table = 'academie_lecon'
        ordering = ['ordre']
        verbose_name = 'Leçon'
        verbose_name_plural = 'Leçons'

    def __str__(self):
        return self.titre

    def est_accessible_pour(self, utilisateur):
        """
        Vérifie si l'utilisateur peut accéder à cette leçon selon 
        l'ordre séquentiel — retourne (accessible: bool, raison: str).
        """
        formation = self.module.formation

        if not formation.sequentiel_obligatoire:
            return True, ""

        # Récupère TOUTES les leçons de la formation, triées par ordre module puis leçon
        toutes_lecons = list(
            Lecon.objects.filter(module__formation=formation)
            .select_related('module')
            .order_by('module__ordre', 'ordre')
        )

        try:
            index_actuel = toutes_lecons.index(self)
        except ValueError:
            return True, ""

        if index_actuel == 0:
            return True, ""  # première leçon, toujours accessible

        lecon_precedente = toutes_lecons[index_actuel - 1]
        terminee = ProgressionLecon.objects.filter(
            utilisateur=utilisateur,
            lecon=lecon_precedente,
            terminee=True
        ).exists()

        if not terminee:
            return False, f"Termine d'abord la leçon « {lecon_precedente.titre} »"

        return True, ""


class ProgressionLecon(models.Model):
    utilisateur = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='progressions')
    lecon = models.ForeignKey(Lecon, on_delete=models.CASCADE, related_name='progressions')
    terminee = models.BooleanField(default=False)
    date_completion = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = 'academie'
        db_table = 'academie_progressionlecon'
        unique_together = ['utilisateur', 'lecon']
        indexes = [
            models.Index(fields=['utilisateur', 'terminee']),
            models.Index(fields=['lecon', 'terminee']),
        ]


class Quiz(models.Model):
    formation = models.ForeignKey(Formation, on_delete=models.CASCADE, null=True, blank=True)
    module = models.ForeignKey(Module, on_delete=models.SET_NULL, null=True, blank=True, related_name='quiz_module')
    titre = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    actif = models.BooleanField(default=True)
    limite_temps_minutes = models.IntegerField(default=0)
    tentatives_max = models.IntegerField(default=0)
    melanger_questions = models.BooleanField(default=True)
    melanger_reponses = models.BooleanField(default=True)
    type_evaluation = models.CharField(max_length=15, choices=TYPES_EVALUATION, default='formative')
    # --- NOUVEAU CHAMP ---
    competences_liees = models.ManyToManyField(
        'Competence',
        blank=True,
        related_name='quiz_lies',
        help_text="Compétences validées si l'étudiant réussit ce quiz (évaluations sommatives/finales)"
    )
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'academie'
        db_table = 'academie_quiz'
        verbose_name = 'Quiz'
        verbose_name_plural = 'Quiz'

    def __str__(self):
        return self.titre

    def contexte(self):
        if self.module:
            return f"{self.module.formation.nom} — Module: {self.module.titre}"
        return self.formation.nom if self.formation else "—"

    @property
    def nombre_questions(self):
        return self.question_set.count()

class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='question_set')
    texte = models.TextField()
    choix_a = models.CharField(max_length=300)
    choix_b = models.CharField(max_length=300)
    choix_c = models.CharField(max_length=300, blank=True)
    choix_d = models.CharField(max_length=300, blank=True)
    bonne_reponse = models.CharField(max_length=1, choices=[('a', 'A'), ('b', 'B'), ('c', 'C'), ('d', 'D')])
    explication = models.TextField(blank=True)
    ordre = models.IntegerField(default=0)

    class Meta:
        app_label = 'academie'
        db_table = 'academie_question'
        ordering = ['ordre']


class ResultatQuiz(models.Model):
    utilisateur = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='resultats_quiz')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    score = models.IntegerField()
    total_questions = models.IntegerField()
    date_passage = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'academie'
        db_table = 'academie_resultatquiz'
        indexes = [
            models.Index(fields=['utilisateur', 'quiz']),
        ]

    def pourcentage(self):
        return round((self.score / self.total_questions) * 100) if self.total_questions else 0


class Parcours(models.Model):
    titre = models.CharField(max_length=200)
    slug = models.SlugField(max_length=250, unique=True, null=True, blank=True, db_index=True)
    icone = models.CharField(max_length=10, default='🚀')
    description = models.TextField(blank=True)
    duree = models.IntegerField(default=12, help_text="Valeur numérique de la durée")
    duree_unite = models.CharField(
        max_length=10,
        choices=[('heures', 'Heures'), ('jours', 'Jours'), ('semaines', 'Semaines'), ('mois', 'Mois')],
        default='mois'
    )
    prix = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    formations = models.ManyToManyField('Formation', blank=True, related_name='parcours_list')
    actif = models.BooleanField(default=True)
    metiers_vises = models.TextField(blank=True, help_text="Métiers visés par ce parcours")
    projets_inclus = models.TextField(blank=True, help_text="Projets concrets inclus dans le parcours")
    certifications_incluses = models.TextField(blank=True, help_text="Certifications délivrées durant le parcours")
    ordre = models.IntegerField(default=0)

    class Meta:
        app_label = 'academie'
        db_table = 'academie_parcours'
        ordering = ['ordre']
        verbose_name = 'Parcours'
        verbose_name_plural = 'Parcours'

    def __str__(self):
        return self.titre

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            base_slug = slugify(self.titre)
            slug_candidat = base_slug
            i = 1
            while Parcours.objects.filter(slug=slug_candidat).exclude(pk=self.pk).exists():
                slug_candidat = f"{base_slug}-{i}"
                i += 1
            self.slug = slug_candidat
        super().save(*args, **kwargs)

    def duree_formatee(self):
        """Retourne la durée formatée (ex: '3 mois', '2 semaines')"""
        return f"{self.duree} {self.get_duree_unite_display()}"

    def prix_htg(self):
        """Retourne le prix en HTG arrondi à l'entier."""
        from django.conf import settings
        return int(self.prix * settings.TAUX_USD_HTG)

    def prix_formate(self, devise='USD'):
        """Retourne le prix formaté selon la devise choisie."""
        if devise == 'HTG':
            return f"{self.prix_htg():,} HTG".replace(',', ' ')
        return f"{self.prix:.2f} USD"  


class Competence(models.Model):
    CATEGORIES = [
        ('technique', '💻 Technique'),
        ('soft_skill', '🤝 Soft Skill'),
        ('outil', '🛠️ Outil/Logiciel'),
        ('methode', '📐 Méthodologie'),
    ]
    nom = models.CharField(max_length=150, unique=True)
    slug = models.SlugField(max_length=150, unique=True, blank=True)
    categorie = models.CharField(max_length=15, choices=CATEGORIES, default='technique')
    description = models.TextField(blank=True)
    icone = models.CharField(max_length=10, default='⚡')
    formations = models.ManyToManyField(Formation, blank=True, related_name='competences')
    modules = models.ManyToManyField(Module, blank=True, related_name='competences')
    lecons = models.ManyToManyField(Lecon, blank=True, related_name='competences')

    class Meta:
        app_label = 'academie'
        db_table = 'academie_competence'
        ordering = ['categorie', 'nom']
        verbose_name = 'Compétence'
        verbose_name_plural = 'Compétences'

    def __str__(self):
        return f"{self.icone} {self.nom}"

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.nom)
        super().save(*args, **kwargs)

    def nb_formations(self):
        return self.formations.count()

    def nb_etudiants_maitrisant(self):
        from django.contrib.auth.models import User
        return User.objects.filter(acces_debloques__formation__in=self.formations.all()).distinct().count()


class LearningOutcome(models.Model):
    formation = models.ForeignKey(Formation, on_delete=models.CASCADE, related_name='learning_outcomes')
    description = models.CharField(max_length=300)
    competence_associee = models.ForeignKey(Competence, on_delete=models.SET_NULL, null=True, blank=True)
    ordre = models.IntegerField(default=0)

    class Meta:
        app_label = 'academie'
        db_table = 'academie_learningoutcome'
        ordering = ['ordre']
        verbose_name = "Résultat d'apprentissage"
        verbose_name_plural = "Résultats d'apprentissage"

    def __str__(self):
        return f"{self.formation.nom} — {self.description[:50]}"


class WorkflowFormation(models.Model):
    ETATS = [
        ('brouillon', '📝 Brouillon'),
        ('en_revision', '🔍 En révision'),
        ('validee', '✅ Validée'),
        ('publiee', '🌐 Publiée'),
        ('suspendue', '⏸️ Suspendue'),
        ('archivee', '📦 Archivée'),
    ]
    TRANSITIONS_AUTORISEES = {
        'brouillon': ['en_revision', 'archivee'],
        'en_revision': ['brouillon', 'validee'],
        'validee': ['publiee', 'brouillon'],
        'publiee': ['suspendue', 'archivee'],
        'suspendue': ['publiee', 'archivee'],
        'archivee': [],
    }

    formation = models.OneToOneField(Formation, on_delete=models.CASCADE, related_name='workflow')
    etat_actuel = models.CharField(max_length=20, choices=ETATS, default='brouillon')
    demande_par = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, related_name='workflows_demandes')
    valide_par = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='workflows_valides')
    checklist_contenu_complet = models.BooleanField(default=False)
    checklist_seo_complet = models.BooleanField(default=False)
    checklist_prix_valide = models.BooleanField(default=False)
    checklist_quiz_present = models.BooleanField(default=False)
    commentaire_revision = models.TextField(blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_derniere_transition = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'academie'
        db_table = 'academie_workflowformation'
        verbose_name = 'Workflow de formation'
        verbose_name_plural = 'Workflows de formations'

    def __str__(self):
        return f"{self.formation.nom} — {self.get_etat_actuel_display()}"

    def peut_transitionner_vers(self, nouvel_etat):
        return nouvel_etat in self.TRANSITIONS_AUTORISEES.get(self.etat_actuel, [])

    def score_checklist(self):
        items = [self.checklist_contenu_complet, self.checklist_seo_complet, self.checklist_prix_valide, self.checklist_quiz_present]
        return round((sum(items) / len(items)) * 100)

    def transitionner(self, nouvel_etat, utilisateur, commentaire=''):
        if not self.peut_transitionner_vers(nouvel_etat):
            return False, f"Transition '{self.etat_actuel}' → '{nouvel_etat}' non autorisée."
        if nouvel_etat == 'publiee' and self.score_checklist() < 100:
            return False, f"Checklist incomplète ({self.score_checklist()}%)."

        ancien_etat = self.etat_actuel
        self.etat_actuel = nouvel_etat
        if nouvel_etat == 'publiee':
            self.valide_par = utilisateur
            self.formation.actif = True
            self.formation.save(update_fields=['actif'])
        elif nouvel_etat in ['suspendue', 'archivee', 'brouillon']:
            self.formation.actif = False
            self.formation.save(update_fields=['actif'])
        if commentaire:
            self.commentaire_revision = commentaire
        self.save()

        from users.models import LogAudit
        LogAudit.objects.create(
            utilisateur=utilisateur, action='publication',
            description=f"Formation '{self.formation.nom}' : {ancien_etat} → {nouvel_etat}",
            objet_type='Formation', objet_id=self.formation.id,
        )
        return True, f"Transition réussie vers '{self.get_etat_actuel_display()}'"


class Examen(models.Model):
    formation = models.ForeignKey(Formation, on_delete=models.CASCADE, related_name='examens')
    titre = models.CharField(max_length=200)
    duree_minutes = models.IntegerField(default=45)
    seuil_reussite = models.IntegerField(default=70)
    tentatives_max = models.IntegerField(default=3)
    competences_evaluees = models.TextField(blank=True)
    competences_liees = models.ManyToManyField(
        'Competence', blank=True, related_name='examens_lies',
        help_text="Compétences validées automatiquement si l'étudiant réussit cet examen"
    )
    type_evaluation = models.CharField(max_length=15, choices=TYPES_EVALUATION, default='sommative')
    actif = models.BooleanField(default=True)
    prerequis = models.TextField(blank=True)
    conditions_utilisation = models.TextField(blank=True)
    xp_recompense = models.IntegerField(default=50)
    certificat_automatique = models.BooleanField(default=True)
    date_disponibilite = models.DateTimeField(null=True, blank=True)
    date_expiration = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = 'academie'
        db_table = 'academie_examen'
        verbose_name = 'Examen'
        verbose_name_plural = 'Examens'
        indexes = [
            models.Index(fields=['formation']),
        ]

    def __str__(self):
        return self.titre

    def academie(self):
        if self.formation and self.formation.ecole:
            return self.formation.ecole.academie
        return None

    @property
    def questions(self):
        return self.questionexamen_set.all()


class QuestionExamen(models.Model):
    examen = models.ForeignKey(Examen, on_delete=models.CASCADE)
    texte = models.TextField()
    type_question = models.CharField(
        max_length=15,
        choices=[('qcm', 'QCM'), ('vrai_faux', 'Vrai/Faux'), ('texte', 'Texte libre')],
        default='qcm'
    )
    ordre = models.IntegerField(default=0)
    points = models.IntegerField(default=10)

    class Meta:
        app_label = 'academie'
        db_table = 'academie_questionexamen'
        ordering = ['ordre']

    def choix_melanges(self):
        import random
        choix = list(self.choixexamen_set.all())
        random.shuffle(choix)
        return choix


class ChoixExamen(models.Model):
    question = models.ForeignKey(QuestionExamen, on_delete=models.CASCADE)
    texte = models.CharField(max_length=300)
    est_correct = models.BooleanField(default=False)

    class Meta:
        app_label = 'academie'
        db_table = 'academie_choixexamen'


class TentativeExamen(models.Model):
    utilisateur = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='tentatives_examen')
    examen = models.ForeignKey(Examen, on_delete=models.CASCADE, related_name='tentatives')
    score = models.IntegerField(default=0)
    nb_bonnes = models.IntegerField(default=0)
    nb_mauvaises = models.IntegerField(default=0)
    temps_utilise = models.IntegerField(default=0)
    reussi = models.BooleanField(default=False)
    date_passage = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'academie'
        db_table = 'academie_tentativeexamen'
        ordering = ['-date_passage']

    def academie(self):
        return self.examen.academie() if self.examen else None

    @property
    def pourcentage(self):
        total = self.nb_bonnes + self.nb_mauvaises
        return round((self.nb_bonnes / total) * 100) if total else 0


# ================================================
# MODELS.PY — Notes personnelles étudiant sur une leçon
# ================================================

class NoteLecon(models.Model):
    """Note personnelle qu'un étudiant prend pendant sa lecture — privée."""

    utilisateur = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='notes_lecons')
    lecon = models.ForeignKey(Lecon, on_delete=models.CASCADE, related_name='notes_etudiants')
    contenu = models.TextField()
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Note de leçon'
        verbose_name_plural = 'Notes de leçons'
        ordering = ['-date_modification']
        unique_together = ['utilisateur', 'lecon']   # ← AJOUTÉ

    def __str__(self):
        return f"Note de {self.utilisateur.username} sur {self.lecon.titre}"


# ================================================
# MODELS.PY — Streak (série quotidienne d'apprentissage)
# Mécanisme de rétention type Duolingo
# ================================================

class StreakEtudiant(models.Model):
    """Suivi de la série de jours consécutifs d'activité d'un étudiant."""

    utilisateur = models.OneToOneField('auth.User', on_delete=models.CASCADE, related_name='streak')
    jours_consecutifs = models.IntegerField(default=0)
    record_jours_consecutifs = models.IntegerField(default=0)
    derniere_activite = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = 'Série étudiant'
        verbose_name_plural = 'Séries étudiants'

    def __str__(self):
        return f"{self.utilisateur.username} — {self.jours_consecutifs} jour(s)"

    def enregistrer_activite_jour(self):
        """Appelé à chaque action pédagogique (leçon terminée, quiz passé)."""
        aujourdhui = timezone.now().date()

        if self.derniere_activite == aujourdhui:
            return  # déjà comptée aujourd'hui

        hier = aujourdhui - timezone.timedelta(days=1)
        if self.derniere_activite == hier:
            self.jours_consecutifs += 1
        else:
            self.jours_consecutifs = 1

        self.record_jours_consecutifs = max(self.record_jours_consecutifs, self.jours_consecutifs)
        self.derniere_activite = aujourdhui
        self.save()


# ================================================
# MODELS.PY — Gradebook / Suivi des notes des étudiants
# ================================================

class GradebookEntry(models.Model):
    """Note attribuée à un étudiant pour une formation, par un formateur."""

    formation = models.ForeignKey('Formation', on_delete=models.CASCADE, related_name='grades')
    etudiant = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='grades')
    formateur = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='grades_attribuees')
    note = models.DecimalField(max_digits=5, decimal_places=2, help_text="Note sur 20")
    appreciation = models.TextField(blank=True, help_text="Commentaire qualitatif")
    date_attribution = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['formation', 'etudiant']
        ordering = ['-date_attribution']
        verbose_name = 'Note Gradebook'
        verbose_name_plural = 'Notes Gradebook'

    def __str__(self):
        return f"{self.etudiant.username} — {self.formation.nom} : {self.note}/20"


# ================================================
# MODELS.PY — Mentorat : Disponibilités et réservations
# ================================================

class DisponibiliteMentor(models.Model):
    """Créneau de disponibilité d'un formateur pour du mentorat."""
    formateur = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='disponibilites_mentorat')
    date = models.DateField()
    heure_debut = models.TimeField()
    heure_fin = models.TimeField()
    actif = models.BooleanField(default=True)

    class Meta:
        ordering = ['date', 'heure_debut']
        verbose_name = 'Disponibilité mentor'
        verbose_name_plural = 'Disponibilités mentors'

    def __str__(self):
        return f"{self.formateur.username} — {self.date} {self.heure_debut}-{self.heure_fin}"


class ReservationMentorat(models.Model):
    """Réservation d'un créneau par un étudiant."""
    STATUTS = [
        ('en_attente', 'En attente'),
        ('confirmee', 'Confirmée'),
        ('annulee', 'Annulée'),
        ('terminee', 'Terminée'),
    ]
    disponibilite = models.ForeignKey(DisponibiliteMentor, on_delete=models.CASCADE, related_name='reservations')
    etudiant = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='reservations_mentorat')
    statut = models.CharField(max_length=20, choices=STATUTS, default='en_attente')
    sujet = models.CharField(max_length=200)
    notes = models.TextField(blank=True)
    date_reservation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_reservation']
        verbose_name = 'Réservation mentorat'
        verbose_name_plural = 'Réservations mentorat'
        indexes = [
            models.Index(fields=['etudiant']),
        ]

    def __str__(self):
        return f"{self.etudiant.username} → {self.disponibilite.formateur.username} ({self.get_statut_display()})"


# ================================================
# MODELS.PY — CompetenceValidee (LE MAILLON CENTRAL de la vision produit)
# "Ne pas seulement apprendre une compétence. Être capable de la démontrer."
# Chaque ligne = une preuve horodatée, traçable, vérifiable qu'un 
# utilisateur maîtrise réellement une compétence précise.
# ================================================

class CompetenceValidee(models.Model):
    """
    Preuve traçable qu'un utilisateur a démontré une compétence.
    C'est CE modèle qui transforme "j'ai réussi un quiz" en 
    "je maîtrise Python" — visible sur profil, portfolio, recrutement.
    """

    SOURCES = [
        ('examen', '🎯 Examen réussi'),
        ('quiz', '📝 Quiz réussi'),
        ('projet', '💼 Projet évalué par un formateur'),
        ('formation_completee', '🎓 Formation terminée à 100%'),
        ('validation_manuelle', '✍️ Validée manuellement par un admin/formateur'),
    ]

    NIVEAUX = [
        ('acquis', '✅ Acquis'),
        ('confirme', '⭐ Confirmé'),
        ('expert', '🏆 Expert'),
    ]

    utilisateur = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='competences_validees')
    competence = models.ForeignKey(Competence, on_delete=models.CASCADE, related_name='validations')

    source_type = models.CharField(max_length=25, choices=SOURCES)
    niveau = models.CharField(max_length=15, choices=NIVEAUX, default='acquis')

    # Traçabilité de la preuve — au moins UN de ces champs est rempli selon la source
    examen_origine = models.ForeignKey('Examen', on_delete=models.SET_NULL, null=True, blank=True, related_name='competences_declenchees')
    quiz_origine = models.ForeignKey('Quiz', on_delete=models.SET_NULL, null=True, blank=True)
    formation_origine = models.ForeignKey('Formation', on_delete=models.SET_NULL, null=True, blank=True)
    projet_origine = models.ForeignKey('ProjetEtudiant', on_delete=models.SET_NULL, null=True, blank=True)
    validee_par = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='competences_validees_par_moi')

    score_obtenu = models.IntegerField(null=True, blank=True, help_text="Score/pourcentage au moment de la validation, si applicable")
    date_validation = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['utilisateur', 'competence', 'source_type', 'examen_origine', 'quiz_origine']
        ordering = ['-date_validation']
        verbose_name = 'Compétence validée'
        verbose_name_plural = 'Compétences validées'
        indexes = [
            models.Index(fields=['utilisateur', 'competence']),
            models.Index(fields=['utilisateur', 'date_validation']),
        ]

    def __str__(self):
        return f"{self.utilisateur.username} — {self.competence.nom} ({self.get_niveau_display()})"

    @staticmethod
    def valider_pour_examen(utilisateur, examen, tentative):
        """
        Point d'entrée unique — appelé automatiquement quand un examen 
        est réussi. Crée une CompetenceValidee pour CHAQUE compétence 
        liée à cet examen (via le nouveau FK M2M Examen.competences_liees).
        """
        if not tentative.reussi:
            return []

        niveau = 'expert' if tentative.pourcentage >= 90 else 'confirme' if tentative.pourcentage >= 75 else 'acquis'
        creees = []

        for competence in examen.competences_liees.all():
            obj, cree = CompetenceValidee.objects.get_or_create(
                utilisateur=utilisateur, competence=competence,
                source_type='examen', examen_origine=examen, quiz_origine=None,
                defaults={
                    'niveau': niveau, 'formation_origine': examen.formation,
                    'score_obtenu': tentative.pourcentage,
                }
            )
            if cree:
                creees.append(obj)
            elif obj.score_obtenu and tentative.pourcentage > obj.score_obtenu:
                # Meilleur score obtenu lors d'un nouvel essai : upgrade la preuve
                obj.score_obtenu = tentative.pourcentage
                obj.niveau = niveau
                obj.date_validation = timezone.now()
                obj.save()

        return creees

    @staticmethod
    def valider_pour_formation_completee(utilisateur, formation):
        """Déclenché quand une formation est terminée à 100% — valide toutes ses compétences liées."""
        creees = []
        for competence in formation.competences.all():
            obj, cree = CompetenceValidee.objects.get_or_create(
                utilisateur=utilisateur, competence=competence,
                source_type='formation_completee', formation_origine=formation,
                examen_origine=None, quiz_origine=None,
                defaults={'niveau': 'acquis'}
            )
            if cree:
                creees.append(obj)
        return creees

    @staticmethod
    def valider_pour_quiz(utilisateur, quiz, resultat_quiz):
        """
        Symétrique de valider_pour_examen() — traite maintenant les Quiz
        de la même façon que les Examens pour la validation de compétences.
        Nécessite que le quiz ait des compétences liées (via competences_liees).
        """
        if quiz.type_evaluation not in ['sommative', 'finale']:
            return []  # formatif = pratique, ne valide pas encore

        pourcentage = resultat_quiz.pourcentage()
        seuil_reussite = 70  # seuil par défaut cohérent avec Examen
        if pourcentage < seuil_reussite:
            return []

        niveau = 'expert' if pourcentage >= 90 else 'confirme' if pourcentage >= 75 else 'acquis'
        creees = []

        for competence in quiz.competences_liees.all():
            obj, cree = CompetenceValidee.objects.get_or_create(
                utilisateur=utilisateur, competence=competence,
                source_type='quiz', quiz_origine=quiz, examen_origine=None,
                defaults={'niveau': niveau, 'formation_origine': quiz.formation, 'score_obtenu': pourcentage}
            )
            if cree:
                creees.append(obj)

        return creees
    


# ================================================
# MODELS.PY — SoumissionProjet — Évaluation pratique par formateur
# Corrige la faiblesse P1 : "aucune évaluation par livrable concret"
# ================================================

class SoumissionProjet(models.Model):
    """Soumission d'un projet pratique par un étudiant, évalué par un formateur."""

    STATUTS = [
        ('en_attente', '⏳ En attente d\'évaluation'),
        ('validee', '✅ Validée'),
        ('a_revoir', '🔄 À revoir'),
        ('refusee', '❌ Refusée'),
    ]

    utilisateur = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='soumissions_projets')
    formation = models.ForeignKey('Formation', on_delete=models.CASCADE, related_name='soumissions')
    module = models.ForeignKey('Module', on_delete=models.SET_NULL, null=True, blank=True)
    titre = models.CharField(max_length=200)
    description = models.TextField()
    lien_livrable = models.URLField(help_text="Lien GitHub, Figma, démo, etc.")
    fichier_livrable = models.FileField(upload_to='soumissions_projets/', null=True, blank=True)

    statut = models.CharField(max_length=15, choices=STATUTS, default='en_attente')
    evalue_par = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='projets_evalues')
    feedback_formateur = models.TextField(blank=True)
    note_sur_20 = models.IntegerField(null=True, blank=True)
    competences_a_valider = models.ManyToManyField('Competence', blank=True, related_name='soumissions_liees')

    date_soumission = models.DateTimeField(auto_now_add=True)
    date_evaluation = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-date_soumission']
        verbose_name = 'Soumission de projet'
        verbose_name_plural = 'Soumissions de projets'
        indexes = [models.Index(fields=['statut']), models.Index(fields=['utilisateur'])]

    def __str__(self):
        return f"{self.titre} — {self.utilisateur.username} ({self.get_statut_display()})"

    def valider(self, formateur, note=None, feedback=''):
        """Valide la soumission — déclenche CompetenceValidee automatiquement."""
        self.statut = 'validee'
        self.evalue_par = formateur
        self.date_evaluation = timezone.now()
        if note is not None:
            self.note_sur_20 = note
        if feedback:
            self.feedback_formateur = feedback
        self.save()

        niveau = 'expert' if (note and note >= 18) else 'confirme' if (note and note >= 14) else 'acquis'
        for competence in self.competences_a_valider.all():
            CompetenceValidee.objects.get_or_create(
                utilisateur=self.utilisateur, competence=competence,
                source_type='projet', projet_origine=None, formation_origine=self.formation,
                defaults={'niveau': niveau, 'score_obtenu': note, 'validee_par': formateur}
            )

        # Auto-crée un ProjetEtudiant dans le portfolio si validé (ferme la boucle P0 #4)
        ProjetEtudiant.objects.get_or_create(
            auteur=self.utilisateur, titre=self.titre,
            defaults={
                'description': self.description, 'lien': self.lien_livrable,
                'formation_liee': self.formation,
            }
        )


# ================================================
# MODELS.PY — Cohorte (pilote réel — aucune statistique inventée)
# Toutes les méthodes ci-dessous interrogent la base réelle, jamais 
# de valeur codée en dur
# ================================================

class Cohorte(models.Model):
    """Groupe réel d'étudiants suivant un lot de formations ensemble (ex: pilote 8 personnes)."""

    nom = models.CharField(max_length=150, help_text="Ex: Cohorte Pilote 2026")
    formations = models.ManyToManyField('Formation', related_name='cohortes')
    membres = models.ManyToManyField('auth.User', related_name='cohortes', blank=True)
    date_debut = models.DateField()
    date_fin_prevue = models.DateField()
    actif = models.BooleanField(default=True)

    # --- NOUVEAU CHAMP AJOUTÉ ---
    frais_montant = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Montant des frais de certification en USD"
    )
    # -------------------------

    class Meta:
        verbose_name = 'Cohorte'
        verbose_name_plural = 'Cohortes'
        ordering = ['-date_debut']

    def __str__(self):
        return self.nom

    def nb_inscrits(self):
        return self.membres.count()

    def nb_presents(self):
        return self.membres.filter(progressions__isnull=False).distinct().count()

    def progression_moyenne(self):
        from django.db.models import Count, Q
        membres_ids = list(self.membres.values_list('id', flat=True))
        formations_ids = list(self.formations.values_list('id', flat=True))
        if not membres_ids or not formations_ids:
            return 0
        stats = ProgressionLecon.objects.filter(
            utilisateur_id__in=membres_ids,
            lecon__module__formation_id__in=formations_ids
        ).aggregate(
            total=Count('id'),
            terminees=Count('id', filter=Q(terminee=True))
        )
        if not stats['total']:
            return 0
        return round((stats['terminees'] / stats['total']) * 100)

    def nb_completions_100pct(self):
        from django.db.models import Count, Q
        membres_ids = list(self.membres.values_list('id', flat=True))
        formations_ids = list(self.formations.values_list('id', flat=True))
        if not membres_ids or not formations_ids:
            return 0
        resultats = ProgressionLecon.objects.filter(
            utilisateur_id__in=membres_ids,
            lecon__module__formation_id__in=formations_ids
        ).values('utilisateur_id').annotate(
            total=Count('id'),
            terminees=Count('id', filter=Q(terminee=True))
        )
        complets = sum(1 for r in resultats if r['total'] > 0 and r['total'] == r['terminees'])
        return complets

    def moyenne_examens(self):
        from django.db.models import Avg
        resultat = TentativeExamen.objects.filter(
            utilisateur__in=self.membres.all(),
            examen__formation__in=self.formations.all(),
            reussi=True
        ).aggregate(m=Avg('score'))
        return round(resultat['m'] or 0, 1)

    def nb_projets_realises(self):
        return ProjetEtudiant.objects.filter(
            auteur__in=self.membres.all(), formation_liee__in=self.formations.all()
        ).count()

    def nb_certificats_delivres(self):
        return Certificat.objects.filter(
            utilisateur__in=self.membres.all(), formation__in=self.formations.all()
        ).count()

    def nb_temoignages_publies(self):
        # Version optimisée (plus de boucle Python)
        return Temoignage.objects.filter(
            formation_suivie__in=self.formations.all(),
            approuve=True,
            prenom_nom__in=self.membres.values_list('username', flat=True)
        ).count()

    def nb_competences_validees(self):
        return CompetenceValidee.objects.filter(
            utilisateur__in=self.membres.all(), formation_origine__in=self.formations.all()
        ).values('competence').distinct().count()



# ================================================
# MODELS.PY — Workflow Témoignage (jamais de publication automatique)
# ================================================

class DemandeTemoignage(models.Model):
    STATUTS = [
        ('envoyee', '📤 Envoyée'), ('repondue', '✍️ Répondue'),
        ('consentement_donne', '✅ Consentement donné'), ('validee_admin', '👍 Validée par admin'),
        ('publiee', '🌐 Publiée'), ('refusee', '❌ Refusée par le participant'),
    ]

    utilisateur = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='demandes_temoignage')
    formation = models.ForeignKey('Formation', on_delete=models.SET_NULL, null=True, blank=True)
    statut = models.CharField(max_length=20, choices=STATUTS, default='envoyee')
    reponse_texte = models.TextField(blank=True)
    note = models.IntegerField(null=True, blank=True, choices=[(i, str(i)) for i in range(1, 6)])
    consentement_publication = models.BooleanField(default=False)
    temoignage_publie = models.ForeignKey('academie.Temoignage', on_delete=models.SET_NULL, null=True, blank=True)
    date_envoi = models.DateTimeField(auto_now_add=True)
    date_reponse = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Demande de témoignage'
        verbose_name_plural = 'Demandes de témoignage'

    def __str__(self):
        return f"Demande à {self.utilisateur.username} — {self.get_statut_display()}"


# ================================================
# MODELS.PY — Parrainage (referral communautaire, distinct d'Affilie B2B)
# ================================================

class Parrainage(models.Model):
    """Un apprenant invite un ami — traçable, récompensable simplement."""

    STATUTS = [('invite', '📨 Invité'), ('inscrit', '✅ Inscrit'), ('actif', '🎯 Devenu actif')]

    parrain = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='parrainages_envoyes')
    filleul_email = models.EmailField()
    filleul_utilisateur = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='parrainage_origine')
    code_parrainage = models.CharField(max_length=20, unique=True, editable=False)
    statut = models.CharField(max_length=15, choices=STATUTS, default='invite')
    date_invitation = models.DateTimeField(auto_now_add=True)
    date_conversion = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Parrainage'
        verbose_name_plural = 'Parrainages'

    def __str__(self):
        return f"{self.parrain.username} → {self.filleul_email} ({self.get_statut_display()})"

    def save(self, *args, **kwargs):
        if not self.code_parrainage:
            import uuid
            self.code_parrainage = f"REF-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)


# ================================================
# MODELS.PY — Partenaire (vitrine publique de confiance)
# Distinct de PartenaireAPI (technique/API) — celui-ci est 100% marketing/confiance
# ================================================

class Partenaire(models.Model):
    TYPES = [('entreprise', '🏢 Entreprise'), ('institution', '🏛️ Institution'), ('ong', '🤝 ONG'), ('media', '📰 Média')]

    nom = models.CharField(max_length=200)
    type_partenaire = models.CharField(max_length=15, choices=TYPES, default='entreprise')
    logo = models.ImageField(upload_to='partenaires/logos/', null=True, blank=True)
    description = models.CharField(max_length=250, blank=True)
    url_site = models.URLField(blank=True)
    actif = models.BooleanField(default=True)
    ordre = models.IntegerField(default=0)

    class Meta:
        ordering = ['ordre']
        verbose_name = 'Partenaire'
        verbose_name_plural = 'Partenaires'

    def __str__(self):
        return self.nom


# ================================================
# MODELS.PY — Programme Ambassadeur
# ================================================

class Ambassadeur(models.Model):
    NIVEAUX = [
        ('pilote', '🚀 Pilote fondateur'),
        ('actif', '⭐ Ambassadeur actif'),
        ('elite', '🏆 Ambassadeur élite'),
    ]

    utilisateur = models.OneToOneField('auth.User', on_delete=models.CASCADE, related_name='statut_ambassadeur')
    niveau = models.CharField(max_length=15, choices=NIVEAUX, default='pilote')
    citation_mise_en_avant = models.CharField(max_length=250, blank=True, help_text="Phrase courte affichée publiquement")
    photo = models.ImageField(upload_to='ambassadeurs/', null=True, blank=True)
    visible_publiquement = models.BooleanField(default=False, help_text="Nécessite le consentement explicite")
    date_nomination = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Ambassadeur'
        verbose_name_plural = 'Ambassadeurs'

    def __str__(self):
        return f"{self.utilisateur.username} — {self.get_niveau_display()}"


# ================================================
# MODELS.PY — Outil / Logiciel enseigné
# ================================================

class Outil(models.Model):
    """Logiciel/outil concret enseigné dans une formation (Excel, VS Code, ChatGPT, SAP...)."""
    nom = models.CharField(max_length=100)
    icone = models.CharField(max_length=10, default='🛠️')
    formations = models.ManyToManyField('Formation', blank=True, related_name='outils_enseignes')
    site_officiel = models.URLField(blank=True)

    class Meta:
        verbose_name = 'Outil pédagogique'
        verbose_name_plural = 'Outils pédagogiques'
        ordering = ['nom']

    def __str__(self):
        return f"{self.icone} {self.nom}"

# ================================================
# MODELS.PY — Étude de Cas
# ================================================

class EtudeDeCas(models.Model):
    """Cas pratique concret illustrant l'application d'une formation."""
    DIFFICULTES = [('debutant', '🌱 Débutant'), ('intermediaire', '⚡ Intermédiaire'), ('avance', '🔥 Avancé')]

    formation = models.ForeignKey('Formation', on_delete=models.CASCADE, related_name='etudes_de_cas')
    titre = models.CharField(max_length=200)
    description = models.TextField()
    probleme = models.TextField(help_text="Problème posé")
    solution = models.TextField(help_text="Solution apportée")
    resultat = models.TextField(blank=True, help_text="Résultat concret obtenu")
    difficulte = models.CharField(max_length=15, choices=DIFFICULTES, default='intermediaire')
    contexte = models.TextField(blank=True, help_text="Situation professionnelle réelle ou réaliste")
    objectif = models.TextField(blank=True, help_text="Ce que l'étudiant doit résoudre/produire")
    module_lie = models.ForeignKey('Module', on_delete=models.SET_NULL, null=True, blank=True)
    ordre = models.IntegerField(default=0)

    class Meta:
        ordering = ['ordre']
        verbose_name = 'Étude de cas'
        verbose_name_plural = 'Études de cas'

    def __str__(self):
        return f"{self.titre} — {self.formation.nom}"


# ================================================
# MODELS.PY — Evenement (webinaires, hackathons, sessions live)
# Prépare l'extensibilité listée : "webinaires, classes virtuelles, hackathons"
# ================================================

class Evenement(models.Model):
    TYPES = [('webinaire', '🎥 Webinaire'), ('hackathon', '💻 Hackathon'), ('atelier', '🛠️ Atelier'), ('remise_certificats', '🎓 Remise de certificats')]

    titre = models.CharField(max_length=200)
    type_evenement = models.CharField(max_length=20, choices=TYPES, default='webinaire')
    description = models.TextField()
    date_debut = models.DateTimeField()
    date_fin = models.DateTimeField(null=True, blank=True)
    lien_inscription = models.URLField(blank=True)
    lien_visio = models.URLField(blank=True)
    formation_liee = models.ForeignKey('Formation', on_delete=models.SET_NULL, null=True, blank=True)
    image = models.ImageField(upload_to='evenements/', null=True, blank=True)
    publie = models.BooleanField(default=False)

    class Meta:
        ordering = ['date_debut']
        verbose_name = 'Événement'
        verbose_name_plural = 'Événements'

    def __str__(self):
        return self.titre

    def est_passe(self):
        return timezone.now() > (self.date_fin or self.date_debut)


# ================================================
# Registre canonique des inscriptions (Enrollment)
# ================================================

class Enrollment(models.Model):
    """
    Registre canonique d'inscription — répond à UNE seule question :
    "Cet utilisateur est-il inscrit à cette formation, et pourquoi ?"
    Distinct de :
    - AccesFormationDebloque (technique, peut être dérivé de ceci)
    - ProgressionLecon (mesure l'avancement, pas le droit d'accès)
    - Certificat (résultat final, pas la condition d'accès)
    """

    ORIGINES = [
        ('achat', '💰 Achat payant'), ('gratuit', '🎁 Formation gratuite'),
        ('cohorte', '👥 Cohorte pilote'), ('offert_admin', '🎟️ Offert par admin'),
        ('parcours', '🚀 Inclus dans un parcours'),
    ]
    STATUTS = [('actif', '✅ Actif'), ('suspendu', '⏸️ Suspendu'), ('termine', '🏁 Terminé'), ('expire', '⏳ Expiré')]

    utilisateur = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='enrollments')
    formation = models.ForeignKey('academie.Formation', on_delete=models.CASCADE, related_name='enrollments')
    origine = models.CharField(max_length=20, choices=ORIGINES)
    statut = models.CharField(max_length=15, choices=STATUTS, default='actif')

    commande_origine = models.ForeignKey('academie.Order', on_delete=models.SET_NULL, null=True, blank=True)
    cohorte_origine = models.ForeignKey('academie.Cohorte', on_delete=models.SET_NULL, null=True, blank=True)
    accorde_par = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='enrollments_accordes')

    date_inscription = models.DateTimeField(auto_now_add=True)
    date_expiration = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['utilisateur', 'formation']
        verbose_name = 'Inscription (Enrollment)'
        verbose_name_plural = 'Inscriptions (Enrollments)'
        indexes = [
            models.Index(fields=['utilisateur', 'statut']),
            models.Index(fields=['formation', 'statut']),
        ]

    def __str__(self):
        return f"{self.utilisateur.username} → {self.formation.nom} ({self.get_statut_display()})"

    def est_actif(self):
        if self.statut != 'actif':
            return False
        if self.date_expiration and timezone.now() > self.date_expiration:
            return False
        return True

    @staticmethod
    def inscrire(utilisateur, formation, origine, **kwargs):
        """
        Point d'entrée UNIQUE pour toute inscription — remplace les créations 
        dispersées d'AccesFormationDebloque dans le code existant.
        Crée AUSSI l'AccesFormationDebloque dérivé pour rétrocompatibilité totale.
        """
        enrollment, cree = Enrollment.objects.get_or_create(
            utilisateur=utilisateur, formation=formation,
            defaults={'origine': origine, **kwargs}
        )
        # Dérive automatiquement l'accès technique existant (zéro casse)
        AccesFormationDebloque.objects.get_or_create(
            utilisateur=utilisateur, formation=formation,
            defaults={'nom_formation_snapshot': formation.nom, 'commande_origine': kwargs.get('commande_origine')}
        )
        return enrollment


# ================================================
# REGISTRE D'ÉMISSION IMMUABLE (append‑only)
# ================================================

class RegistreEmissionCertificat(models.Model):
    """
    Journal immuable de tout événement affectant un certificat.
    Ce modèle est en écriture seule : une fois créé, il ne peut être ni modifié ni supprimé.
    """
    ACTIONS = [
        ('emission', '✅ Émission'),
        ('revocation', '❌ Révocation'),
        ('verification_externe', '🔍 Vérification consultée'),
    ]

    certificat = models.ForeignKey(
        'Certificat',
        on_delete=models.PROTECT,
        related_name='registre'
    )
    action = models.CharField(max_length=25, choices=ACTIONS)
    effectue_par = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True
    )
    details = models.TextField(blank=True)
    adresse_ip = models.GenericIPAddressField(null=True, blank=True)
    date_evenement = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'academie'
        db_table = 'academie_registre_emission_certificat'
        ordering = ['date_evenement']
        verbose_name = "Registre d'émission certificat"
        verbose_name_plural = "Registre d'émission certificats"

    def __str__(self):
        return f"{self.get_action_display()} — {self.certificat.numero} — {self.date_evenement:%d/%m/%Y}"

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValueError("❌ Le registre d'émission est immuable — modification interdite.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError("❌ Le registre d'émission est immuable — suppression interdite.")
    

# ================================================
# MODELS.PY — EligibiliteCertification (processus contrôlé pour cohortes)
# ================================================

class EligibiliteCertification(models.Model):
    """
    Processus contrôlé de certification pour les membres d'une cohorte pilote.
    L'étudiant doit payer des frais de certification et obtenir une validation
    administrative avant que le Certificat final soit émis.
    """

    utilisateur = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='eligibilites_certification'
    )
    formation = models.ForeignKey(
        'Formation',
        on_delete=models.CASCADE,
        related_name='eligibilites_certification'
    )
    cohorte = models.ForeignKey(
        'Cohorte',
        on_delete=models.CASCADE,
        related_name='eligibilites_certification',
        help_text="Ce processus contrôlé (frais + validation admin) s'applique UNIQUEMENT aux membres d'une cohorte"
    )

    frais_paye = models.BooleanField(default=False, help_text="Frais de certification acquittés")
    valide_par = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='certifications_validees'
    )
    date_validation = models.DateTimeField(null=True, blank=True)
    certificat_genere = models.ForeignKey(
        'Certificat',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='eligibilite_origine'
    )
    date_creation = models.DateTimeField(auto_now_add=True)

    # --- NOUVEAUX CHAMPS ---
    note_theorique = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Note de l'examen théorique sur 100")
    note_projet = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Note du projet sur 100")
    moyenne_finale = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Moyenne pondérée ou simple des notes")
    STATUTS = [
        ('en_cours', 'En cours'),
        ('eligible', 'Éligible (certificat prêt)'),
        ('certifie', 'Certifié'),
        ('refuse', 'Refusé'),
    ]
    statut = models.CharField(max_length=10, choices=STATUTS, default='en_cours')

    class Meta:
        app_label = 'academie'
        db_table = 'academie_eligibilitecertification'
        unique_together = ['utilisateur', 'formation']
        verbose_name = "Éligibilité certification"
        verbose_name_plural = "Éligibilités certifications"

    def __str__(self):
        return f"{self.utilisateur.username} → {self.formation.nom} (cohorte {self.cohorte.nom})"

    def est_eligible(self):
        """Vérifie si tous les prérequis sont remplis pour générer le certificat."""
        return self.frais_paye and self.valide_par is not None

    def valider(self, admin_user):
        """Valide l'éligibilité et génère le certificat si tout est OK."""
        if not self.est_eligible():
            raise ValueError("L'éligibilité n'est pas complète (frais non payés ou non validé).")
        if self.certificat_genere:
            return self.certificat_genere

        from content.models import Certificat
        certificat = Certificat.objects.create(
            utilisateur=self.utilisateur,
            formation=self.formation
        )
        self.certificat_genere = certificat
        self.save()
        return certificat

    # --- NOUVELLES MÉTHODES ---
    def calculer_moyenne(self):
        """Calcule la moyenne des notes si disponibles."""
        notes = []
        if self.note_theorique is not None:
            notes.append(float(self.note_theorique))
        if self.note_projet is not None:
            notes.append(float(self.note_projet))
        if notes:
            return round(sum(notes) / len(notes), 2)
        return None

    def verifier_et_mettre_a_jour_statut(self):
        """Met à jour le statut en fonction des notes et du paiement."""
        if self.certificat_genere:
            self.statut = 'certifie'
        elif self.frais_paye and self.note_theorique is not None and self.note_projet is not None:
            self.statut = 'eligible'
        else:
            self.statut = 'en_cours'
        self.save(update_fields=['statut'])



# ================================================
# MODELS.PY — Fonction utilitaire : cet étudiant est-il en cohorte 
# pilote pour cette formation ? (détermine QUEL système s'applique)
# ================================================

def obtenir_cohorte_active_pour(utilisateur, formation):
    """
    Retourne la Cohorte active si l'utilisateur en est membre pour 
    cette formation précise, sinon None (= processus classique s'applique).
    """
    return Cohorte.objects.filter(
        membres=utilisateur, formations=formation, actif=True
    ).first()