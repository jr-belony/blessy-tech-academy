# ================================================
# MODELS_BANQUE.PY — Banque Officielle de Questions BTA
# Système isolé, réutilisable, extensible sans refonte
# Import dans academie/models.py via : from academie.models_banque import *
# ================================================

from django.db import models
from django.utils import timezone
import uuid


# ================================================
# 1. TAXONOMIE — Module → Catégorie → Sous-catégorie
# ================================================

class ModuleBanque(models.Model):
    """Les 4 grands domaines de compétences (extensible à l'infini)."""

    nom = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True, help_text="Ex: INT, IA, BUR, STK")
    icone = models.CharField(max_length=10, default='📚')
    hors_examen_principal = models.BooleanField(default=False, help_text="Ex: Gestion de Stock = bonus")
    ordre = models.IntegerField(default=0)

    class Meta:
        ordering = ['ordre']
        verbose_name = 'Module (Banque)'
        verbose_name_plural = 'Modules (Banque)'

    def __str__(self):
        return f"{self.icone} {self.nom}"


class CategorieBanque(models.Model):
    """Catégories par module (ex: Navigation Web, Sécurité numérique...)."""

    module = models.ForeignKey(ModuleBanque, on_delete=models.CASCADE, related_name='categories')
    nom = models.CharField(max_length=150)
    ordre = models.IntegerField(default=0)
    competence_associee = models.ForeignKey(
        'Competence',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='categories_banque',
        help_text="Compétence validée automatiquement si l'étudiant réussit une question de cette catégorie"
    )
    class Meta:
        ordering = ['module', 'ordre']
        unique_together = ['module', 'nom']
        verbose_name = 'Catégorie (Banque)'
        verbose_name_plural = 'Catégories (Banque)'

    def __str__(self):
        return f"{self.module.code} — {self.nom}"


class SousCategorieBanque(models.Model):
    """Granularité fine (optionnelle) — permet un ciblage précis des compétences."""

    categorie = models.ForeignKey(CategorieBanque, on_delete=models.CASCADE, related_name='sous_categories')
    nom = models.CharField(max_length=150)

    class Meta:
        verbose_name = 'Sous-catégorie (Banque)'
        verbose_name_plural = 'Sous-catégories (Banque)'

    def __str__(self):
        return f"{self.categorie} → {self.nom}"


# ================================================
# 2. QUESTION — Le cœur du système, riche en métadonnées
# ================================================

