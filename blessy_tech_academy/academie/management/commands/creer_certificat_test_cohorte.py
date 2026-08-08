# ================================================
# CREER_CERTIFICAT_TEST_COHORTE.PY — Génère un certificat de test complet
# Usage : python manage.py creer_certificat_test_cohorte
# ================================================

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from academie.models import Certificat, Formation
from django.core.files.base import ContentFile
from academie.services.certificat_pdf import generer_pdf_certificat_officiel


class Command(BaseCommand):
    help = "Génère un certificat de test complet pour vérifier le rendu HTML/PDF"

    def handle(self, *args, **options):
        # ------------------------------------------------------------
        # 1. Création de l'utilisateur test
        # ------------------------------------------------------------
        utilisateur, created = User.objects.get_or_create(
            username='test_certificat_cohorte',
            defaults={
                'first_name': 'Prénom',
                'last_name': 'Nom',
                'email': 'test@blessytechacademy.com'
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"✅ Utilisateur test créé : {utilisateur.username}"))
        else:
            self.stdout.write(f"ℹ️ Utilisateur test existant : {utilisateur.username}")

        # ------------------------------------------------------------
        # 2. Récupération des formations de la cohorte (noms EXACTS)
        # ------------------------------------------------------------
        formations_cohorte = Formation.objects.filter(
            nom__in=[
                'Bureautique Professionnelle',
                'Intelligence Artificielle',
                'Internet, Recherche et Productivité',
                'Microsoft Excel pour la Gestion de Stock',
            ]
        )

        if formations_cohorte.count() < 4:
            self.stdout.write(self.style.WARNING(
                f"⚠️ Seulement {formations_cohorte.count()}/4 formations trouvées — "
                f"vérifie les noms EXACTS dans /admin/academie/formation/"
            ))
        else:
            self.stdout.write(self.style.SUCCESS(f"✅ {formations_cohorte.count()} formations trouvées"))

        formation_principale = formations_cohorte.first()
        if not formation_principale:
            self.stdout.write(self.style.ERROR("❌ Aucune formation trouvée – arrêt."))
            return

        # ------------------------------------------------------------
        # 3. Récupération ou création du certificat (mise à jour si existant)
        # ------------------------------------------------------------
        certificat, created = Certificat.objects.get_or_create(
            utilisateur=utilisateur,
            formation=formation_principale,
            defaults={
                'resultat_final': 87,
                'libelle_programme': 'Compétences Numériques Professionnelles',
                'mention': 'Très Bien',
            }
        )

        if not created:
            # Mise à jour des champs si le certificat existe déjà
            certificat.resultat_final = 87
            certificat.libelle_programme = 'Compétences Numériques Professionnelles'
            certificat.mention = 'Très Bien'
            self.stdout.write(self.style.WARNING("⚠️ Certificat existant mis à jour."))
        else:
            self.stdout.write(self.style.SUCCESS("✅ Nouveau certificat créé."))

        # Lier les formations incluses (écrase l'ancienne liste)
        certificat.formations_incluses.set(formations_cohorte)
        certificat.save()

        # ------------------------------------------------------------
        # 4. Génération du PDF (synchrone)
        # ------------------------------------------------------------
        pdf_bytes = generer_pdf_certificat_officiel(certificat)
        if pdf_bytes:
            certificat.fichier_pdf.save(
                f"certificat_{certificat.numero}.pdf",
                ContentFile(pdf_bytes),
                save=True
            )
            self.stdout.write(self.style.SUCCESS("✅ PDF généré avec succès"))
            pdf_url = certificat.fichier_pdf.url
        else:
            pdf_url = 'en cours de génération... (vérifie les logs)'

        # ------------------------------------------------------------
        # 5. Affichage des résultats
        # ------------------------------------------------------------
        self.stdout.write(self.style.SUCCESS(
            f"✅ Certificat test disponible : {certificat.numero}\n"
            f"📄 PDF : {pdf_url}\n"
            f"🔍 Vérification publique : /certificat/{certificat.uuid}/\n"
            f"👤 Utilisateur : {utilisateur.username} (mot de passe : 'test123' si créé)"
        ))