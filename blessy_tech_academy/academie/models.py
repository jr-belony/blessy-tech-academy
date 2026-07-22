import uuid
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django_ckeditor_5.fields import CKEditor5Field
from simple_history.models import HistoricalRecords
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from users.models import ProfilUtilisateur, LogAudit, Enseignant, HistoriqueConversationIA, PushSubscription, NotificationPushEnvoyee

class Ecole(models.Model):
    """Représente une École (catégorie de formations)."""

    nom = models.CharField(max_length=200)
    icone = models.CharField(max_length=10, default="🏫")
    # === Lien racine Academie (multi-tenant) ===
    academie = models.ForeignKey(
        "Academie",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="ecoles",
        help_text="Académie mère de cette école",
    )
    description = models.TextField()
    ordre = models.IntegerField(default=0)

    class Meta:
        ordering = ["ordre", "nom"]
        verbose_name = "École"
        verbose_name_plural = "Écoles"

    def __str__(self):
        return f"{self.icone} {self.nom}"

    def natural_key(self):  # ← Ajoute cette méthode
        return (self.nom,)

    history = HistoricalRecords()  # ← AJOUTE À LA FIN, avant Meta/méthodes

    def progression_pour(self, utilisateur):
        """Calcule le % de progression d'un utilisateur sur cette formation."""
        if not utilisateur.is_authenticated:
            return 0

        toutes_lecons = Lecon.objects.filter(module__formation=self)
        total = toutes_lecons.count()

        if total == 0:
            return 0

        terminees = ProgressionLecon.objects.filter(
            utilisateur=utilisateur, lecon__in=toutes_lecons, terminee=True
        ).count()

        return round((terminees / total) * 100)


# ================================================
# MODELS.PY — Classe Formation
# Représente une formation avec slug SEO auto-généré,
# progression utilisateur et workflow éditorial.
# ================================================
class Formation(models.Model):
    """
    Représente une formation proposée par Blessy Tech Academy.
    """

    # 1. CONSTANTES
    NIVEAUX = [
        ("debutant", "Débutant"),
        ("intermediaire", "Intermédiaire"),
        ("avance", "Avancé"),
        ("professionnel", "Professionnel"),
    ]

    # 2. INFORMATIONS GÉNÉRALES
    ecole = models.ForeignKey(
        Ecole, on_delete=models.SET_NULL, null=True, blank=True, related_name="formations"
    )
    nom = models.CharField(max_length=200)
    slug = models.SlugField(max_length=250, unique=True, null=True, blank=True, db_index=True)
    icone = models.CharField(max_length=10, default="📚")
    illustration = models.CharField(
        max_length=10, blank=True, default="", help_text="Émoji d'illustration (💻 🤖 🔐 📈 ...)"
    )
    description = models.TextField()
    niveau = models.CharField(max_length=20, choices=NIVEAUX, default="debutant")
    duree_mois = models.IntegerField()
    prix = models.IntegerField()
    actif = models.BooleanField(default=True)
    gratuit = models.BooleanField(default=False, help_text="Formation gratuite (Lead Magnet)")

    # 3. PROGRAMME & CONTENU
    prerequis = models.TextField(blank=True)
    debouches = models.TextField(blank=True)
    certifications = models.TextField(blank=True)
    # 4. EMPLOYABILITÉ & CARRIÈRE
    metiers = models.TextField(blank=True, help_text="Un métier par ligne")
    competences_acquises = models.TextField(blank=True, help_text="Une compétence par ligne")
    competences_cles = models.TextField(blank=True, help_text="Compétences clés (une par ligne)")
    logiciels_maitrises = models.TextField(
        blank=True, help_text="Logiciels ou outils maîtrisés (un par ligne)"
    )

    outils_utilises = models.TextField(
        blank=True, help_text="Technologies utilisées durant la formation"
    )
    projets_realises = models.TextField(blank=True, help_text="Un projet réalisé par ligne")
    certification_obtenue = models.CharField(
        max_length=255, blank=True, help_text="Nom du certificat délivré"
    )
    niveau_sortie = models.CharField(
        max_length=120, blank=True, help_text="Ex : Développeur Backend Junior"
    )
    temps_pour_emploi = models.CharField(max_length=120, blank=True, help_text="Ex : 3 à 6 mois")
    taux_employabilite = models.PositiveIntegerField(default=0, help_text="Pourcentage estimé")
    salaire_haiti = models.CharField(
        max_length=60, blank=True, help_text="Ex : 40 000 à 120 000 HTG/mois"
    )
    salaire_international = models.CharField(
        max_length=60, blank=True, help_text="Ex : 2 000 à 6 000 USD/mois"
    )
    # 5. MARKETING & PARTAGE
    message_partage = models.CharField(
        max_length=500,
        blank=True,
        default="",
        help_text="Message utilisé lors du partage automatique.",
    )
    # 6. UPSELL / CROSS-SELL
    formation_upgrade = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="formations_gratuites",
        help_text="Formation premium recommandée après cette formation gratuite",
    )
    # 7. MÉTADONNÉES
    date_creation = models.DateTimeField(auto_now_add=True)

    # 8. CONFIGURATION DJANGO
    class Meta:
        ordering = ["nom"]
        verbose_name = "Formation"
        verbose_name_plural = "Formations"

        indexes = [
            models.Index(fields=["actif"]),
            models.Index(fields=["niveau"]),
            models.Index(fields=["ecole", "actif"]),
        ]
    # 9. MÉTHODES
    def __str__(self):
        return f"{self.icone} {self.nom} ({self.duree_mois} mois)"

    def natural_key(self):
        return (self.nom, self.ecole.nom if self.ecole else None)

    def progression_pour(self, utilisateur):
        """Calcule le % de progression d'un utilisateur sur cette formation."""
        if not utilisateur.is_authenticated:
            return 0

        toutes_lecons = Lecon.objects.filter(module__formation=self)
        total = toutes_lecons.count()
        if total == 0:
            return 0

        terminees = ProgressionLecon.objects.filter(
            utilisateur=utilisateur, lecon__in=toutes_lecons, terminee=True
        ).count()

        return round((terminees / total) * 100)

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            base_slug = slugify(self.nom)
            slug_candidat = base_slug
            compteur = 1
            while Formation.objects.filter(slug=slug_candidat).exclude(pk=self.pk).exists():
                slug_candidat = f"{base_slug}-{compteur}"
                compteur += 1
            self.slug = slug_candidat
        super().save(*args, **kwargs)

    history = HistoricalRecords()


