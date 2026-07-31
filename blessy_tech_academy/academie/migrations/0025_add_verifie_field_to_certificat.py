from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('academie', '0024_force_alter_numero_certificat_length'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="ALTER TABLE academie_certificat ADD COLUMN IF NOT EXISTS verifie boolean NOT NULL DEFAULT false;",
                    reverse_sql="ALTER TABLE academie_certificat DROP COLUMN IF EXISTS verifie;",
                ),
            ],
            state_operations=[
                migrations.AddField(
                    model_name='certificat',
                    name='verifie',
                    field=models.BooleanField(default=False),
                ),
            ],
        ),
    ]