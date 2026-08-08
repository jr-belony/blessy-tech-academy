# ================================================
# CONTENT/MODELS.PY — Knowledge Center + Portfolio + Certificats extraits
# app_label='academie' partout — zéro migration nécessaire
# ================================================
import uuid
from django.db import models, transaction
from django.utils import timezone
from academie.validators import valider_document, valider_image


class Article(models.Model):
    CATEGORIES = [
        ('guide', '📖 Guide'), ('tutoriel', '🎓 Tutoriel'), ('actualite', '📰 Actualité'),
        ('conseil', '💡 Conseil'), ('outil', '🛠️ Outil'),
    ]
    TYPES_CONTENU = [
        ('article', '📝 Article'), ('guide', '📖 Guide'), ('tutoriel', '🎓 Tutoriel'),
        ('etude_cas', '📊 Étude de cas'), ('actualite', '📰 Actualité Tech'),
        ('livre_blanc', '📄 Livre blanc'), ('faq', '❓ FAQ'),
    ]

    titre = models.CharField(max_length=300)
    slug = models.SlugField(max_length=300, unique=True, blank=True)
    resume = models.TextField(max_length=500)
    contenu = models.TextField(blank=True)
    categorie = models.CharField(max_length=20, choices=CATEGORIES, default='guide')
    type_contenu = models.CharField(max_length=20, choices=TYPES_CONTENU, default='article')
    formation_liee = models.ForeignKey('academie.Formation', on_delete=models.SET_NULL, null=True, blank=True, related_name='articles')
    academie = models.ForeignKey('academie.Academie', on_delete=models.SET_NULL, null=True, blank=True, related_name='articles')
    auteur = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='articles')
    en_vedette = models.BooleanField(default=False)
    publie = models.BooleanField(default=False)
    temps_lecture = models.IntegerField(default=5)
    fichier_telechargeable = models.FileField(
        upload_to='knowledge_center/',
        null=True,
        blank=True,
        validators=[valider_document]
    )
    articles_associes = models.ManyToManyField('self', blank=True, symmetrical=True)
    nb_vues = models.IntegerField(default=0)
    nb_partages = models.IntegerField(default=0)
    meta_titre = models.CharField(max_length=70, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)
    mots_cles = models.CharField(max_length=255, blank=True)
    noindex = models.BooleanField(default=False)
    date_publication = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    # --- NOUVEAUX CHAMPS POUR LE WORKFLOW ÉDITORIAL LÉGER ---
    STATUTS_EDITORIAUX = [
        ('brouillon', '📝 Brouillon'),
        ('en_relecture', '🔍 En relecture'),
        ('publie', '🌐 Publié'),
        ('archive', '📦 Archivé'),
    ]
    statut_editorial = models.CharField(
        max_length=15,
        choices=STATUTS_EDITORIAUX,
        default='brouillon'
    )
    relu_par = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='articles_relus'
    )

    class Meta:
        app_label = 'academie'
        db_table = 'academie_article'
        ordering = ['-en_vedette', '-date_publication']
        verbose_name = 'Article'
        verbose_name_plural = 'Articles'

    def __str__(self):
        return self.titre

    def save(self, *args, **kwargs):
        # Génération automatique du slug
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.titre)

        # Synchronisation cohérente : publie reflète statut_editorial
        self.publie = (self.statut_editorial == 'publie')

        super().save(*args, **kwargs)

    def temps_lecture_estime(self):
        import re
        texte_brut = re.sub('<[^<]+?>', '', self.contenu or '')
        nb_mots = len(texte_brut.split())
        return max(1, round(nb_mots / 200))

    def score_seo(self):
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
        suggestions = []
        if not self.meta_titre:
            suggestions.append("Ajoute un titre SEO (50-70 caractères)")
        elif not (50 <= len(self.meta_titre) <= 70):
            suggestions.append(f"Titre SEO actuel : {len(self.meta_titre)} caractères — vise 50-70")
        if not self.meta_description:
            suggestions.append("Ajoute une meta description (120-160 caractères)")
        if not self.mots_cles:
            suggestions.append("Renseigne des mots-clés principaux")
        return suggestions


