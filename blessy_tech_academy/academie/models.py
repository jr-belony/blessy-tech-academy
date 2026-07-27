import uuid
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django_ckeditor_5.fields import CKEditor5Field
from simple_history.models import HistoricalRecords
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from users.models import ProfilUtilisateur, LogAudit, Enseignant, HistoriqueConversationIA, PushSubscription, NotificationPushEnvoyee
from billing.models import (
    MoyenPaiement, Coupon, Promotion, Order, OrderItem, Invoice,
    Transaction, Refund, AccesFormationDebloque, PlanAbonnement,
    Subscription, Affilie, CommissionAffiliation,
)


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
        "academie.Formation", on_delete=models.SET_NULL, null=True, blank=True, related_name="inscriptions"
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
        "academie.Formation", on_delete=models.SET_NULL, null=True, blank=True, related_name="sujets_forum"
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
    # MODELS.PY — Ajout traçabilité pédagogique
    formation_liee = models.ForeignKey(
    "academie.Formation", on_delete=models.SET_NULL, null=True, blank=True,
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
    formation = models.ForeignKey("academie.Formation", on_delete=models.CASCADE, related_name="certificats")
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
        "academie.Formation", on_delete=models.SET_NULL, null=True, blank=True, related_name="articles"
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
            suggestions.append("Contenu court — articles de 3+ min se référencent mieux")
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
        "academie.Formation", on_delete=models.SET_NULL, null=True, blank=True, related_name="temoignages"
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
        from academie.models import Formation
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
    

    # ================================================
# LEARNING/MODELS.PY — Modèles pédagogiques extraits d'academie
# Ecole, Formation, Module, Lecon, Quiz, Question, Parcours, 
# Examen, QuestionExamen, ChoixExamen, TentativeExamen, 
# Competence, LearningOutcome, WorkflowFormation
# app_label='academie' + db_table explicite = zéro perte de données
# ================================================

from django.db import models
from django.utils import timezone


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
    NIVEAUX = [('debutant', 'Débutant'), ('intermediaire', 'Intermédiaire'), ('avance', 'Avancé'), ('professionnel', 'Professionnel')]

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
        indexes = [models.Index(fields=['actif', 'niveau']), models.Index(fields=['ecole'])]

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
        total = sum(m.lecons.count() for m in self.modules.all())
        if total == 0:
            return 0
        from .models import ProgressionLecon
        terminees = ProgressionLecon.objects.filter(
            utilisateur=utilisateur, lecon__module__formation=self, terminee=True
        ).count()
        return round((terminees / total) * 100)


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
        indexes = [models.Index(fields=['utilisateur', 'terminee']), models.Index(fields=['lecon', 'terminee'])]


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
    CATEGORIES = [('technique', '💻 Technique'), ('soft_skill', '🤝 Soft Skill'), ('outil', '🛠️ Outil/Logiciel'), ('methode', '📐 Méthodologie')]
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
        ('brouillon', '📝 Brouillon'), ('en_revision', '🔍 En révision'),
        ('validee', '✅ Validée'), ('publiee', '🌐 Publiée'),
        ('suspendue', '⏸️ Suspendue'), ('archivee', '📦 Archivée'),
    ]
    TRANSITIONS_AUTORISEES = {
        'brouillon': ['en_revision', 'archivee'], 'en_revision': ['brouillon', 'validee'],
        'validee': ['publiee', 'brouillon'], 'publiee': ['suspendue', 'archivee'],
        'suspendue': ['publiee', 'archivee'], 'archivee': [],
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
    type_question = models.CharField(max_length=15, choices=[('qcm', 'QCM'), ('vrai_faux', 'Vrai/Faux'), ('texte', 'Texte libre')], default='qcm')
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