class QuestionBanque(models.Model):
    """
    Une question réutilisable — répond exactement à la structure demandée :
    identifiant, module, catégorie, sous-catégorie, niveau, compétence, 
    question, illustration, réponses, explication, référence, temps, 
    points, mots-clés.
    """

    NIVEAUX = [
        ('facile', '🟢 Facile'), ('intermediaire', '🟡 Intermédiaire'),
        ('avance', '🟠 Avancé'), ('professionnel', '🔴 Professionnel'),
    ]

    # Pondération par niveau — utilisée dans le calcul de score et la génération d'examen
    PONDERATION_NIVEAU = {'facile': 1.0, 'intermediaire': 1.3, 'avance': 1.6, 'professionnel': 2.0}

    TYPES_QUESTION = [
        ('qcm', 'QCM (une seule bonne réponse)'),
        ('choix_multiples', 'Choix multiples (plusieurs bonnes réponses)'),
        ('vrai_faux', 'Vrai / Faux'),
        ('association', 'Association (relier des éléments)'),
        ('classement', 'Classement (ordonner des éléments)'),
        ('completer', 'Compléter une phrase'),
        ('reponse_courte', 'Réponse courte (texte libre)'),
        ('etude_cas', 'Étude de cas'),
        ('analyse_image', "Analyse d'image / capture d'écran"),
        ('scenario_pro', 'Scénario professionnel'),
        ('analyse_prompt_ia', 'Prompt IA à analyser'),
        ('correction_word', 'Document Word à corriger'),
        ('analyse_excel', 'Feuille Excel à analyser'),
        ('amelioration_ppt', 'Présentation PowerPoint à améliorer'),
    ]

    STATUTS = [('brouillon', '📝 Brouillon'), ('active', '✅ Active'), ('archivee', '📦 Archivée'), ('en_revision', '🔍 En révision')]

    # --- Identification ---
    identifiant_unique = models.CharField(max_length=20, unique=True, editable=False, db_index=True, help_text="Ex: INT-NAV-0001")
    module = models.ForeignKey(ModuleBanque, on_delete=models.PROTECT, related_name='questions')
    categorie = models.ForeignKey(CategorieBanque, on_delete=models.PROTECT, related_name='questions')
    sous_categorie = models.ForeignKey(SousCategorieBanque, on_delete=models.SET_NULL, null=True, blank=True, related_name='questions')

    # --- Classification pédagogique ---
    niveau = models.CharField(max_length=15, choices=NIVEAUX, default='intermediaire')
    type_question = models.CharField(max_length=25, choices=TYPES_QUESTION, default='qcm')
    competence_evaluee = models.ForeignKey('Competence', on_delete=models.SET_NULL, null=True, blank=True, related_name='questions_banque')

    # --- Contenu ---
    enonce = models.TextField(help_text="Le texte de la question")
    illustration = models.ImageField(upload_to='banque_questions/illustrations/', null=True, blank=True)
    fichier_support = models.FileField(upload_to='banque_questions/fichiers/', null=True, blank=True, help_text="Document Word/Excel/PPT à analyser si applicable")

    # --- Réponses (structure JSON flexible selon type_question) ---
    reponses_possibles = models.JSONField(
        default=list,
        help_text='QCM: [{"texte": "...", "correct": true}]. Association: [{"gauche": "...", "droite": "..."}]. Classement: ["étape1", "étape2"...]'
    )
    reponse_texte_courte = models.CharField(max_length=300, blank=True, help_text="Pour type 'reponse_courte' — réponse(s) acceptée(s), séparées par |")

    # --- Pédagogie ---
    explication_pedagogique = models.TextField(help_text="Affichée APRÈS soumission, jamais avant")
    reference_cours = models.CharField(max_length=200, blank=True, help_text="Ex: Formation Bureautique — Module 3, Leçon 2")
    mots_cles = models.CharField(max_length=300, blank=True, help_text="Séparés par des virgules — pour la recherche")

    # --- Paramètres examen ---
    temps_conseille_secondes = models.IntegerField(default=90)
    points_base = models.DecimalField(max_digits=5, decimal_places=2, default=1.0)

    # --- Gouvernance ---
    statut = models.CharField(max_length=15, choices=STATUTS, default='brouillon')
    version = models.IntegerField(default=1, editable=False)
    cree_par = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, related_name='questions_creees')
    valide_par = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='questions_validees')
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    # MODELS_BANQUE.PY — Traçabilité de révision (feedback pilote)
    commentaire_revision = models.TextField(blank=True, help_text="Notes sur pourquoi cette question a été signalée/ajustée suite au test pilote")
    signalee_ambigue = models.BooleanField(default=False, help_text="Marquée par un apprenant ou l'admin comme potentiellement ambiguë")

    class Meta:
        verbose_name = 'Question (Banque)'
        verbose_name_plural = 'Questions (Banque)'
        indexes = [
            models.Index(fields=['module', 'niveau', 'statut']),
            models.Index(fields=['categorie', 'statut']),
        ]

    def __str__(self):
        return f"{self.identifiant_unique} — {self.enonce[:60]}"

    def save(self, *args, **kwargs):
        if not self.identifiant_unique:
            self.identifiant_unique = self._generer_identifiant()
        super().save(*args, **kwargs)

    def _generer_identifiant(self):
        """Génère INT-NAV-0001 (module-categorie-sequence)."""
        from django.utils.text import slugify
        prefixe_categorie = slugify(self.categorie.nom)[:3].upper()
        dernier = QuestionBanque.objects.filter(
            identifiant_unique__startswith=f"{self.module.code}-{prefixe_categorie}-"
        ).count()
        return f"{self.module.code}-{prefixe_categorie}-{str(dernier + 1).zfill(4)}"

    def points_ponderes(self):
        """Points réels selon la difficulté — cohérence de notation."""
        return round(float(self.points_base) * self.PONDERATION_NIVEAU.get(self.niveau, 1.0), 2)

    def dupliquer(self, utilisateur):
        """Duplication demandée dans l'admin — pour créer des variantes rapidement."""
        nouvelle = QuestionBanque.objects.get(pk=self.pk)
        nouvelle.pk = None
        nouvelle.identifiant_unique = ''  # sera régénéré
        nouvelle.statut = 'brouillon'
        nouvelle.cree_par = utilisateur
        nouvelle.version = 1
        nouvelle.save()
        return nouvelle


