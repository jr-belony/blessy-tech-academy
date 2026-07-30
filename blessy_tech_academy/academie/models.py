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
    logo = models.ImageField(upload_to="academies/logos/", null=True, blank=True)
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
    actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'academie'
        db_table = 'academie_partenaireapi'
        verbose_name = "Partenaire API"
        verbose_name_plural = "Partenaires API"

    def __str__(self):
        return self.nom


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
    ]

    ecole = models.ForeignKey(Ecole, on_delete=models.CASCADE, related_name='formations', null=True, blank=True)
    nom = models.CharField(max_length=200)
    slug = models.SlugField(max_length=250, unique=True, null=True, blank=True, db_index=True)
    icone = models.CharField(max_length=10, default='📚')
    illustration = models.CharField(max_length=10, blank=True, default='', help_text="Émoji d'illustration (💻 🤖 🔐 📈 ...)")
    description = models.TextField(blank=True)
    duree_mois = models.IntegerField(default=1)
    prix = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    niveau = models.CharField(max_length=20, choices=NIVEAUX, default='debutant')
    debouches = models.TextField(blank=True)
    prerequis = models.TextField(blank=True)
    certifications = models.TextField(blank=True)
    actif = models.BooleanField(default=True)
    gratuit = models.BooleanField(default=False)
    formation_upgrade = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    salaire_haiti = models.CharField(max_length=50, blank=True)
    salaire_international = models.CharField(max_length=50, blank=True)
    competences_acquises = models.TextField(blank=True)

    class Meta:
        app_label = 'academie'
        db_table = 'academie_formation'
        verbose_name = 'Formation'
        verbose_name_plural = 'Formations'
        indexes = [
            models.Index(fields=['actif', 'niveau']),
            models.Index(fields=['ecole']),
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
    resume = models.TextField(blank=True)
    contenu = models.TextField(blank=True)
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
    icone = models.CharField(max_length=10, default='🚀')
    description = models.TextField(blank=True)
    duree_mois = models.IntegerField(default=12)
    prix = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    formations = models.ManyToManyField(Formation, blank=True, related_name='parcours_list')
    actif = models.BooleanField(default=True)
    ordre = models.IntegerField(default=0)

    class Meta:
        app_label = 'academie'
        db_table = 'academie_parcours'
        ordering = ['ordre']
        verbose_name = 'Parcours'
        verbose_name_plural = 'Parcours'

    def __str__(self):
        return self.titre


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