class Inscription(models.Model):
    """Représente une demande d'inscription."""

    SUJETS = [
        ("inscription", "S'inscrire à une formation"),
        ("information", "Demande d'information"),
        ("partenariat", "Partenariat"),
        ("autre", "Autre"),
    ]

    prenom = models.CharField(max_length=100)
    nom = models.CharField(max_length=100)
    email = models.EmailField()
    telephone = models.CharField(max_length=20, blank=True)
    formation = models.ForeignKey(
        Formation, on_delete=models.SET_NULL, null=True, blank=True, related_name="inscriptions"
    )
    sujet = models.CharField(max_length=20, choices=SUJETS, default="information")
    message = models.TextField()
    date_inscription = models.DateTimeField(auto_now_add=True)
    traite = models.BooleanField(default=False)
    # === Extension CRM ===
    STATUTS_LEAD = [
        ("nouveau", "🆕 Nouveau"),
        ("contacte", "📞 Contacté"),
        ("interesse", "💬 Intéressé"),
        ("converti", "✅ Converti"),
        ("perdu", "❌ Perdu"),
    ]
    statut_lead = models.CharField(max_length=15, choices=STATUTS_LEAD, default="nouveau")
    assigne_a = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="leads_assignes",
        help_text="Membre de l'équipe responsable de ce lead",
    )
    source_lead = models.CharField(
        max_length=50,
        blank=True,
        choices=[
            ("site", "Site web"),
            ("forum", "Forum"),
            ("reseaux", "Réseaux sociaux"),
            ("bouche_oreille", "Bouche-à-oreille"),
            ("autre", "Autre"),
        ],
        default="site",
    )
    notes_internes = models.TextField(
        blank=True, help_text="Notes visibles uniquement par l'équipe"
    )

    class Meta:
        ordering = ["-date_inscription"]
        verbose_name = "Inscription"
        verbose_name_plural = "Inscriptions"

    def __str__(self):
        return f"{self.prenom} {self.nom} — {self.get_sujet_display()}"


# ================================================
# MODELS.PY — Classe Quiz
# Représente un quiz lié à une formation ou à un module spécifique.
# ================================================
class Quiz(models.Model):
    """Représente un quiz lié à une formation."""

    formation = models.ForeignKey(Formation, on_delete=models.CASCADE, related_name="quiz_set")
    module = models.ForeignKey(
        'Module',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='quiz_module',
        help_text="Quiz spécifique à ce module. Si vide, le quiz reste rattaché à la formation entière."
    )
    titre = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    actif = models.BooleanField(default=True)
    limite_temps_minutes = models.IntegerField(default=0, help_text="0 = pas de limite")
    tentatives_max = models.IntegerField(default=0, help_text="0 = illimité")
    melanger_questions = models.BooleanField(default=True)
    melanger_reponses = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date_creation"]
        verbose_name = "Quiz"
        verbose_name_plural = "Quiz"

    def __str__(self):
        return f"{self.titre} ({self.formation.nom})"

    def nombre_questions(self):
        return self.questions.count()

    def contexte(self):
        """Retourne 'Module X' si rattaché à un module, sinon le nom de la formation."""
        if self.module:
            return f"{self.module.formation.nom} — Module: {self.module.titre}"
        return self.formation.nom if self.formation else "—"

class Question(models.Model):
    """Représente une question à choix multiples dans un quiz."""

    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions")
    texte = models.TextField()
    choix_a = models.CharField(max_length=300)
    choix_b = models.CharField(max_length=300)
    choix_c = models.CharField(max_length=300)
    choix_d = models.CharField(max_length=300)
    bonne_reponse = models.CharField(
        max_length=1, choices=[("a", "A"), ("b", "B"), ("c", "C"), ("d", "D")]
    )
    explication = models.TextField(blank=True)
    ordre = models.IntegerField(default=0)

    class Meta:
        ordering = ["ordre"]
        verbose_name = "Question"
        verbose_name_plural = "Questions"

    def __str__(self):
        return f"Q{self.ordre}: {self.texte[:50]}"


class ResultatQuiz(models.Model):
    """Enregistre le résultat d'un étudiant à un quiz."""

    utilisateur = models.ForeignKey(
        "auth.User", on_delete=models.CASCADE, related_name="resultats_quiz"
    )
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="resultats")
    score = models.IntegerField()  # nombre de bonnes réponses
    total_questions = models.IntegerField()
    date_passage = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date_passage"]
        verbose_name = "Résultat de quiz"
        verbose_name_plural = "Résultats de quiz"

    def __str__(self):
        return (
            f"{self.utilisateur.username} - {self.quiz.titre} - {self.score}/{self.total_questions}"
        )

    def pourcentage(self):
        if self.total_questions == 0:
            return 0
        return round((self.score / self.total_questions) * 100)


# ================================================
# MODÈLE — Module (regroupement de leçons)
# ================================================
class Module(models.Model):
    """Un module = un chapitre/section d'une formation."""

    formation = models.ForeignKey(Formation, on_delete=models.CASCADE, related_name="modules")
    titre = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    ordre = models.IntegerField(default=0)

    class Meta:
        ordering = ["ordre"]
        verbose_name = "Module"
        verbose_name_plural = "Modules"

    def __str__(self):
        return f"{self.formation.nom} — Module {self.ordre}: {self.titre}"

    def nombre_lecons(self):
        return self.lecons.count()


# ================================================
# MODÈLE — Leçon (contenu pédagogique)
# ================================================
class Lecon(models.Model):
    """Une leçon = un contenu pédagogique précis dans un module."""

    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name="lecons")
    titre = models.CharField(max_length=200)
    resume = models.CharField(
        max_length=300, blank=True, help_text="Court résumé visible publiquement (sans connexion)"
    )
    contenu = CKEditor5Field(
        blank=True,
        config_name="default",
        help_text="Contenu complet du cours — visible uniquement aux étudiants connectés",
    )
    duree_minutes = models.IntegerField(default=15)
    ordre = models.IntegerField(default=0)
    history = HistoricalRecords()  # ← AJOUTE À LA FIN

    class Meta:
        ordering = ["ordre"]
        verbose_name = "Leçon"
        verbose_name_plural = "Leçons"

    def __str__(self):
        return f"{self.module.titre} — {self.titre}"
        history = HistoricalRecords()  # ← AJOUTE À LA FIN


# ================================================
# MODÈLE — ProgressionLecon (suivi apprentissage)
# ================================================
class ProgressionLecon(models.Model):
    """Suit la progression d'un étudiant sur une leçon."""

    utilisateur = models.ForeignKey(
        "auth.User", on_delete=models.CASCADE, related_name="progressions"
    )
    lecon = models.ForeignKey(Lecon, on_delete=models.CASCADE, related_name="progressions")
    terminee = models.BooleanField(default=False)
    date_completion = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ["utilisateur", "lecon"]
        verbose_name = "Progression de leçon"
        verbose_name_plural = "Progressions de leçons"
        indexes = [
            models.Index(fields=["utilisateur", "terminee"]),
            models.Index(fields=["lecon", "terminee"]),
        ]

    def __str__(self):
        statut = "✅" if self.terminee else "⏳"
        return f"{statut} {self.utilisateur.username} — {self.lecon.titre}"


# ================================================
# MODÈLE — Parcours (programme multi-formations)
# ================================================
class Parcours(models.Model):
    """Un parcours professionnel = combinaison de plusieurs formations."""

    titre = models.CharField(max_length=200)
    icone = models.CharField(max_length=10, default="🎓")
    description = models.TextField(blank=True)
    duree_mois = models.IntegerField()
    prix = models.IntegerField()
    formations = models.ManyToManyField(Formation, related_name="parcours", blank=True)
    actif = models.BooleanField(default=True)
    ordre = models.IntegerField(default=0)

    class Meta:
        ordering = ["ordre", "titre"]
        verbose_name = "Parcours professionnel"
        verbose_name_plural = "Parcours professionnels"

    def __str__(self):
        return f"{self.icone} {self.titre} ({self.duree_mois} mois)"

    def nombre_formations(self):
        return self.formations.count()


