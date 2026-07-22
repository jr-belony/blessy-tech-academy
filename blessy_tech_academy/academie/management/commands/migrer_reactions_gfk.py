# ================================================
# MIGRER_REACTIONS_GFK.PY — Migration données Reaction (testée, réversible)
# Usage : python manage.py migrer_reactions_gfk
# Ne supprime RIEN — remplit juste content_type/object_id depuis 
# les anciens champs sujet/reponse existants
# ================================================

from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType
from academie.models import Reaction, Sujet, Reponse


class Command(BaseCommand):
    help = "Backfill GenericForeignKey depuis les anciens champs sujet/reponse de Reaction"

    def handle(self, *args, **options):
        ct_sujet = ContentType.objects.get_for_model(Sujet)
        ct_reponse = ContentType.objects.get_for_model(Reponse)

        migres_sujet = 0
        migres_reponse = 0
        erreurs = 0

        for reaction in Reaction.objects.filter(content_type__isnull=True):
            try:
                if reaction.sujet_id:
                    reaction.content_type = ct_sujet
                    reaction.object_id = reaction.sujet_id
                    reaction.save(update_fields=['content_type', 'object_id'])
                    migres_sujet += 1
                elif reaction.reponse_id:
                    reaction.content_type = ct_reponse
                    reaction.object_id = reaction.reponse_id
                    reaction.save(update_fields=['content_type', 'object_id'])
                    migres_reponse += 1
            except Exception as e:
                erreurs += 1
                self.stdout.write(self.style.WARNING(f"⚠️ Erreur reaction #{reaction.id} : {e}"))

        self.stdout.write(self.style.SUCCESS(
            f"✅ Migration terminée : {migres_sujet} réactions Sujet, "
            f"{migres_reponse} réactions Réponse, {erreurs} erreur(s)"
        ))
        self.stdout.write("⚠️ Les anciens champs sujet/reponse sont conservés — à retirer manuellement après validation.")