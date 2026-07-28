from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('academie', '0008_gradebook_entry'),
    ]

    operations = [
        migrations.CreateModel(
            name='DisponibiliteMentor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('heure_debut', models.TimeField()),
                ('heure_fin', models.TimeField()),
                ('actif', models.BooleanField(default=True)),
                ('formateur', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='disponibilites_mentorat', to='auth.user')),
            ],
            options={
                'verbose_name': 'Disponibilité mentor',
                'verbose_name_plural': 'Disponibilités mentors',
                'ordering': ['date', 'heure_debut'],
            },
        ),
        migrations.CreateModel(
            name='ReservationMentorat',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('statut', models.CharField(choices=[('en_attente', 'En attente'), ('confirmee', 'Confirmée'), ('annulee', 'Annulée'), ('terminee', 'Terminée')], default='en_attente', max_length=20)),
                ('sujet', models.CharField(max_length=200)),
                ('notes', models.TextField(blank=True)),
                ('date_reservation', models.DateTimeField(auto_now_add=True)),
                ('disponibilite', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reservations', to='academie.disponibiliteMentor')),
                ('etudiant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reservations_mentorat', to='auth.user')),
            ],
            options={
                'verbose_name': 'Réservation mentorat',
                'verbose_name_plural': 'Réservations mentorat',
                'ordering': ['-date_reservation'],
            },
        ),
    ]