from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('academie', '0009_mentorat'),
    ]

    operations = [
        migrations.AlterField(
            model_name='moyenpaiement',
            name='icone',
            field=models.CharField(default='💳', max_length=10),
        ),
        migrations.AlterField(
            model_name='orderitem',
            name='icone_produit_snapshot',
            field=models.CharField(default='📚', max_length=10),
        ),
    ]