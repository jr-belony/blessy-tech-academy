// ================================================
// GENERER_EXAMEN.JS — Bouton "Générer un examen complet avec IA"
// Injecté sur la page ADD de Examen dans l'admin
// ================================================

document.addEventListener('DOMContentLoaded', function() {
    const formationField = document.getElementById('id_formation');
    if (!formationField) return;

    const bouton = document.createElement('button');
    bouton.type = 'button';
    bouton.textContent = '🎯 Générer un examen complet avec IA';
    bouton.style.cssText = 'background:linear-gradient(135deg,#FF6B00,#e85a2a); color:white; border:none; padding:10px 20px; border-radius:8px; font-weight:700; cursor:pointer; margin:12px 0;';

    bouton.addEventListener('click', async function() {
        const formationId = formationField.value;
        if (!formationId) {
            alert('⚠️ Sélectionne d\'abord une formation.');
            return;
        }

        const niveau = prompt('Niveau de l\'examen (debutant/intermediaire/avance) :', 'intermediaire') || 'intermediaire';
        const nbQuestions = prompt('Nombre de questions :', '10') || '10';

        bouton.textContent = '⏳ Génération en cours...';
        bouton.disabled = true;

        const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;

        try {
            const reponse = await fetch('/api/generer-examen/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
                body: JSON.stringify({ formation_id: formationId, niveau: niveau, nombre_questions: parseInt(nbQuestions) })
            });
            const data = await reponse.json();

            if (data.succes) {
                alert(`✅ Examen créé avec ${data.nombre_questions} questions !`);
                window.location.href = `/admin/academie/examen/${data.examen_id}/change/`;
            } else {
                alert('❌ ' + (data.erreur || 'Erreur inconnue'));
                bouton.textContent = '🎯 Générer un examen complet avec IA';
                bouton.disabled = false;
            }
        } catch (e) {
            alert('❌ Erreur réseau : ' + e.message);
            bouton.textContent = '🎯 Générer un examen complet avec IA';
            bouton.disabled = false;
        }
    });

    formationField.closest('.form-row, .field-formation').after(bouton);
});