class WorkflowArticle(models.Model):
    """Workflow de publication pour un article — similaire à WorkflowFormation."""

    ETATS = [
        ('brouillon', '📝 Brouillon'),
        ('en_revision', '🔍 En révision'),
        ('valide', '✅ Validé'),
        ('publie', '🌐 Publié'),
        ('archive', '📦 Archivé'),
    ]

    TRANSITIONS_AUTORISEES = {
        'brouillon': ['en_revision', 'archive'],
        'en_revision': ['brouillon', 'valide'],
        'valide': ['publie', 'brouillon'],
        'publie': ['archive'],
        'archive': [],
    }

    article = models.OneToOneField(
        'Article',
        on_delete=models.CASCADE,
        related_name='workflow'
    )
    etat_actuel = models.CharField(
        max_length=20,
        choices=ETATS,
        default='brouillon'
    )
    demande_par = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='workflows_articles_demandes'
    )
    valide_par = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='workflows_articles_valides'
    )
    checklist_seo_complet = models.BooleanField(default=False)
    checklist_image_presente = models.BooleanField(default=False)
    commentaire_revision = models.TextField(blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_derniere_transition = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'academie'
        db_table = 'academie_workflowarticle'
        verbose_name = 'Workflow article'
        verbose_name_plural = 'Workflows articles'

    def __str__(self):
        return f"{self.article.titre} — {self.get_etat_actuel_display()}"

    def peut_transitionner_vers(self, nouvel_etat):
        """Vérifie si la transition est autorisée."""
        return nouvel_etat in self.TRANSITIONS_AUTORISEES.get(self.etat_actuel, [])

    def score_checklist(self):
        """Calcule le pourcentage de checklist complétée."""
        items = [self.checklist_seo_complet, self.checklist_image_presente]
        return round((sum(items) / len(items)) * 100)

    def transitionner(self, nouvel_etat, utilisateur, commentaire=''):
        """
        Effectue une transition d'état si elle est autorisée.
        Met à jour l'article.publie en fonction de l'état.
        """
        if not self.peut_transitionner_vers(nouvel_etat):
            return False, f"Transition '{self.etat_actuel}' → '{nouvel_etat}' non autorisée."

        # Exemple de règle : pour passer à 'publie', la checklist doit être à 100%
        if nouvel_etat == 'publie' and self.score_checklist() < 100:
            return False, f"Checklist incomplète ({self.score_checklist()}%)."

        ancien_etat = self.etat_actuel
        self.etat_actuel = nouvel_etat

        if nouvel_etat == 'publie':
            self.valide_par = utilisateur
            self.article.publie = True
            self.article.save(update_fields=['publie'])
        elif nouvel_etat in ['archive', 'brouillon']:
            self.article.publie = False
            self.article.save(update_fields=['publie'])

        if commentaire:
            self.commentaire_revision = commentaire

        self.save()

        from users.models import LogAudit
        LogAudit.objects.create(
            utilisateur=utilisateur,
            action='publication_article',
            description=f"Article '{self.article.titre}' : {ancien_etat} → {nouvel_etat}",
            objet_type='Article',
            objet_id=self.article.id,
        )
        return True, f"Transition réussie vers '{self.get_etat_actuel_display()}'"


class OutilRecommande(models.Model):
    CATEGORIES = [
        ('developpement', '💻 Développement'), ('design', '🎨 Design'), ('ia', '🤖 IA'),
        ('productivite', '⚡ Productivité'), ('collaboration', '👥 Collaboration'), ('securite', '🔐 Sécurité'),
    ]
    nom = models.CharField(max_length=200)
    description = models.TextField(max_length=400)
    url = models.URLField()
    icone = models.CharField(max_length=10, default='🛠️')
    categorie = models.CharField(max_length=20, choices=CATEGORIES, default='developpement')
    gratuit = models.BooleanField(default=True)
    recommande_par_bta = models.BooleanField(default=True)
    ordre = models.IntegerField(default=0)

    class Meta:
        app_label = 'academie'
        db_table = 'academie_outilrecommande'
        ordering = ['ordre', 'nom']

    def __str__(self):
        return f"{self.icone} {self.nom}"


class Temoignage(models.Model):
    STATUT_TEMOIGNAGE = [
        ('demande', 'Demande envoyée'),
        ('consenti', 'Consentement obtenu'),
        ('redige', 'Rédigé'),
        ('valide', 'Validé par admin'),
        ('publie', 'Publié'),
    ]
    prenom_nom = models.CharField(max_length=200)
    formation_suivie = models.ForeignKey('academie.Formation', on_delete=models.SET_NULL, null=True, blank=True, related_name='temoignages')
    texte = models.TextField()
    note = models.IntegerField(default=5, choices=[(i, f"{i} étoile{'s' if i > 1 else ''}") for i in range(1, 6)])
    initiales = models.CharField(max_length=3)
    titre_professionnel = models.CharField(max_length=200, blank=True)
    en_vedette = models.BooleanField(default=False)
    approuve = models.BooleanField(default=False)
    statut = models.CharField(max_length=15, choices=STATUT_TEMOIGNAGE, default='redige')
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'academie'
        db_table = 'academie_temoignage'
        ordering = ['-en_vedette', '-date_creation']

    def __str__(self):
        return f"{self.prenom_nom} — {self.note}⭐"


class ProjetEtudiant(models.Model):
    auteur = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='projets')
    titre = models.CharField(max_length=200)
    description = models.TextField()
    technologies = models.CharField(max_length=300, blank=True)
    competences_developpees = models.CharField(max_length=500, blank=True, default='')
    lien = models.URLField(null=True, blank=True)
    image = models.ImageField(
        upload_to='projets/',
        null=True,
        blank=True,
        validators=[valider_image]
    )
    formation_liee = models.ForeignKey('academie.Formation', on_delete=models.SET_NULL, null=True, blank=True, related_name='projets_realises')
    competences_demontrees = models.ManyToManyField('academie.Competence', blank=True, related_name='projets_demonstrations')
    date_creation = models.DateTimeField(auto_now_add=True)
    niveau_difficulte = models.CharField(max_length=20, default='debutant')
    probleme_traite = models.TextField(blank=True, help_text="Quel problème ce projet résout-il ?")
    outils_utilises = models.CharField(max_length=300, blank=True)
    resultat_obtenu = models.TextField(blank=True, help_text="Résultat concret obtenu")
    valide_par_formateur = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='projets_valides_par_moi')
    date_validation = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = 'academie'
        db_table = 'academie_projetetudiant'
        ordering = ['-date_creation']
        verbose_name = 'Projet Étudiant'
        verbose_name_plural = 'Projets Étudiants'

    def __str__(self):
        return f"{self.titre} — {self.auteur.username}"