class VersionQuestionBanque(models.Model):
    """Historique immuable des versions d'une question (audit + rollback)."""

    question = models.ForeignKey(QuestionBanque, on_delete=models.CASCADE, related_name='historique_versions')
    numero_version = models.IntegerField()
    contenu_snapshot = models.JSONField(help_text="Snapshot complet des champs au moment de cette version")
    modifie_par = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    date_modification = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-numero_version']
        verbose_name = 'Version de question'
        verbose_name_plural = 'Versions de questions'


# ================================================
# 3. GÉNÉRATION D'EXAMEN — Instance unique par étudiant
# ================================================

class GabaritExamen(models.Model):
    """
    Modèle de composition d'examen — définit les RÈGLES de génération, 
    pas un examen figé. Ex: "20 Internet + 15 IA + 15 Bureautique = 50 
    questions, 90 min, 60 points".
    """

    nom = models.CharField(max_length=200)
    formation_liee = models.ForeignKey('Formation', on_delete=models.SET_NULL, null=True, blank=True)
    # --- NOUVEAUX CHAMPS ---
    cohorte_pilote = models.ForeignKey(
        'Cohorte', on_delete=models.SET_NULL, null=True, blank=True, related_name='gabarits_test',
        help_text="Si défini, ce gabarit est en phase de TEST avec cette cohorte avant généralisation"
    )
    phase_test = models.BooleanField(default=False, help_text="Active le mode test — statistiques suivies de près pour ajustement")
    # -----------------------
    duree_minutes = models.IntegerField(default=90)
    seuil_reussite = models.IntegerField(default=70)
    actif = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Gabarit d'examen"
        verbose_name_plural = "Gabarits d'examen"

    def __str__(self):
        return self.nom

    def nombre_questions_total(self):
        return sum(c.nombre_questions for c in self.composition.all())

    def points_total(self):
        return sum(c.nombre_questions * c.points_par_question for c in self.composition.all())

class CompositionGabarit(models.Model):
    """Ligne de composition : X questions de tel module/niveau dans le gabarit."""

    gabarit = models.ForeignKey(GabaritExamen, on_delete=models.CASCADE, related_name='composition')
    module = models.ForeignKey(ModuleBanque, on_delete=models.CASCADE)
    niveau = models.CharField(max_length=15, choices=QuestionBanque.NIVEAUX, blank=True, help_text="Vide = tous niveaux")
    nombre_questions = models.IntegerField(default=10)
    points_par_question = models.DecimalField(max_digits=5, decimal_places=2, default=1.0)

    class Meta:
        verbose_name = 'Composition du gabarit'
        verbose_name_plural = 'Compositions du gabarit'

    def __str__(self):
        return f"{self.gabarit.nom} — {self.nombre_questions}x {self.module.code} ({self.niveau or 'tous niveaux'})"