# ================================================
# MODÈLE — Sujet (forum communautaire)
# ================================================
class Sujet(models.Model):
    """Un sujet de discussion dans le forum."""

    CATEGORIES = [
        ("general", "Général"),
        ("question", "Question"),
        ("partage", "Partage de projet"),
        ("aide", "Demande d'aide"),
        ("annonce", "Annonce"),
    ]

    titre = models.CharField(max_length=300)
    contenu = CKEditor5Field(config_name="default")
    auteur = models.ForeignKey("auth.User", on_delete=models.CASCADE, related_name="sujets_forum")
    formation = models.ForeignKey(
        Formation, on_delete=models.SET_NULL, null=True, blank=True, related_name="sujets_forum"
    )
    categorie = models.CharField(max_length=20, choices=CATEGORIES, default="general")
    vues = models.IntegerField(default=0)
    epingle = models.BooleanField(default=False)
    resolu = models.BooleanField(default=False)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-epingle", "-date_creation"]
        verbose_name = "Sujet"
        verbose_name_plural = "Sujets"
        indexes = [
            models.Index(fields=["categorie", "date_creation"]),
            models.Index(fields=["formation"]),
        ]

    def __str__(self):
        return self.titre

    def nombre_reponses(self):
        return self.reponses.count()

    def nombre_likes(self):
        return self.reactions.count()


# ================================================
# MODÈLE — Réponse (forum)
# ================================================
class Reponse(models.Model):
    """Une réponse à un sujet du forum."""

    sujet = models.ForeignKey(Sujet, on_delete=models.CASCADE, related_name="reponses")
    contenu = models.TextField()
    auteur = models.ForeignKey("auth.User", on_delete=models.CASCADE, related_name="reponses_forum")
    acceptee = models.BooleanField(default=False)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["date_creation"]
        verbose_name = "Réponse"
        verbose_name_plural = "Réponses"

    def __str__(self):
        return f"Réponse de {self.auteur.username} sur {self.sujet.titre[:30]}"

    def nombre_likes(self):
        return self.reactions.count()


# ================================================
# MODÈLE — Réaction (like/émotion forum)
# ================================================
class Reaction(models.Model):
    """Un like sur un sujet ou une réponse."""

    utilisateur = models.ForeignKey(
        "auth.User", on_delete=models.CASCADE, related_name="reactions_forum"
    )
    sujet = models.ForeignKey(
        Sujet, on_delete=models.CASCADE, null=True, blank=True, related_name="reactions"
    )
    reponse = models.ForeignKey(
        Reponse, on_delete=models.CASCADE, null=True, blank=True, related_name="reactions"
    )
    date_creation = models.DateTimeField(auto_now_add=True)
# Nouveau système polymorphe (V2)
# Les anciens champs sujet/reponse restent temporairement
# pour assurer la compatibilité.
# ==========================================================

    content_type = models.ForeignKey(
    ContentType,
    on_delete=models.CASCADE,
    null=True,
    blank=True,
    related_name="reactions",
    )
    object_id = models.PositiveBigIntegerField(
    null=True,
    blank=True,
    )
    cible = GenericForeignKey(
    "content_type",
    "object_id",
    )
    class Meta:
        unique_together = [
            ["utilisateur", "sujet"],
            ["utilisateur", "reponse"],
        ]
        verbose_name = "Réaction"
        verbose_name_plural = "Réactions"

    def __str__(self):
        cible = self.sujet or self.reponse
        return f"❤️ {self.utilisateur.username} → {cible}"


# ================================================
# MODÈLE — BadgeForum (gamification)
# ================================================
class BadgeForum(models.Model):
    """Badge attribué à un membre du forum."""

    TYPES_BADGES = [
        # Badges Forum (existants)
        ("premier_post", "✍️ Premier Post"),
        ("premiere_reponse", "💬 Première Réponse"),
        ("solution_acceptee", "✅ Solution Acceptée"),
        ("dix_reponses", "🔥 10 Réponses"),
        ("cinquante_reponses", "⭐ 50 Réponses"),
        ("cent_likes", "❤️ 100 Likes reçus"),
        ("sujet_populaire", "🏆 Sujet Populaire"),
        # Badges Apprentissage (existants)
        ("premier_quiz", "🏅 Premier Quiz Réussi"),
        ("cinq_quiz", "📝 5 Quiz Réussis"),
        ("dix_heures", "⏰ 10 Heures d'Apprentissage"),
        ("cinquante_heures", "🎯 50 Heures d'Apprentissage"),
        ("premiere_formation", "🎓 Première Formation Complétée"),
        ("trois_formations", "🏆 3 Formations Complétées"),
        # Badges Apprentissage (nouveaux)
        ("premier_cours_termine", "🏅 Premier cours terminé"),
        ("cinq_lecons", "📚 5 leçons terminées"),
        ("dix_lecons", "📘 10 leçons terminées"),
        # Badges Compétences (existants)
        ("expert_python", "🐍 Expert Python"),
        ("expert_web", "🌐 Expert Web"),
        ("expert_data", "📊 Expert Données"),
        ("expert_cyber", "🔒 Expert Cybersécurité"),
        ("expert_design", "🎨 Expert Design"),
        # Badges Compétences (nouveaux)
        ("expert_excel", "📊 Expert Excel"),
        ("expert_ia", "🤖 Expert IA"),
        # Badges Projet (existants)
        ("projet_termine", "🚀 Projet Terminé"),
        ("trois_projets", "💼 3 Projets Livrés"),
        # Badges Social (existants)
        ("profile_complet", "👤 Profil Complété"),
        ("premier_certificat", "📜 Premier Certificat"),
        ("membre_actif", "🌟 Membre Actif"),
        ("membre_actif_forum", "💬 Membre actif du forum"),
    ]
    utilisateur = models.ForeignKey(
        "auth.User", on_delete=models.CASCADE, related_name="badges_forum"
    )
    type_badge = models.CharField(max_length=30, choices=TYPES_BADGES)
    date_obtention = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["utilisateur", "type_badge"]
        ordering = ["-date_obtention"]
        verbose_name = "Badge Forum"
        verbose_name_plural = "Badges Forum"

    def __str__(self):
        return f"{self.get_type_badge_display()} — {self.utilisateur.username}"


