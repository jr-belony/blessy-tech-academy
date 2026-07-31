from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('academie', '0029_competences_developpees_state'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            CREATE TABLE IF NOT EXISTS academie_projetetudiant_competences_demontrees (
                id bigserial NOT NULL PRIMARY KEY,
                projetetudiant_id integer NOT NULL REFERENCES academie_projetetudiant(id) DEFERRABLE INITIALLY DEFERRED,
                competence_id integer NOT NULL REFERENCES academie_competence(id) DEFERRABLE INITIALLY DEFERRED
            );
            CREATE INDEX IF NOT EXISTS academie_projetetudiant_competences_demontrees_projetetudiant_id_idx
                ON academie_projetetudiant_competences_demontrees (projetetudiant_id);
            CREATE INDEX IF NOT EXISTS academie_projetetudiant_competences_demontrees_competence_id_idx
                ON academie_projetetudiant_competences_demontrees (competence_id);
            """,
            reverse_sql="DROP TABLE IF EXISTS academie_projetetudiant_competences_demontrees;"
        ),
    ]