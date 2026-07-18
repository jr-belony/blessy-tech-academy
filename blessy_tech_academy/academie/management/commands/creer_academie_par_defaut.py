# ================================================
# CREER_ACADEMIE_PAR_DEFAUT.PY — Migration zéro-casse
# Crée "Blessy Tech Academy" et y rattache TOUT l'existant automatiquement
# Usage : python manage.py creer_academie_par_defaut
# ================================================

from django.core.management.base import BaseCommand

from academie.models import Academie, Article, Ecole, ProfilUtilisateur


class Command(BaseCommand):
    help = "Crée l'Academie par défaut et rattache toutes les écoles/utilisateurs/articles existants"

    def handle(self, *args, **options):
        academie_defaut, cree = Academie.objects.get_or_create(
            nom='Blessy Tech Academy',
            defaults={
                'sous_titre': "L'école de la haute technologie moderne d'Haïti",
                'icone': '🎓',
                'couleur_principale': '#0B2447',
                'couleur_accent': '#00B4D8',
                'est_academie_par_defaut': True,
                'actif': True,
            }
        )

        # Rattache toutes les Ecoles sans academie à l'Academie par défaut
        ecoles_orphelines = Ecole.objects.filter(academie__isnull=True)
        nb_ecoles = ecoles_orphelines.update(academie=academie_defaut)

        # Rattache tous les utilisateurs à l'Academie par défaut
        nb_utilisateurs = 0
        for profil in ProfilUtilisateur.objects.all():
            if not profil.academies.exists():
                profil.academies.add(academie_defaut)
                nb_utilisateurs += 1

        # === Backfill des Articles ===
        articles_orphelins = Article.objects.filter(academie__isnull=True)
        nb_articles = articles_orphelins.update(academie=academie_defaut)

        self.stdout.write(self.style.SUCCESS(
            f"✅ Academie '{academie_defaut.nom}' {'créée' if cree else 'déjà existante'}\n"
            f"   • {nb_ecoles} école(s) rattachée(s)\n"
            f"   • {nb_utilisateurs} utilisateur(s) rattaché(s)\n"
            f"   • {nb_articles} article(s) rattaché(s)"
        ))