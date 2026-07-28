from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('academie', '0007_streak_etudiant'),  # dépend de la dernière migration
    ]

    operations = [
        migrations.CreateModel(
            name='GradebookEntry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('note', models.DecimalField(decimal_places=2, help_text='Note sur 20', max_digits=5)),
                ('appreciation', models.TextField(blank=True, help_text='Commentaire qualitatif')),
                ('date_attribution', models.DateTimeField(auto_now_add=True)),
                ('etudiant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='grades', to='auth.user')),
                ('formateur', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='grades_attribuees', to='auth.user')),
                ('formation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='grades', to='academie.formation')),
            ],
            options={
                'verbose_name': 'Note Gradebook',
                'verbose_name_plural': 'Notes Gradebook',
                'ordering': ['-date_attribution'],
                'unique_together': {('formation', 'etudiant')},
            },
        ),
    ]