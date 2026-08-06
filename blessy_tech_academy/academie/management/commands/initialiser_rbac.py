# academie/management/commands/initialiser_rbac.py

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from academie.models import Formation, Certificat


class Command(BaseCommand):
    help = "Initialise les groupes et permissions RBAC pour Blessy Tech Academy"

    def handle(self, *args, **options):
        self.stdout.write("🚀 Initialisation des groupes et permissions...\n")

        # --- 1. Récupération des ContentTypes ---
        formation_ct = ContentType.objects.get_for_model(Formation)
        certificat_ct = ContentType.objects.get_for_model(Certificat)

        # --- 2. Création des groupes ---
        groupes = {
            'Étudiant': 'Rôle par défaut pour les apprenants',
            'Formateur': 'Peut gérer le contenu des formations et évaluer',
            'Administrateur': 'Accès complet',
            'Support': 'Gestion des tickets et modération forum',
            'Finance': 'Accès aux données de facturation',
            'Direction': 'Accès aux statistiques et tableaux de bord',
        }

        group_objects = {}
        for nom, description in groupes.items():
            group, created = Group.objects.get_or_create(name=nom)
            group_objects[nom] = group
            if created:
                self.stdout.write(self.style.SUCCESS(f"✅ Groupe créé : {nom}"))
            else:
                self.stdout.write(f"🔄 Groupe existant : {nom}")

        # --- 3. Définition des permissions par groupe ---
        permissions_mapping = {
            # Permissions sur Formation (personnalisées)
            'view_formation_detail': ['Étudiant', 'Formateur', 'Administrateur', 'Support', 'Direction'],
            'edit_formation': ['Formateur', 'Administrateur'],
            'can_delete_formation': ['Administrateur'],
            'publish_formation': ['Administrateur'],
            'manage_formation_content': ['Formateur', 'Administrateur'],
            'view_formation_stats': ['Formateur', 'Administrateur', 'Direction'],

            # Permissions sur Certificat (système + personnalisées)
            'view_certificat': ['Étudiant', 'Formateur', 'Administrateur', 'Support', 'Direction'],
            'can_generate_certificat': ['Formateur', 'Administrateur'],
            'can_revoke_certificat': ['Administrateur'],
        }

        # --- 4. Assignation des permissions ---
        for codename, groupes_noms in permissions_mapping.items():
            try:
                # Trouver la permission (soit sur Formation, soit sur Certificat)
                if codename.startswith('view_formation') or codename in ['edit_formation', 'can_delete_formation',
                                                                          'publish_formation', 'manage_formation_content',
                                                                          'view_formation_stats']:
                    perm = Permission.objects.get(content_type=formation_ct, codename=codename)
                else:
                    perm = Permission.objects.get(content_type=certificat_ct, codename=codename)

                for nom_groupe in groupes_noms:
                    group = group_objects.get(nom_groupe)
                    if group:
                        group.permissions.add(perm)

                self.stdout.write(self.style.SUCCESS(f"✅ Permission '{codename}' assignée à : {', '.join(groupes_noms)}"))

            except Permission.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"⚠️ Permission '{codename}' non trouvée — vérifie le nom."))

        # --- 5. Ajout des permissions Django natives (ajout, modification, suppression) ---
        # Pour les administrateurs
        admin_group = group_objects['Administrateur']
        all_perms = Permission.objects.filter(
            content_type__in=[formation_ct, certificat_ct]
        )
        admin_group.permissions.add(*all_perms)
        self.stdout.write(self.style.SUCCESS(f"✅ Toutes les permissions accordées au groupe 'Administrateur'"))

        # --- 6. Message final ---
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS("🎉 RBAC initialisé avec succès !"))
        self.stdout.write(self.style.SUCCESS(f"Groupes : {', '.join(group_objects.keys())}"))
        self.stdout.write("=" * 60)