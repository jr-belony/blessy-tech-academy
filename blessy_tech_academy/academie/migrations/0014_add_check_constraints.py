from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('academie', '0013_examen_academie_ex_formati_6b4fd4_idx_and_more'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='coupon',
            constraint=models.CheckConstraint(
                condition=models.Q(date_fin__isnull=True) | models.Q(date_fin__gte=models.F('date_debut')),
                name='coupon_date_fin_apres_debut'
            ),
        ),
        migrations.AddConstraint(
            model_name='coupon',
            constraint=models.CheckConstraint(
                condition=models.Q(valeur__gt=0),
                name='coupon_valeur_positive'
            ),
        ),
        migrations.AddConstraint(
            model_name='promotion',
            constraint=models.CheckConstraint(
                condition=models.Q(date_fin__gte=models.F('date_debut')),
                name='promotion_date_fin_apres_debut'
            ),
        ),
        migrations.AddConstraint(
            model_name='orderitem',
            constraint=models.CheckConstraint(
                condition=(
                    models.Q(type_produit='formation', formation__isnull=False, parcours__isnull=True) |
                    models.Q(type_produit='parcours', parcours__isnull=False, formation__isnull=True)
                ),
                name='orderitem_type_produit_coherent'
            ),
        ),
    ]