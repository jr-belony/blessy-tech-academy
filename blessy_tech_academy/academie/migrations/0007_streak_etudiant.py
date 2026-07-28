from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('academie', '0006_note_lecon'),  # ← adaptez selon votre dernière migration
    ]

    operations = [
        migrations.CreateModel(
            name='StreakEtudiant',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('jours_consecutifs', models.IntegerField(default=0)),
                ('record_jours_consecutifs', models.IntegerField(default=0)),
                ('derniere_activite', models.DateField(blank=True, null=True)),
                ('utilisateur', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='streak', to='auth.user')),
            ],
            options={
                'verbose_name': 'Série étudiant',
                'verbose_name_plural': 'Séries étudiants',
            },
        ),
    ]