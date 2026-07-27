# ================================================
# CRM/MODELS.PY — Inscription + InteractionCRM
# app_label='academie' → tables existantes academie_* 
# ================================================
from django.db import models


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
        app_label = 'academie'
        db_table = 'academie_inscription'   # ← corrigé (était exdb_table)

    def __str__(self):
        return f"{self.prenom} {self.nom} — {self.get_sujet_display()}"


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
        app_label = 'academie'
        db_table = 'academie_interactioncrm'   # ← ajouté

    def __str__(self):
        return f"{self.get_type_interaction_display()} — {self.inscription}"