# ================================================
# MODÈLE — ProjetEtudiant (portfolio)
# ================================================
class ProjetEtudiant(models.Model):
    """Projet réalisé par un étudiant pour son portfolio."""

    auteur = models.ForeignKey("auth.User", on_delete=models.CASCADE, related_name="projets")
    titre = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to="projets/", blank=True, null=True)
    lien = models.URLField(blank=True, null=True)
    
    technologies = models.CharField(
        max_length=300, blank=True, help_text="Ex: Python, Django, React"
    )
    niveau_difficulte = models.CharField(
        max_length=20,
        choices=[
            ("debutant", "Débutant"),
            ("intermediaire", "Intermédiaire"),
            ("avance", "Avancé"),
        ],
        default="debutant",
        blank=True,
    )
    competences_developpees = models.CharField(max_length=300, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    # ================================================
    # MODELS.PY — Ajout traçabilité pédagogique
    # ================================================
    formation_liee = models.ForeignKey(
    Formation, on_delete=models.SET_NULL, null=True, blank=True,
    related_name='projets_etudiants',
    help_text="Formation dans le cadre de laquelle ce projet a été réalisé"
)
    class Meta:
        ordering = ["-date_creation"]
        verbose_name = "Projet étudiant"
        verbose_name_plural = "Projets étudiants"

    def __str__(self):
        return f"{self.titre} par {self.auteur.username}"


# ================================================
# MODÈLE — Certificat (certification)
# ================================================
class Certificat(models.Model):
    """Certificat émis à un étudiant après complétion d'une formation."""

    utilisateur = models.ForeignKey(
        "auth.User", on_delete=models.CASCADE, related_name="certificats"
    )
    formation = models.ForeignKey(Formation, on_delete=models.CASCADE, related_name="certificats")
    numero = models.CharField(max_length=20, unique=True)
    date_emission = models.DateTimeField(auto_now_add=True)
    verifie = models.BooleanField(default=False)  # pour usage futur

    class Meta:
        unique_together = ["utilisateur", "formation"]
        ordering = ["-date_emission"]
        verbose_name = "Certificat"
        verbose_name_plural = "Certificats"

    def __str__(self):
        return f"Certificat {self.numero} - {self.utilisateur.username} ({self.formation.nom})"


# ================================================
# MODÈLE — Article (Blog, Ressources, Knowledge Center)
# ================================================
class Article(models.Model):
    """Article ou guide publié dans la page Ressources."""

    CATEGORIES = [
        ("guide", "📖 Guide"),
        ("tutoriel", "🎓 Tutoriel"),
        ("actualite", "📰 Actualité"),
        ("conseil", "💡 Conseil"),
        ("outil", "🛠️ Outil"),
    ]

    titre = models.CharField(max_length=300)
    slug = models.SlugField(max_length=300, unique=True, blank=True)
    resume = models.TextField(max_length=500)
    contenu = CKEditor5Field(config_name="default", blank=True)
    categorie = models.CharField(max_length=20, choices=CATEGORIES, default="guide")
    formation_liee = models.ForeignKey(
        Formation, on_delete=models.SET_NULL, null=True, blank=True, related_name="articles"
    )
    # === Lien racine Academie (multi-tenant) ===
    academie = models.ForeignKey(
        "Academie",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="articles",
        help_text="Académie propriétaire de cet article",
    )
    auteur = models.ForeignKey(
        "auth.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="articles"
    )
    en_vedette = models.BooleanField(default=False)
    publie = models.BooleanField(default=False)
    temps_lecture = models.IntegerField(default=5, help_text="Temps de lecture estimé en minutes")
    date_publication = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    # Champs SEO
    meta_titre = models.CharField(
        max_length=70, blank=True, help_text="Titre SEO (60-70 caractères recommandés)"
    )
    meta_description = models.CharField(
        max_length=160, blank=True, help_text="Description SEO (150-160 caractères recommandés)"
    )
    mots_cles = models.CharField(
        max_length=255, blank=True, help_text="Mots-clés séparés par des virgules"
    )
    noindex = models.BooleanField(default=False, help_text="Empêcher l'indexation Google")

    # === Knowledge Center — nouveaux types de contenu ===
    TYPES_CONTENU = [
        ("article", "📝 Article"),
        ("guide", "📖 Guide"),
        ("tutoriel", "🎓 Tutoriel"),
        ("etude_cas", "📊 Étude de cas"),
        ("actualite", "📰 Actualité Tech"),
        ("livre_blanc", "📄 Livre blanc"),
        ("faq", "❓ FAQ"),
    ]
    type_contenu = models.CharField(max_length=20, choices=TYPES_CONTENU, default="article")
    fichier_telechargeable = models.FileField(upload_to="knowledge_center/", null=True, blank=True)
    articles_associes = models.ManyToManyField("self", blank=True, symmetrical=True)
    nb_vues = models.IntegerField(default=0)
    nb_partages = models.IntegerField(default=0)

    # Enregistrement historique
    history = HistoricalRecords()

    class Meta:
        ordering = ["-en_vedette", "-date_publication"]
        verbose_name = "Article"
        verbose_name_plural = "Articles"

    def __str__(self):
        return self.titre

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify

            self.slug = slugify(self.titre)
        super().save(*args, **kwargs)

    def temps_lecture_estime(self):
        """Calcule le temps de lecture basé sur le nombre de mots (200 mots/min)."""
        import re

        texte_brut = re.sub("<[^<]+?>", "", self.contenu or "")
        nb_mots = len(texte_brut.split())
        return max(1, round(nb_mots / 200))

    # ================================================
    # Score SEO (réutilisation des champs existants)
    # ================================================
    def score_seo(self):
        """Calcule un score SEO sur 100 basé sur les champs déjà existants."""
        score = 0
        if self.meta_titre and 50 <= len(self.meta_titre) <= 70:
            score += 20
        if self.meta_description and 120 <= len(self.meta_description) <= 160:
            score += 20
        if self.mots_cles:
            score += 15
        if self.resume and len(self.resume) > 50:
            score += 15
        if self.temps_lecture_estime() >= 3:
            score += 15
        if not self.noindex:
            score += 15
        return score

    def suggestions_seo(self):
        """Liste de suggestions d'amélioration SEO — actionnable directement."""
        suggestions = []
        if not self.meta_titre:
            suggestions.append("Ajoute un titre SEO (50-70 caractères)")
        elif not (50 <= len(self.meta_titre) <= 70):
            suggestions.append(f"Titre SEO actuel : {len(self.meta_titre)} caractères — vise 50-70")
        if not self.meta_description:
            suggestions.append("Ajoute une meta description (120-160 caractères)")
        if not self.mots_cles:
            suggestions.append("Renseigne des mots-clés principaux")
        if self.temps_lecture_estime() < 3:
            suggestions.append("Contenu court — articles de 3+ min se réfèrencent mieux")
        return suggestions


class OutilRecommande(models.Model):
    """Outil numérique recommandé aux étudiants."""

    CATEGORIES = [
        ("developpement", "💻 Développement"),
        ("design", "🎨 Design"),
        ("ia", "🤖 Intelligence Artificielle"),
        ("productivite", "⚡ Productivité"),
        ("collaboration", "👥 Collaboration"),
        ("securite", "🔐 Sécurité"),
    ]

    nom = models.CharField(max_length=200)
    description = models.TextField(max_length=400)
    url = models.URLField()
    icone = models.CharField(max_length=10, default="🛠️")
    categorie = models.CharField(max_length=20, choices=CATEGORIES, default="developpement")
    gratuit = models.BooleanField(default=True)
    recommande_par_bta = models.BooleanField(default=True)
    ordre = models.IntegerField(default=0)

    class Meta:
        ordering = ["ordre", "nom"]
        verbose_name = "Outil recommandé"
        verbose_name_plural = "Outils recommandés"

    def __str__(self):
        return f"{self.icone} {self.nom}"


class Temoignage(models.Model):
    """Témoignage d'un étudiant BTA."""

    prenom_nom = models.CharField(max_length=200)
    formation_suivie = models.ForeignKey(
        Formation, on_delete=models.SET_NULL, null=True, blank=True, related_name="temoignages"
    )
    texte = models.TextField()
    note = models.IntegerField(
        default=5, choices=[(i, f"{i} étoile{'s' if i > 1 else ''}") for i in range(1, 6)]
    )
    initiales = models.CharField(max_length=3, help_text="Ex: JRB pour Jean Raymond BELONY")
    titre_professionnel = models.CharField(
        max_length=200, blank=True, help_text="Ex: Développeur Web Freelance"
    )
    en_vedette = models.BooleanField(default=False)
    approuve = models.BooleanField(default=False)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-en_vedette", "-date_creation"]
        verbose_name = "Témoignage"
        verbose_name_plural = "Témoignages"

    def __str__(self):
        return f"{self.prenom_nom} — {self.note}⭐"


# ================================================
# MODÈLE : ConnexionUtilisateur
# Rôle : Enregistre chaque connexion d'un utilisateur
# Utilisé par : signals.py (signal user_logged_in)
#               dashboard.html (historique)
# ================================================
class ConnexionUtilisateur(models.Model):
    """Enregistre chaque connexion d'un utilisateur pour l'historique et la détection suspecte."""

    utilisateur = models.ForeignKey(
        "auth.User", on_delete=models.CASCADE, related_name="connexions"
    )
    adresse_ip = models.GenericIPAddressField()
    navigateur = models.CharField(max_length=300)
    pays = models.CharField(max_length=100, blank=True)
    ville = models.CharField(max_length=100, blank=True)
    suspecte = models.BooleanField(
        default=False
    )  # True si IP ou pays différent de la dernière connexion
    date_connexion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date_connexion"]
        verbose_name = "Connexion utilisateur"
        verbose_name_plural = "Connexions utilisateurs"

    def __str__(self):
        return f"{self.utilisateur.username} - {self.date_connexion}"


# ================================================
# MODELS.PY — Système de Paiement (Payment Center)
# ================================================


class MoyenPaiement(models.Model):
    """Moyens de paiement disponibles — administrable, extensible."""

    CODES = [
        ("manuel", "Paiement manuel (validation admin)"),
        ("moncash", "MonCash"),
        ("natcash", "NatCash"),
        ("stripe", "Carte bancaire (Stripe)"),
        ("paypal", "PayPal"),
        ("virement", "Virement bancaire"),
    ]

    code = models.CharField(max_length=20, choices=CODES, unique=True)
    nom_affiche = models.CharField(max_length=100)
    icone = models.CharField(max_length=10, default="💳")
    actif = models.BooleanField(default=True)
    instructions = models.TextField(
        blank=True, help_text="Instructions affichées à l'étudiant (ex: numéro MonCash à utiliser)"
    )
    ordre = models.IntegerField(default=0)

    class Meta:
        ordering = ["ordre"]
        verbose_name = "Moyen de paiement"
        verbose_name_plural = "Moyens de paiement"

    def __str__(self):
        return f"{self.icone} {self.nom_affiche}"


class Coupon(models.Model):
    """Code promo — fixe ou pourcentage, avec restrictions flexibles."""

    TYPES = [("fixe", "Montant fixe"), ("pourcentage", "Pourcentage")]

    code = models.CharField(max_length=30, unique=True)
    type_reduction = models.CharField(max_length=15, choices=TYPES, default="pourcentage")
    valeur = models.DecimalField(
        max_digits=10, decimal_places=2, help_text="Montant $ ou % selon le type"
    )

    # Restrictions optionnelles — vide = applicable à tout
    formation_specifique = models.ForeignKey(
        Formation, on_delete=models.SET_NULL, null=True, blank=True, related_name="coupons"
    )
    ecole_specifique = models.ForeignKey(
        Ecole, on_delete=models.SET_NULL, null=True, blank=True, related_name="coupons"
    )
    parcours_specifique = models.ForeignKey(
        Parcours, on_delete=models.SET_NULL, null=True, blank=True, related_name="coupons"
    )

    utilisations_max = models.IntegerField(default=0, help_text="0 = illimité")
    utilisations_actuelles = models.IntegerField(default=0)

    date_debut = models.DateTimeField(default=timezone.now)
    date_fin = models.DateTimeField(null=True, blank=True)
    actif = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Coupon"
        verbose_name_plural = "Coupons"

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

    def calculer_reduction(self, montant):
        from decimal import Decimal

        if self.type_reduction == "pourcentage":
            return round(montant * (Decimal(str(self.valeur)) / 100), 2)
        return min(self.valeur, montant)


class Promotion(models.Model):
    """Promotion globale automatique (ex: Black Friday) — s'applique sans code."""

    nom = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    pourcentage_reduction = models.IntegerField(help_text="Ex: 30 pour -30%")

    ecoles_concernees = models.ManyToManyField(Ecole, blank=True, related_name="promotions")
    formations_concernees = models.ManyToManyField(Formation, blank=True, related_name="promotions")

    date_debut = models.DateTimeField()
    date_fin = models.DateTimeField()
    actif = models.BooleanField(default=True)
    bandeau_texte = models.CharField(
        max_length=200, blank=True, help_text="Ex: 🔥 -30% jusqu'au 30 novembre"
    )

    class Meta:
        verbose_name = "Promotion"
        verbose_name_plural = "Promotions"

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
    """Commande — le panier devenu commande."""

    STATUTS = [
        ("en_attente", "⏳ En attente de paiement"),
        ("paye", "✅ Payée"),
        ("annule", "❌ Annulée"),
        ("rembourse", "↩️ Remboursée"),
    ]

    reference = models.CharField(max_length=20, unique=True, editable=False)
    utilisateur = models.ForeignKey("auth.User", on_delete=models.CASCADE, related_name="commandes")

    sous_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    reduction_totale = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    devise = models.CharField(max_length=3, choices=[("USD", "USD"), ("HTG", "HTG")], default="USD")

    coupon_applique = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)
    moyen_paiement = models.ForeignKey(
        MoyenPaiement, on_delete=models.SET_NULL, null=True, blank=True
    )
    # === Ajout champ affiliation ===
    affilie_origine = models.ForeignKey(
        "Affilie",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="commandes_generees",
    )
    statut = models.CharField(max_length=15, choices=STATUTS, default="en_attente")
    date_creation = models.DateTimeField(auto_now_add=True)
    date_paiement = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-date_creation"]
        verbose_name = "Commande"
        verbose_name_plural = "Commandes"
        indexes = [
            models.Index(fields=["statut", "date_creation"]),
            models.Index(fields=["utilisateur", "statut"]),
        ]

    def __str__(self):
        return f"Commande #{self.reference} — {self.utilisateur.username}"

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = f"BTA-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def recalculer_total(self):
        """Recalcule les totaux depuis les OrderItem — source de vérité unique."""
        items = self.items.all()
        self.sous_total = sum(item.prix_unitaire for item in items)
        if self.coupon_applique:
            self.reduction_totale = self.coupon_applique.calculer_reduction(self.sous_total)
        self.total = max(0, self.sous_total - self.reduction_totale)
        self.save(update_fields=["sous_total", "reduction_totale", "total"])


