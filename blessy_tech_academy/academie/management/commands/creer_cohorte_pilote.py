# academie/management/commands/creer_cohorte_pilote.py
# ================================================
# CREER_COHORTE_PILOTE.PY — Initialise la cohorte réelle du projet
# Usage : python manage.py creer_cohorte_pilote
# Adapte les usernames des 8 participants réels avant exécution
# ================================================

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from datetime import date
from academie.models import Cohorte, Formation


class Command(BaseCommand):
    help = "Crée la cohorte pilote réelle (8 personnes, 4 formations)"

    def handle(self, *args, **options):
        formations_noms = [
            'Bureautique Professionnelle',
            'Internet, Recherche et Productivité',
            'Intelligence Artificielle',
            'Gestion de Stock avec Excel',
        ]

        formations = Formation.objects.filter(nom__in=formations_noms)
        self.stdout.write(f"📚 {formations.count()}/4 formation(s) trouvée(s) : {[f.nom for f in formations]}")

        cohorte, cree = Cohorte.objects.get_or_create(
            nom='Cohorte Pilote 2026',
            defaults={'date_debut': date.today(), 'date_fin_prevue': date(2026, 12, 31)}
        )
        cohorte.formations.set(formations)

        self.stdout.write(self.style.SUCCESS(
            f"✅ Cohorte '{cohorte.nom}' {'créée' if cree else 'existante'}\n"
            f"⚠️ Ajoute maintenant les 8 membres manuellement via l'admin "
            f"(/admin/academie/cohorte/{cohorte.id}/change/) ou via :\n"
            f"   python manage.py shell -c \"from academie.models import Cohorte; "
            f"from django.contrib.auth.models import User; "
            f"c = Cohorte.objects.get(nom='Cohorte Pilote 2026'); "
            f"c.membres.add(*User.objects.filter(username__in=['user1','user2',...]))\""
        ))