class ExamenGenere(models.Model):
    """
    UN examen réellement passé par UN étudiant — questions et réponses 
    tirées aléatoirement selon le GabaritExamen. Jamais 2 étudiants 
    n'ont exactement le même examen.
    """

    STATUTS = [('en_cours', '⏳ En cours'), ('termine', '✅ Terminé'), ('abandonne', '❌ Abandonné')]

    gabarit = models.ForeignKey(GabaritExamen, on_delete=models.PROTECT, related_name='examens_generes')
    utilisateur = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='examens_banque')

    questions_tirees = models.ManyToManyField(QuestionBanque, through='QuestionExamenGenere')

    statut = models.CharField(max_length=15, choices=STATUTS, default='en_cours')
    date_debut = models.DateTimeField(auto_now_add=True)
    date_fin = models.DateTimeField(null=True, blank=True)

    score_brut = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    score_pourcentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    reussi = models.BooleanField(null=True)

    class Meta:
        verbose_name = 'Examen généré (Banque)'
        verbose_name_plural = 'Examens générés (Banque)'
        indexes = [models.Index(fields=['utilisateur', 'statut'])]

    def __str__(self):
        return f"Examen {self.gabarit.nom} — {self.utilisateur.username}"

    @staticmethod
    def generer_pour(gabarit, utilisateur):
        """
        Point d'entrée UNIQUE de génération — tire aléatoirement les 
        questions selon la composition du gabarit, mélange l'ordre des 
        questions ET des réponses (demandé explicitement).
        """
        import random

        examen = ExamenGenere.objects.create(gabarit=gabarit, utilisateur=utilisateur)
        ordre_global = 0

        for ligne in gabarit.composition.all():
            queryset = QuestionBanque.objects.filter(module=ligne.module, statut='active')
            if ligne.niveau:
                queryset = queryset.filter(niveau=ligne.niveau)

            questions_disponibles = list(queryset)
            random.shuffle(questions_disponibles)
            questions_choisies = questions_disponibles[:ligne.nombre_questions]

            for question in questions_choisies:
                ordre_global += 1
                # Mélange l'ordre des réponses pour cette instance précise
                reponses_melangees = list(question.reponses_possibles)
                random.shuffle(reponses_melangees)

                QuestionExamenGenere.objects.create(
                    examen=examen, question=question, ordre=ordre_global,
                    reponses_ordre_affiche=reponses_melangees,
                    points_attribues=ligne.points_par_question,
                )

        return examen

    # ==========================================================
    # ⬇️ MÉTHODE CORRIGER MODIFIÉE (déclenchement éligibilité)
    # ==========================================================
    def corriger(self):
        """Correction automatique — calcule score global + détail par module + compétences."""
        details = self.reponses_donnees.select_related('question__module', 'question__competence_evaluee')

        score_obtenu = 0
        score_max = 0
        resultats_par_module = {}
        competences_maitrisees = set()
        competences_a_renforcer = set()

        for detail in details:
            score_max += float(detail.points_attribues)
            module_nom = detail.question.module.nom
            resultats_par_module.setdefault(module_nom, {'obtenu': 0, 'max': 0})
            resultats_par_module[module_nom]['max'] += float(detail.points_attribues)

            if detail.est_correcte:
                score_obtenu += float(detail.points_attribues)
                resultats_par_module[module_nom]['obtenu'] += float(detail.points_attribues)
                if detail.question.competence_evaluee:
                    competences_maitrisees.add(detail.question.competence_evaluee)
            else:
                if detail.question.competence_evaluee:
                    competences_a_renforcer.add(detail.question.competence_evaluee)

        self.score_brut = score_obtenu
        self.score_pourcentage = round((score_obtenu / score_max) * 100, 2) if score_max else 0
        self.reussi = self.score_pourcentage >= self.gabarit.seuil_reussite
        self.statut = 'termine'
        self.date_fin = timezone.now()
        self.save()

        # ================================================
        # NOUVEAU BLOC — Déclenchement de l'éligibilité à la certification
        # ================================================
        from academie.models import obtenir_cohorte_active_pour, EligibiliteCertification

        if self.gabarit.formation_liee:
            cohorte_active = obtenir_cohorte_active_pour(self.utilisateur, self.gabarit.formation_liee)
            if cohorte_active:
                eligibilite, _ = EligibiliteCertification.objects.get_or_create(
                    utilisateur=self.utilisateur,
                    formation=self.gabarit.formation_liee,
                    defaults={'cohorte': cohorte_active}
                )
                eligibilite.note_theorique = self.score_pourcentage
                eligibilite.calculer_moyenne_et_verifier_eligibilite()
        # ================================================

        return {
            'score_pourcentage': self.score_pourcentage,
            'reussi': self.reussi,
            'resultats_par_module': resultats_par_module,
            'competences_maitrisees': list(competences_maitrisees),
            'competences_a_renforcer': list(competences_a_renforcer - competences_maitrisees),
        }