class OrderItem(models.Model):
    """
    Ligne de commande — SNAPSHOT IMMUABLE.
    C'est ICI que la magie anti-cassure opère : toutes les infos
    produit sont copiées au moment de l'achat, indépendamment de
    ce qui arrive ensuite à la Formation/Parcours d'origine.
    """

    TYPES_PRODUIT = [("formation", "Formation"), ("parcours", "Parcours Professionnel")]

    commande = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")

    # Liens "vivants" — SET_NULL si le produit est supprimé (ne casse jamais la commande)
    formation = models.ForeignKey(Formation, on_delete=models.SET_NULL, null=True, blank=True)
    parcours = models.ForeignKey(Parcours, on_delete=models.SET_NULL, null=True, blank=True)

    type_produit = models.CharField(max_length=15, choices=TYPES_PRODUIT)

    # === SNAPSHOT — copié au moment de l'achat, JAMAIS modifié après ===
    nom_produit_snapshot = models.CharField(max_length=200)
    icone_produit_snapshot = models.CharField(max_length=10, default="📚")
    ecole_nom_snapshot = models.CharField(max_length=200, blank=True)
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = "Article de commande"
        verbose_name_plural = "Articles de commande"

    def __str__(self):
        return f"{self.nom_produit_snapshot} — {self.prix_unitaire}$"

    def obtenir_lien_produit(self):
        """Retourne le lien si le produit existe encore, sinon None."""
        if self.formation:
            return f"/formation/{self.formation.id}/"
        return None


