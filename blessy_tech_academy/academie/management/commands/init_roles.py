"""
Commande Django pour initialiser les groupes et permissions RBAC.
Usage : python manage.py init_roles
"""

from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Initialise les groupes RBAC et leurs permissions"

    def handle(self, *args, **options):
        self.stdout.write("🔐 Initialisation des rôles RBAC...")

        # ================================================
        # Définition des rôles et permissions associées
        # ================================================
        ROLES = {
            "SuperAdmin": {
                "label": "Super Administrateur",
                "permissions": "__all__",  # Toutes les permissions
            },
            "Admin": {
                "label": "Administrateur",
                "permissions": [
                    "view_user",
                    "change_user",
                    "add_user",
                    "view_formation",
                    "change_formation",
                    "add_formation",
                    "view_inscription",
                    "view_quiz",
                    "change_quiz",
                ],
            },
            "Direction": {
                "label": "Direction",
                "permissions": [
                    "view_formation",
                    "view_inscription",
                    "view_statistiques",
                ],
            },
            "RespAcademique": {
                "label": "Responsable Académique",
                "permissions": [
                    "view_formation",
                    "change_formation",
                    "add_formation",
                    "view_module",
                    "change_module",
                    "add_module",
                    "view_lecon",
                    "change_lecon",
                    "add_lecon",
                    "view_quiz",
                    "change_quiz",
                    "add_quiz",
                ],
            },
            "Formateur": {
                "label": "Formateur",
                "permissions": [
                    "view_formation",
                    "view_module",
                    "change_module",
                    "view_lecon",
                    "change_lecon",
                    "view_quiz",
                ],
            },
            "AsstFormateur": {
                "label": "Assistant Formateur",
                "permissions": [
                    "view_formation",
                    "view_module",
                    "view_lecon",
                ],
            },
            "Support": {
                "label": "Support",
                "permissions": [
                    "view_user",
                    "view_inscription",
                    "view_formation",
                ],
            },
            "Marketing": {
                "label": "Marketing",
                "permissions": [
                    "view_article",
                    "change_article",
                    "add_article",
                    "view_inscription",
                ],
            },
            "Finance": {
                "label": "Finance",
                "permissions": [
                    "view_inscription",
                ],
            },
            "Examinateur": {
                "label": "Examinateur",
                "permissions": [
                    "view_quiz",
                    "change_quiz",
                    "add_quiz",
                    "view_resultatquiz",
                ],
            },
            "Correcteur": {
                "label": "Correcteur",
                "permissions": [
                    "view_quiz",
                    "view_resultatquiz",
                ],
            },
        }

        # ================================================
        # Création des groupes
        # ================================================
        for group_name, config in ROLES.items():
            group, created = Group.objects.get_or_create(name=group_name)
            if created:
                self.stdout.write(f"  ✅ Groupe créé : {config['label']} ({group_name})")
            else:
                self.stdout.write(f"  ⏭️  Groupe existant : {config['label']} ({group_name})")

            # Attribution des permissions
            if config["permissions"] == "__all__":
                # SuperAdmin reçoit toutes les permissions
                all_permissions = Permission.objects.all()
                group.permissions.set(all_permissions)
                self.stdout.write(
                    f"     → {all_permissions.count()} permissions attribuées (toutes)"
                )
            else:
                # Attribution sélective
                count = 0
                for perm_codename in config["permissions"]:
                    try:
                        permission = Permission.objects.get(codename=perm_codename)
                        group.permissions.add(permission)
                        count += 1
                    except Permission.DoesNotExist:
                        self.stdout.write(
                            self.style.WARNING(f"     ⚠️  Permission introuvable : {perm_codename}")
                        )
                self.stdout.write(f"     → {count} permissions attribuées")

        self.stdout.write(self.style.SUCCESS("\n✅ Initialisation RBAC terminée."))