class QuestionExamenGenere(models.Model):
    """Table pivot — LA question précise dans CET examen précis, avec son ordre d'affichage figé."""

    examen = models.ForeignKey(ExamenGenere, on_delete=models.CASCADE, related_name='questions_ordonnees')
    question = models.ForeignKey(QuestionBanque, on_delete=models.CASCADE)
    ordre = models.IntegerField()
    reponses_ordre_affiche = models.JSONField(default=list, help_text="Snapshot des réponses mélangées pour CET étudiant")
    points_attribues = models.DecimalField(max_digits=5, decimal_places=2, default=1.0)

    class Meta:
        ordering = ['ordre']
        unique_together = ['examen', 'question']


class ReponseEtudiantBanque(models.Model):
    """La réponse effective donnée par l'étudiant à une question précise."""

    examen = models.ForeignKey(ExamenGenere, on_delete=models.CASCADE, related_name='reponses_donnees')
    question = models.ForeignKey(QuestionBanque, on_delete=models.CASCADE)
    points_attribues = models.DecimalField(max_digits=5, decimal_places=2, default=1.0)

    reponse_donnee = models.JSONField(default=dict, help_text="Format libre selon type_question")
    est_correcte = models.BooleanField(default=False)
    temps_pris_secondes = models.IntegerField(default=0)

    class Meta:
        unique_together = ['examen', 'question']
        verbose_name = 'Réponse étudiant (Banque)'
        verbose_name_plural = 'Réponses étudiants (Banque)'

    def evaluer(self):
        """Corrige automatiquement selon type_question — logique centralisée."""
        q = self.question
        if q.type_question == 'qcm':
            bonne_reponse = next((r['texte'] for r in q.reponses_possibles if r.get('correct')), None)
            self.est_correcte = (self.reponse_donnee.get('choix') == bonne_reponse)
        elif q.type_question == 'vrai_faux':
            bonne_reponse = next((r['texte'] for r in q.reponses_possibles if r.get('correct')), None)
            self.est_correcte = (self.reponse_donnee.get('choix') == bonne_reponse)
        elif q.type_question == 'choix_multiples':
            bonnes = set(r['texte'] for r in q.reponses_possibles if r.get('correct'))
            donnees = set(self.reponse_donnee.get('choix', []))
            # 🔁 Correction : vérifie que l'ensemble n'est pas vide
            self.est_correcte = (bonnes == donnees) and len(bonnes) > 0
        elif q.type_question == 'reponse_courte':
            reponses_acceptees = [r.strip().lower() for r in q.reponse_texte_courte.split('|')]
            self.est_correcte = self.reponse_donnee.get('texte', '').strip().lower() in reponses_acceptees
        else:
            # Types nécessitant correction manuelle (étude de cas, analyse image, etc.)
            self.est_correcte = self.reponse_donnee.get('correction_manuelle', False)
        self.save()
        return self.est_correcte



# ================================================
# 4. STATISTIQUES — Analyse de la banque
# ================================================
class StatistiqueQuestion(models.Model):
    """Agrégats de performance par question — recalculés périodiquement."""

    question = models.OneToOneField(QuestionBanque, on_delete=models.CASCADE, related_name='statistiques')
    nb_utilisations = models.IntegerField(default=0)
    nb_reussites = models.IntegerField(default=0)
    temps_moyen_secondes = models.FloatField(default=0)
    derniere_maj = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Statistique de question'
        verbose_name_plural = 'Statistiques de questions'

    def taux_reussite(self):
        return round((self.nb_reussites / self.nb_utilisations) * 100, 1) if self.nb_utilisations else 0

    def necessite_revision(self):
        """Question suspecte : très facile (>95%) ou très difficile (<15%) — signal de mauvaise question."""
        taux = self.taux_reussite()
        return self.nb_utilisations >= 10 and (taux > 95 or taux < 15)