class Invoice(models.Model):
    """Facture officielle — générée automatiquement après paiement validé."""

    commande = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="facture")
    numero_facture = models.CharField(max_length=30, unique=True, editable=False)
    date_emission = models.DateTimeField(auto_now_add=True)
    fichier_pdf = models.FileField(upload_to="factures/", null=True, blank=True)

    class Meta:
        verbose_name = "Facture"
        verbose_name_plural = "Factures"

    def save(self, *args, **kwargs):
        if not self.numero_facture:
            annee = timezone.now().year
            self.numero_facture = f"FACT-{annee}-{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.numero_facture


class Transaction(models.Model):
    """Trace chaque tentative/confirmation de paiement — journalisation complète."""

    STATUTS = [
        ("initiee", "Initiée"),
        ("reussie", "Réussie"),
        ("echouee", "Échouée"),
        ("en_verification", "En vérification manuelle"),
    ]

    commande = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="transactions")
    moyen_paiement = models.ForeignKey(MoyenPaiement, on_delete=models.SET_NULL, null=True)
    reference_externe = models.CharField(
        max_length=100, blank=True, help_text="ID transaction MonCash/Stripe/etc."
    )
    preuve_paiement = models.ImageField(upload_to="preuves_paiement/", null=True, blank=True)
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    statut = models.CharField(max_length=20, choices=STATUTS, default="initiee")
    notes_admin = models.TextField(blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    valide_par = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transactions_validees",
    )

    class Meta:
        ordering = ["-date_creation"]
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"
        indexes = [
            models.Index(fields=["statut"]),
            models.Index(fields=["commande", "statut"]),
        ]

    def __str__(self):
        return f"Transaction {self.commande.reference} — {self.get_statut_display()}"


class Refund(models.Model):
    """Remboursement — traçabilité complète, ne supprime jamais la commande d'origine."""

    commande = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="remboursements")
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    raison = models.TextField()
    approuve_par = models.ForeignKey("auth.User", on_delete=models.SET_NULL, null=True)
    date_demande = models.DateTimeField(auto_now_add=True)
    date_traitement = models.DateTimeField(null=True, blank=True)
    statut = models.CharField(
        max_length=15,
        choices=[("demande", "Demandé"), ("approuve", "Approuvé"), ("rejete", "Rejeté")],
        default="demande",
    )

    class Meta:
        verbose_name = "Remboursement"
        verbose_name_plural = "Remboursements"

    def __str__(self):
        return f"Remboursement {self.commande.reference} — {self.montant}$"


class AccesFormationDebloque(models.Model):
    """
    Table de vérité pour l'accès étudiant — INDÉPENDANTE de Formation.
    Garantit que même si Formation est supprimée, on sait toujours
    QUI a payé pour QUOI (utile pour reporting/support/historique).
    """

    utilisateur = models.ForeignKey(
        "auth.User", on_delete=models.CASCADE, related_name="acces_debloques"
    )
    formation = models.ForeignKey(Formation, on_delete=models.SET_NULL, null=True, blank=True)
    nom_formation_snapshot = models.CharField(max_length=200)
    commande_origine = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True)
    date_deblocage = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["utilisateur", "nom_formation_snapshot"]
        verbose_name = "Accès formation débloqué"
        verbose_name_plural = "Accès formations débloqués"
        indexes = [
            models.Index(fields=["utilisateur"]),
            models.Index(fields=["formation"]),
        ]

    def __str__(self):
        return f"{self.utilisateur.username} → {self.nom_formation_snapshot}"


# ================================================
# MODELS.PY — Abonnements Premium récurrents
# ================================================
class PlanAbonnement(models.Model):
    """Plan d'abonnement Premium — administrable."""

    PERIODICITES = [("mensuel", "Mensuel"), ("annuel", "Annuel")]

    nom = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    prix = models.DecimalField(max_digits=10, decimal_places=2)
    periodicite = models.CharField(max_length=10, choices=PERIODICITES, default="mensuel")
    avantages = models.TextField(help_text="Un avantage par ligne")
    actif = models.BooleanField(default=True)

    stripe_price_id = models.CharField(
        max_length=100, blank=True, help_text="ID prix Stripe (price_xxx)"
    )

    class Meta:
        verbose_name = "Plan d'abonnement"
        verbose_name_plural = "Plans d'abonnement"

    def __str__(self):
        return f"{self.nom} — {self.prix}$/{self.get_periodicite_display()}"


class Subscription(models.Model):
    """Abonnement actif d'un utilisateur."""

    STATUTS = [
        ("actif", "Actif"),
        ("annule", "Annulé"),
        ("expire", "Expiré"),
        ("en_echec", "Paiement échoué"),
    ]

    utilisateur = models.ForeignKey(
        "auth.User", on_delete=models.CASCADE, related_name="abonnements"
    )
    plan = models.ForeignKey(PlanAbonnement, on_delete=models.SET_NULL, null=True)
    plan_nom_snapshot = models.CharField(max_length=100)
    prix_snapshot = models.DecimalField(max_digits=10, decimal_places=2)

    stripe_subscription_id = models.CharField(max_length=100, blank=True)
    stripe_customer_id = models.CharField(max_length=100, blank=True)

    statut = models.CharField(max_length=15, choices=STATUTS, default="actif")
    date_debut = models.DateTimeField(auto_now_add=True)
    date_prochain_renouvellement = models.DateTimeField()
    date_annulation = models.DateTimeField(null=True, blank=True)
    renouvellement_auto = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Abonnement"
        verbose_name_plural = "Abonnements"

    def __str__(self):
        return (
            f"{self.utilisateur.username} — {self.plan_nom_snapshot} ({self.get_statut_display()})"
        )

    def est_actif(self):
        return self.statut == "actif" and self.date_prochain_renouvellement > timezone.now()


# ================================================
# MODÈLES — Plateforme d'examens officiels
# ================================================


