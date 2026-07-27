// ================================================
// GENERER_ECOLE.JS — Bouton "Générer description + formations avec IA"
// ================================================

document.addEventListener('DOMContentLoaded', function() {
    const nomField = document.getElementById('id_nom');
    const descField = document.getElementById('id_description');
    if (!nomField) return;

    const bouton = document.createElement('button');
    bouton.type = 'button';
    bouton.textContent = '🏫 Générer description avec IA';
    bouton.style.cssText = 'background:linear-gradient(135deg,#00B4D8,#0090b8); color:white; border:none; padding:10px 20px; border-radius:8px; font-weight:700; cursor:pointer; margin:12px 0;';

    bouton.addEventListener('click', async function() {
        const nomEcole = nomField.value;
        if (!nomEcole) {
            alert('⚠️ Renseigne d\'abord le nom de l\'école.');
            return;
        }

        const domaine = prompt('Domaine de cette école (optionnel) :', '') || '';

        bouton.textContent = '⏳ Génération...';
        bouton.disabled = true;

        const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;

        try {
            const reponse = await fetch('/api/generer-ecole/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
                body: JSON.stringify({ nom_ecole: nomEcole, domaine: domaine })
            });
            const data = await reponse.json();

            if (data.succes) {
                if (descField) descField.value = data.donnees.description;

                const iconeField = document.getElementById('id_icone');
                if (iconeField && data.donnees.icone_suggeree) iconeField.value = data.donnees.icone_suggeree;

                let messageFormations = '💡 Formations suggérées à créer ensuite :\n';
                (data.donnees.formations_suggerees || []).forEach(f => {
                    messageFormations += `\n• ${f.nom} (${f.niveau}, ${f.duree_mois} mois)`;
                });
                alert('✅ Description générée !\n\n' + messageFormations);
            } else {
                alert('❌ ' + (data.erreur || 'Erreur inconnue'));
            }
        } catch (e) {
            alert('❌ Erreur réseau : ' + e.message);
        }

        bouton.textContent = '🏫 Générer description avec IA';
        bouton.disabled = false;
    });

    nomField.closest('.form-row, .field-nom').after(bouton);
});