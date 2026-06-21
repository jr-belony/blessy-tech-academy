document.addEventListener('DOMContentLoaded', function () {

    // Ce script ne s'active que sur la page de MODIFICATION
    // d'une formation existante (pas sur "Ajouter")
    const urlActuelle = window.location.pathname;
    const correspondance = urlActuelle.match(/\/admin\/academie\/formation\/(\d+)\/change\//);

    if (!correspondance) return; // pas sur une page de modification de formation

    const formationId = correspondance[1];

    // Trouve un bon endroit pour insérer le bouton (avant les fieldsets)
    const conteneurForm = document.querySelector('#formation_form, form');
    if (!conteneurForm) return;

    const premierFieldset = document.querySelector('.module, fieldset');
    if (!premierFieldset) return;

    // Crée le bouton
    const bouton = document.createElement('button');
    bouton.type = 'button';
    bouton.textContent = '🎓 Générer le programme complet avec Blessy AI';
    bouton.style.cssText = `
        background: linear-gradient(135deg, #0B2447, #00B4D8);
        color: white;
        border: none;
        padding: 12px 24px;
        border-radius: 8px;
        cursor: pointer;
        margin: 16px 0;
        font-weight: 700;
        font-size: 14px;
        display: block;
        width: 100%;
    `;

    premierFieldset.parentNode.insertBefore(bouton, premierFieldset);

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let cookie of cookies) {
                cookie = cookie.trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    bouton.addEventListener('click', async function () {

        const confirmation = confirm(
            "⚠️ Ceci va générer automatiquement 4-6 modules avec leurs leçons " +
            "pour cette formation, directement enregistrés en base de données.\n\n" +
            "Si des modules existent déjà, ils ne seront PAS supprimés " +
            "(les nouveaux s'ajouteront). Continuer ?"
        );

        if (!confirmation) return;

        bouton.textContent = '⏳ Génération en cours (peut prendre 20-40s)...';
        bouton.disabled = true;

        try {
            const reponse = await fetch('/api/generer-programme/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken'),
                },
                body: JSON.stringify({ formation_id: formationId })
            });

            const data = await reponse.json();

            if (data.erreur) {
                alert('❌ Erreur : ' + data.erreur);
                bouton.textContent = '🎓 Générer le programme complet avec Blessy AI';
                bouton.disabled = false;
                return;
            }

            alert(
                `✅ ${data.message}\n\n` +
                `La page va se recharger pour afficher les nouveaux modules.`
            );

            window.location.reload();

        } catch (erreur) {
            alert('❌ Impossible de contacter le serveur.');
            bouton.textContent = '🎓 Générer le programme complet avec Blessy AI';
            bouton.disabled = false;
        }
    });
});