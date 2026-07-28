from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('academie', '0005_move_content_models'),  # ou votre dernière migration stable
    ]

    operations = [
        migrations.CreateModel(
            name='NoteLecon',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('contenu', models.TextField()),
                ('date_creation', models.DateTimeField(auto_now_add=True)),
                ('date_modification', models.DateTimeField(auto_now=True)),
                ('lecon', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notes_etudiants', to='academie.lecon')),
                ('utilisateur', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notes_lecons', to='auth.user')),
            ],
            options={
                'verbose_name': 'Note de leçon',
                'verbose_name_plural': 'Notes de leçons',
                'ordering': ['-date_modification'],
            },
        ),
    ]