class Examen(models.Model):
    """Examen officiel avec sécurité anti-triche."""

    formation = models.ForeignKey(Formation, on_delete=models.CASCADE, related_name="examens")
    titre = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    duree_minutes = models.IntegerField(default=60)
    seuil_reussite = models.IntegerField(default=70, help_text="Pourcentage minimum pour réussir")
    tentatives_max = models.IntegerField(default=3)
    actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    # === Nouveaux champs — Modernisation Exam Center ===
    competences_evaluees = models.TextField(
        blank=True, help_text="Compétences évaluées (une par ligne)"
    )
    prerequis_examen = models.TextField(blank=True, help_text="Prérequis pour passer l'examen")
    conditions_utilisation = models.TextField(
        blank=True, help_text="Conditions à accepter avant l'examen"
    )
    date_disponibilite = models.DateTimeField(null=True, blank=True, help_text="Date d'ouverture")
    date_expiration = models.DateTimeField(null=True, blank=True, help_text="Date de fermeture")
    xp_recompense = models.IntegerField(default=100, help_text="XP gagnés si réussite")
    certificat_auto = models.BooleanField(default=True, help_text="Générer certificat si réussite")

    class Meta:
        verbose_name = "Examen"
        verbose_name_plural = "Examens"

    def __str__(self):
        return f"📝 {self.titre}"

    def academie(self):
        """Raccourci pour accéder à l'académie d'un examen sans naviguer manuellement les FK."""
        if self.formation and self.formation.ecole:
            return self.formation.ecole.academie
        return None


class QuestionExamen(models.Model):
    """Question d'examen avec ordre aléatoire."""

    examen = models.ForeignKey(Examen, on_delete=models.CASCADE, related_name="questions")
    texte = models.TextField()
    type_question = models.CharField(
        max_length=20,
        choices=[
            ("qcm", "QCM"),
            ("vrai_faux", "Vrai/Faux"),
            ("texte", "Réponse texte"),
        ],
        default="qcm",
    )
    ordre = models.IntegerField(default=0)
    points = models.IntegerField(default=1)

    class Meta:
        verbose_name = "Question d'examen"
        verbose_name_plural = "Questions d'examen"
        ordering = ["ordre"]

    def __str__(self):
        return f"❓ {self.texte[:60]}"


class ChoixExamen(models.Model):
    """Choix de réponse pour QCM."""

    question = models.ForeignKey(QuestionExamen, on_delete=models.CASCADE, related_name="choix")
    texte = models.CharField(max_length=300)
    est_correct = models.BooleanField(default=False)
    ordre = models.IntegerField(default=0)

    class Meta:
        verbose_name = "Choix"
        verbose_name_plural = "Choix"
        ordering = ["ordre"]

    def __str__(self):
        return f"{'✅' if self.est_correct else '⬜'} {self.texte[:50]}"


class TentativeExamen(models.Model):
    """Tentative d'un étudiant avec suivi anti-triche."""

    utilisateur = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="tentatives_examens"
    )
    examen = models.ForeignKey(Examen, on_delete=models.CASCADE, related_name="tentatives")
    date_debut = models.DateTimeField(auto_now_add=True)
    date_fin = models.DateTimeField(null=True, blank=True)
    score = models.FloatField(null=True, blank=True)
    reussi = models.BooleanField(null=True, blank=True)
    evenements_suspects = models.JSONField(default=list)
    temps_utilise_secondes = models.IntegerField(
        null=True, blank=True, help_text="Temps total utilisé"
    )
    questions_repondues = models.IntegerField(default=0)
    bonnes_reponses = models.IntegerField(default=0)
    mauvaises_reponses = models.IntegerField(default=0)

    class Meta:
        verbose_name = "Tentative d'examen"
        verbose_name_plural = "Tentatives d'examens"

    def __str__(self):
        return f"{self.utilisateur} - {self.examen.titre}"

    def academie(self):
        """Permet de filtrer/grouper les tentatives d'examen par académie sans dupliquer la donnée."""
        return self.examen.academie() if self.examen else None


# ================================================
# MODELS.PY — Historique des interactions CRM
# ================================================


class InteractionCRM(models.Model):
    """Historique des échanges avec un prospect/lead."""

    TYPES = [
        ("appel", "📞 Appel"),
        ("email", "📧 Email"),
        ("whatsapp", "💬 WhatsApp"),
        ("rencontre", "🤝 Rencontre"),
        ("note", "📝 Note"),
    ]

    inscription = models.ForeignKey(
        Inscription, on_delete=models.CASCADE, related_name="interactions"
    )
    type_interaction = models.CharField(max_length=15, choices=TYPES, default="note")
    contenu = models.TextField()
    auteur = models.ForeignKey("auth.User", on_delete=models.SET_NULL, null=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date_creation"]
        verbose_name = "Interaction CRM"
        verbose_name_plural = "Interactions CRM"

    def __str__(self):
        return f"{self.get_type_interaction_display()} — {self.inscription}"


# ================================================
# MODELS.PY — Machine à États : Workflow de publication Formation
# ================================================
class WorkflowFormation(models.Model):
    """
    Machine à états pour le cycle de vie d'une formation.
    Remplace le simple booléen Formation.actif par un vrai processus
    éditorial avec traçabilité complète.
    """

    ETATS = [
        ("brouillon", "📝 Brouillon"),
        ("en_revision", "🔍 En révision"),
        ("validee", "✅ Validée — prête à publier"),
        ("publiee", "🌐 Publiée"),
        ("suspendue", "⏸️ Suspendue temporairement"),
        ("archivee", "📦 Archivée"),
    ]

    # Transitions autorisées : état actuel → liste des états accessibles
    TRANSITIONS_AUTORISEES = {
        "brouillon": ["en_revision", "archivee"],
        "en_revision": ["brouillon", "validee"],
        "validee": ["publiee", "brouillon"],
        "publiee": ["suspendue", "archivee"],
        "suspendue": ["publiee", "archivee"],
        "archivee": [],  # état final, aucune transition sortante
    }

    formation = models.OneToOneField(Formation, on_delete=models.CASCADE, related_name="workflow")
    etat_actuel = models.CharField(max_length=20, choices=ETATS, default="brouillon")

    demande_par = models.ForeignKey(
        "auth.User", on_delete=models.SET_NULL, null=True, related_name="workflows_demandes"
    )
    valide_par = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="workflows_valides",
    )

    checklist_contenu_complet = models.BooleanField(
        default=False, help_text="Modules et leçons rédigés"
    )
    checklist_seo_complet = models.BooleanField(
        default=False, help_text="Description et mots-clés renseignés"
    )
    checklist_prix_valide = models.BooleanField(
        default=False, help_text="Prix et promotions vérifiés"
    )
    checklist_quiz_present = models.BooleanField(default=False, help_text="Au moins un quiz créé")

    commentaire_revision = models.TextField(blank=True, help_text="Retours du réviseur si refus")
    date_creation = models.DateTimeField(auto_now_add=True)
    date_derniere_transition = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Workflow de formation"
        verbose_name_plural = "Workflows de formations"

    def __str__(self):
        return f"{self.formation.nom} — {self.get_etat_actuel_display()}"

    def peut_transitionner_vers(self, nouvel_etat):
        """Vérifie si la transition demandée est autorisée par la machine à états."""
        return nouvel_etat in self.TRANSITIONS_AUTORISEES.get(self.etat_actuel, [])

    def score_checklist(self):
        """Pourcentage de complétion de la checklist qualité."""
        items = [
            self.checklist_contenu_complet,
            self.checklist_seo_complet,
            self.checklist_prix_valide,
            self.checklist_quiz_present,
        ]
        return round((sum(items) / len(items)) * 100)

    def transitionner(self, nouvel_etat, utilisateur, commentaire=""):
        """
        Effectue la transition si autorisée. Retourne (succes: bool, message: str).
        Synchronise automatiquement Formation.actif selon le nouvel état.
        """
        if not self.peut_transitionner_vers(nouvel_etat):
            return False, f"Transition '{self.etat_actuel}' → '{nouvel_etat}' non autorisée."

        if nouvel_etat == "publiee" and self.score_checklist() < 100:
            return (
                False,
                f"Checklist incomplète ({self.score_checklist()}%) — impossible de publier.",
            )

        ancien_etat = self.etat_actuel
        self.etat_actuel = nouvel_etat

        if nouvel_etat == "publiee":
            self.valide_par = utilisateur
            self.formation.actif = True
            self.formation.save(update_fields=["actif"])
        elif nouvel_etat in ["suspendue", "archivee", "brouillon"]:
            self.formation.actif = False
            self.formation.save(update_fields=["actif"])

        if commentaire:
            self.commentaire_revision = commentaire

        self.save()

        # Journalisation automatique (réutilise LogAudit existant)
        LogAudit.objects.create(
            utilisateur=utilisateur,
            action="publication",
            description=f"Formation '{self.formation.nom}' : {ancien_etat} → {nouvel_etat}",
            objet_type="Formation",
            objet_id=self.formation.id,
        )
        return True, f"Transition réussie vers '{self.get_etat_actuel_display()}'"