class Certificat(models.Model):
    NIVEAUX = [('initiation', 'Initiation'), ('intermediaire', 'Intermédiaire'), ('avance', 'Avancé')]
    STATUTS = [('valide', '✅ Valide'), ('revoque', '❌ Révoqué'), ('expire', '⏳ Expiré')]

    utilisateur = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='certificats')
    formation = models.ForeignKey('academie.Formation', on_delete=models.SET_NULL, null=True, blank=True)
    parcours_origine = models.ForeignKey(
        'Parcours',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='certificats_delivres'
    )
    examen_origine = models.ForeignKey('academie.Examen', on_delete=models.SET_NULL, null=True, blank=True)

    # ============ NOUVEAUX CHAMPS (cohorte pilote / multi‑formations) ============
    formations_incluses = models.ManyToManyField(
        'academie.Formation',
        blank=True,
        related_name='certificats_inclus_dans',
        help_text="Liste des formations couvertes par ce certificat (ex: pour un parcours ou une cohorte)"
    )
    mention = models.CharField(
        max_length=50,
        blank=True,
        help_text="Ex: Très Bien, Bien, Assez Bien, Félicitations"
    )
    libelle_programme = models.CharField(
        max_length=200,
        blank=True,
        help_text="Ex: Compétences Numériques Professionnelles – Programme Fondateur"
    )
    # =============================================================================

    # --- IDENTIFIANTS PUBLICS (UUID public) ---
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True,
        help_text="Identifiant universel public pour la vérification"
    )
    numero = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        blank=True,
        editable=False,
        help_text="Numéro lisible (ex: BTA-2026-PRO-0001)"
    )

    # --- HASH D'INTÉGRITÉ (empreinte immuable) ---
    hash = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        help_text="SHA-256 du contenu du certificat pour vérification d'intégrité"
    )

    # --- MÉTA-DONNÉES ---
    niveau = models.CharField(max_length=20, choices=NIVEAUX, default='initiation')
    statut = models.CharField(max_length=15, choices=STATUTS, default='valide')
    duree_heures = models.IntegerField(default=0, help_text="Durée totale de la formation en heures")
    resultat_final = models.IntegerField(null=True, blank=True, help_text="Score/pourcentage final si examen")

    # --- RÉVOCATION (avec traçabilité de l'auteur) ---
    date_revocation = models.DateTimeField(null=True, blank=True, help_text="Date de révocation (si révoqué)")
    raison_revocation = models.TextField(null=True, blank=True, help_text="Raison de la révocation")
    revoque_par = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='certificats_revoques'
    )

    # --- FICHIERS ---
    qr_code_image = models.ImageField(upload_to='certificats/qr/', null=True, blank=True)
    fichier_pdf = models.FileField(
        upload_to='certificats/',
        null=True,
        blank=True,
        validators=[valider_document]
    )
    date_emission = models.DateTimeField(auto_now_add=True)
    verifie = models.BooleanField(default=False, help_text="Indique si le certificat a été vérifié publiquement")

    class Meta:
        app_label = 'academie'
        db_table = 'academie_certificat'
        verbose_name = 'Certificat'
        verbose_name_plural = 'Certificats'
        permissions = [
            ("can_generate_certificat", "Peut générer un certificat"),
            ("can_revoke_certificat", "Peut révoquer un certificat"),
        ]

    def __str__(self):
        return f"{self.numero} — {self.utilisateur.username}"

    def _generer_hash(self):
        """Calcule le SHA-256 du contenu du certificat."""
        import hashlib
        contenu = (
            f"{self.numero}"
            f"{self.date_emission.isoformat()}"
            f"{self.formation.nom if self.formation else 'N/A'}"
            f"{self.utilisateur.username}"
            f"{self.resultat_final or ''}"
            f"{self.duree_heures}"
        )
        return hashlib.sha256(contenu.encode()).hexdigest()

    def save(self, *args, **kwargs):
        # 1. Générer le numéro si absent
        if not self.numero:
            self.numero = self._generer_numero_lisible()

        # 2. Calculer la durée en heures
        if not self.duree_heures and self.formation:
            from django.db.models import Sum
            from academie.models import Lecon

            total_minutes = Lecon.objects.filter(
                module__formation=self.formation
            ).aggregate(t=Sum('duree_minutes'))['t'] or 0

            if total_minutes > 0:
                self.duree_heures = round(total_minutes / 60)
            else:
                # Fallback basé sur la durée de la formation (heures/jours/semaines)
                if self.formation.duree_unite == 'heures':
                    self.duree_heures = self.formation.duree
                elif self.formation.duree_unite == 'jours':
                    self.duree_heures = self.formation.duree * 8
                elif self.formation.duree_unite == 'semaines':
                    self.duree_heures = self.formation.duree * 20
                else:
                    self.duree_heures = self.formation.duree * 20

        # 3. Récupérer le résultat final depuis l'examen
        if not self.resultat_final and self.examen_origine:
            derniere_tentative = self.examen_origine.tentatives.filter(
                utilisateur=self.utilisateur, reussi=True
            ).order_by('-date_passage').first()
            if derniere_tentative:
                self.resultat_final = derniere_tentative.pourcentage

        # 4. Sauvegarder
        super().save(*args, **kwargs)

        # 5. Générer le QR code si absent
        if not self.qr_code_image:
            self._generer_qr_code()

        # 6. Générer le hash (après la sauvegarde pour avoir l'ID)
        if not self.hash:
            self.hash = self._generer_hash()
            # Resauvegarder uniquement le hash pour ne pas boucler
            Certificat.objects.filter(id=self.id).update(hash=self.hash)

    def _generer_numero_lisible(self):
        annee = timezone.now().year
        code_formation = (
            self.formation.slug[:3].upper()
            if self.formation and self.formation.slug
            else 'BTA'
        )
        with transaction.atomic():
            dernier = Certificat.objects.select_for_update().filter(
                formation=self.formation,
                date_emission__year=annee
            ).count()
            sequence = str(dernier + 1).zfill(4)
        return f"BTA-{annee}-{code_formation}-{sequence}"

    def _generer_qr_code(self):
        try:
            import qrcode
            from io import BytesIO
            from django.core.files.base import ContentFile
            from django.conf import settings

            url_verification = f"{getattr(settings, 'SITE_URL', '')}/certificat/{self.numero}/"
            qr = qrcode.make(url_verification)
            buffer = BytesIO()
            qr.save(buffer, format='PNG')
            self.qr_code_image.save(
                f"qr_{self.numero}.png",
                ContentFile(buffer.getvalue()),
                save=False
            )
            super().save(update_fields=['qr_code_image'])
        except ImportError:
            pass

    def verifier_hash(self):
        """Vérifie que le hash stocké correspond au recalcul."""
        return self.hash == self._generer_hash()

    def revoquer(self, admin, raison=""):
        """
        Révoque le certificat avec contrôle d'accès RBAC.
        Seul un administrateur avec la permission 'certificat.revoquer' peut exécuter cette action.
        """
        from academie.permissions import peut
        if not peut(admin, 'certificat.revoquer'):
            raise PermissionError("Seul un administrateur peut révoquer un certificat.")

        self.statut = 'revoque'
        self.date_revocation = timezone.now()
        self.raison_revocation = raison
        self.revoque_par = admin
        self.save(update_fields=['statut', 'date_revocation', 'raison_revocation', 'revoque_par'])

        # Enregistrer dans l'historique
        CertificatHistorique.objects.create(
            certificat=self,
            statut=self.statut,
            raison=f"Révocation par {admin.username} : {raison}" if raison else f"Révocation par {admin.username}",
            auteur=admin
        )

    def est_valide(self):
        """Vérifie si le certificat est valide (non révoqué et non expiré)."""
        return self.statut == 'valide'

    def competences_associees(self):
        from academie.models import CompetenceValidee
        return CompetenceValidee.objects.filter(
            utilisateur=self.utilisateur,
            formation_origine=self.formation
        ).select_related('competence')

    # Calcul automatique de la mention
    def calculer_mention(self):
        """Détermine la mention selon resultat_final — cohérent avec les standards académiques."""
        if not self.resultat_final:
            return ''
        if self.resultat_final >= 90:
            return 'Excellent'
        if self.resultat_final >= 80:
            return 'Très Bien'
        if self.resultat_final >= 70:
            return 'Bien'
        if self.resultat_final >= 60:
            return 'Assez Bien'
        return ''

# ================================================
# [AJOUT AUDIT] Registre d'historique immuable pour les certificats
# ================================================

class CertificatHistorique(models.Model):
    """Registre immuable de tous les événements sur un certificat."""
    certificat = models.ForeignKey(Certificat, on_delete=models.CASCADE, related_name='historique')
    statut = models.CharField(max_length=15, choices=Certificat.STATUTS)
    raison = models.TextField(blank=True)
    date = models.DateTimeField(default=timezone.now)
    auteur = models.ForeignKey('auth.User', null=True, on_delete=models.SET_NULL)

    class Meta:
        app_label = 'academie'
        db_table = 'academie_certificathistorique'
        ordering = ['-date']
        verbose_name = 'Historique certificat'
        verbose_name_plural = 'Historique certificats'

    def __str__(self):
        return f"{self.certificat.numero} — {self.statut} ({self.date.strftime('%Y-%m-%d %H:%M')})"