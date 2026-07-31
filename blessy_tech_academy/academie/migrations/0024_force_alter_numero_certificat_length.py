from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('academie', '0023_remove_orderitem_orderitem_produit_coherent_and_more'),
    ]

    operations = [
        migrations.RunSQL(
            sql='ALTER TABLE academie_certificat ALTER COLUMN numero TYPE varchar(50);',
            reverse_sql='ALTER TABLE academie_certificat ALTER COLUMN numero TYPE varchar(20);',
        ),
        migrations.AlterField(
            model_name='certificat',
            name='numero',
            field=models.CharField(db_index=True, max_length=50, unique=True, blank=True, editable=False),
        ),
    ]