# ================================================
# MODELS.PY — Système d'Affiliation
# ================================================
class Affilie(models.Model):
    """Partenaire affilié — génère des ventes via son lien unique."""

    utilisateur = models.OneToOneField(
        "auth.User", on_delete=models.CASCADE, related_name="affiliation"
    )
    code_affiliation = models.CharField(max_length=20, unique=True)
    taux_commission = models.DecimalField(
        max_digits=5, decimal_places=2, default=10, help_text="% de commission"
    )
    actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Affilié"
        verbose_name_plural = "Affiliés"

    def __str__(self):
        return f"{self.utilisateur.username} ({self.code_affiliation})"

    def save(self, *args, **kwargs):
        if not self.code_affiliation:
            self.code_affiliation = (
                f"AFF-{self.utilisateur.username[:6].upper()}{uuid.uuid4().hex[:4].upper()}"
            )
        super().save(*args, **kwargs)

    def commission_totale(self):
        from django.db.models import Sum

        ventes = (
            OrderItem.objects.filter(
                commande__affilie_origine=self, commande__statut="paye"
            ).aggregate(t=Sum("prix_unitaire"))["t"]
            or 0
        )
        return round(ventes * (self.taux_commission / 100), 2)


class CommissionAffiliation(models.Model):
    """Trace chaque commission générée — payée ou en attente."""

    STATUTS = [("en_attente", "En attente"), ("payee", "Payée")]

    affilie = models.ForeignKey(Affilie, on_delete=models.CASCADE, related_name="commissions")
    commande = models.ForeignKey(Order, on_delete=models.CASCADE)
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    statut = models.CharField(max_length=15, choices=STATUTS, default="en_attente")
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Commission affiliation"
        verbose_name_plural = "Commissions affiliation"


# ================================================
# MODELS.PY — Academie (racine Enterprise Multi-Academy)
# ================================================
class Academie(models.Model):
    """
    Racine de la plateforme Enterprise. Chaque Academie est une
    "marque" indépendante (Blessy Tech Academy, Blessy Business School...)
    partageant le même code et la même base de données.
    """

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
        return Formation.objects.filter(ecole__academie=self).count()

    def nb_etudiants(self):
        return ProfilUtilisateur.objects.filter(academies=self, role="etudiant").count()


# ================================================
# MODÈLE — PartenaireAPI (accès API tiers)
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
        verbose_name = "Partenaire API"
        verbose_name_plural = "Partenaires API"

    def __str__(self):
        return self.nom


# ================================================
# MODELS.PY — Journal des requêtes partenaires API
# Enregistre chaque appel API partenaire pour le
# monitoring, la facturation et les alertes de débit.
# ================================================
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
        verbose_name = "Log Requête Partenaire"
        verbose_name_plural = "Logs Requêtes Partenaires"
        ordering = ['-date_creation']

    def __str__(self):
        return f"{self.partenaire.nom} — {self.statut_reponse} ({self.date_creation})"
    

# ================================================
# MODELS.PY — Modèle Competence/Skill (normalisation pédagogique)
# Corrige le point audit : "compétences en TextField non structuré"
# ================================================

class Competence(models.Model):
    """
    Compétence normalisée — remplace progressivement les TextField 
    libres (competences_acquises, debouches) par des entités structurées, 
    requêtables et analysables.
    """

    CATEGORIES = [
        ('technique', '💻 Technique'), ('soft_skill', '🤝 Soft Skill'),
        ('outil', '🛠️ Outil/Logiciel'), ('methode', '📐 Méthodologie'),
    ]

    nom = models.CharField(max_length=150, unique=True)
    slug = models.SlugField(max_length=150, unique=True, blank=True)
    categorie = models.CharField(max_length=15, choices=CATEGORIES, default='technique')
    description = models.TextField(blank=True)
    icone = models.CharField(max_length=10, default='⚡')

    formations = models.ManyToManyField(Formation, blank=True, related_name='competences')
    modules = models.ManyToManyField(Module, blank=True, related_name='competences')
    lecons = models.ManyToManyField(Lecon, blank=True, related_name='competences')
    examens = models.ManyToManyField('Examen', blank=True, related_name='competences') if 'Examen' in dir() else None

    class Meta:
        verbose_name = 'Compétence'
        verbose_name_plural = 'Compétences'
        ordering = ['categorie', 'nom']

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
        """Étudiants ayant complété au moins 1 formation liée à cette compétence."""
        from django.contrib.auth.models import User
        return User.objects.filter(
            acces_debloques__formation__in=self.formations.all()
        ).distinct().count()


class LearningOutcome(models.Model):
    """
    Résultat d'apprentissage — objectif pédagogique mesurable, 
    rattaché à une formation. Complète Competence (le "quoi") 
    avec un objectif clair (le "ce que tu sauras faire").
    """

    formation = models.ForeignKey(Formation, on_delete=models.CASCADE, related_name='learning_outcomes')
    description = models.CharField(max_length=300, help_text="Ex: Être capable de créer une API REST avec Django")
    competence_associee = models.ForeignKey(Competence, on_delete=models.SET_NULL, null=True, blank=True)
    ordre = models.IntegerField(default=0)

    class Meta:
        ordering = ['ordre']
        verbose_name = "Résultat d'apprentissage"
        verbose_name_plural = "Résultats d'apprentissage"

    def __str__(self):
        return f"{self.formation.nom} — {self.description[:50]}"
    

# ================================================
# MODÈLE — Notification (système d'alertes)
# ================================================
class Notification(models.Model):
    """Notification envoyée à un utilisateur."""

    utilisateur = models.ForeignKey(
        "auth.User", on_delete=models.CASCADE, related_name="notifications"
    )
    titre = models.CharField(max_length=200)
    message = models.TextField()
    lien = models.URLField(blank=True, default="")
    lue = models.BooleanField(default=False)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date_creation"]
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"

    def __str__(self):
        statut = "✓" if self.lue else "●"
        return f"{statut} {self.titre} — {self.utilisateur.username}"


