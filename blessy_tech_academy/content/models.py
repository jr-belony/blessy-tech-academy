# ================================================
# CONTENT/MODELS.PY — Knowledge Center + Portfolio + Certificats extraits
# app_label='academie' partout — zéro migration nécessaire
# ================================================

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

    class Meta:
        app_label = 'academie'
        db_table = 'academie_article'
        ordering = ['-en_vedette', '-date_publication']
        verbose_name = 'Article'
        verbose_name_plural = 'Articles'

    def __str__(self):
        return self.titre

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.titre)
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
    examen_origine = models.ForeignKey('academie.Examen', on_delete=models.SET_NULL, null=True, blank=True)

    numero = models.CharField(max_length=50, unique=True, db_index=True, blank=True, editable=False)
    niveau = models.CharField(max_length=20, choices=NIVEAUX, default='initiation')
    statut = models.CharField(max_length=15, choices=STATUTS, default='valide')
    duree_heures = models.IntegerField(default=0, help_text="Durée totale de la formation en heures")
    resultat_final = models.IntegerField(null=True, blank=True, help_text="Score/pourcentage final si examen")

    qr_code_image = models.ImageField(upload_to='certificats/qr/', null=True, blank=True)
    date_emission = models.DateTimeField(auto_now_add=True)
    fichier_pdf = models.FileField(
        upload_to='certificats/',
        null=True,
        blank=True,
        validators=[valider_document]
    )
    verifie = models.BooleanField(default=False)

    class Meta:
        app_label = 'academie'
        db_table = 'academie_certificat'
        verbose_name = 'Certificat'
        verbose_name_plural = 'Certificats'

    def __str__(self):
        return f"{self.numero} — {self.utilisateur.username}"

    def save(self, *args, **kwargs):
        if not self.numero:
            self.numero = self._generer_numero_lisible()

        # duree_heures auto-calculée
        if not self.duree_heures and self.formation:
            # Calcul réel basé sur les leçons existantes si disponibles
            from django.db.models import Sum
            from academie.models import Lecon
            
            total_minutes = Lecon.objects.filter(
                module__formation=self.formation
            ).aggregate(t=Sum('duree_minutes'))['t'] or 0

            if total_minutes > 0:
                self.duree_heures = round(total_minutes / 60)
            else:
                # Fallback si aucune leçon chronométrée : estimation via duree
                if self.formation.duree_unite == 'heures':
                    self.duree_heures = self.formation.duree
                elif self.formation.duree_unite == 'jours':
                    self.duree_heures = self.formation.duree * 8  # 8h par jour
                elif self.formation.duree_unite == 'semaines':
                    self.duree_heures = self.formation.duree * 20  # 20h par semaine
                else:  # mois
                    self.duree_heures = self.formation.duree * 20  # 20h par mois

        if not self.resultat_final and self.examen_origine:
            derniere_tentative = self.examen_origine.tentatives.filter(
                utilisateur=self.utilisateur, reussi=True
            ).order_by('-date_passage').first()
            if derniere_tentative:
                self.resultat_final = derniere_tentative.pourcentage

        super().save(*args, **kwargs)
        if not self.qr_code_image:
            self._generer_qr_code()

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

    def competences_associees(self):
        from academie.models import CompetenceValidee
        return CompetenceValidee.objects.filter(
            utilisateur=self.utilisateur,
            formation_origine=self.formation
        ).select_related('competence')