# ================================================
# CONTENT/MODELS.PY — Knowledge Center + Portfolio + Certificats extraits
# app_label='academie' partout — zéro migration nécessaire
# ================================================

from django.db import models
from django.utils import timezone
from academie.validators import valider_document, valider_image   # <-- ajouté


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
        validators=[valider_document]   # <-- validateur ajouté
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
    prenom_nom = models.CharField(max_length=200)
    formation_suivie = models.ForeignKey('academie.Formation', on_delete=models.SET_NULL, null=True, blank=True, related_name='temoignages')
    texte = models.TextField()
    note = models.IntegerField(default=5, choices=[(i, f"{i} étoile{'s' if i > 1 else ''}") for i in range(1, 6)])
    initiales = models.CharField(max_length=3)
    titre_professionnel = models.CharField(max_length=200, blank=True)
    en_vedette = models.BooleanField(default=False)
    approuve = models.BooleanField(default=False)
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
    lien = models.URLField(null=True, blank=True)
    image = models.ImageField(
        upload_to='projets/',
        null=True,
        blank=True,
        validators=[valider_image]   # <-- validateur ajouté
    )
    formation_liee = models.ForeignKey('academie.Formation', on_delete=models.SET_NULL, null=True, blank=True, related_name='projets_realises')
    competences_demontrees = models.ManyToManyField('academie.Competence', blank=True, related_name='projets_demonstrations')
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'academie'
        db_table = 'academie_projetetudiant'
        ordering = ['-date_creation']
        verbose_name = 'Projet Étudiant'
        verbose_name_plural = 'Projets Étudiants'

    def __str__(self):
        return f"{self.titre} — {self.auteur.username}"


class Certificat(models.Model):
    utilisateur = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='certificats')
    formation = models.ForeignKey('academie.Formation', on_delete=models.SET_NULL, null=True, blank=True)
    examen_origine = models.ForeignKey('academie.Examen', on_delete=models.SET_NULL, null=True, blank=True)
    numero = models.CharField(max_length=50, unique=True, db_index=True, blank=True, editable=False)
    date_emission = models.DateTimeField(auto_now_add=True)
    fichier_pdf = models.FileField(
        upload_to='certificats/',
        null=True,
        blank=True,
        validators=[valider_document]   # <-- validateur ajouté
    )
    verifie = models.BooleanField(default=False)
    
    class Meta:
        app_label = 'academie'
        db_table = 'academie_certificat'
        verbose_name = 'Certificat'
        verbose_name_plural = 'Certificats'

    def __str__(self):
        return f"Certificat {self.numero} — {self.utilisateur.username}"

    def save(self, *args, **kwargs):
        if not self.numero:
            import secrets
            self.numero = secrets.token_hex(12).upper()  # 24 caractères hex aléatoires, non devinable
        super().save(*args, **kwargs)