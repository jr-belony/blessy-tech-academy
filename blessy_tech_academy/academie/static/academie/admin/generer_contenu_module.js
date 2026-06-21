document.addEventListener('DOMContentLoaded', function () {

    // Actif uniquement sur la page de modification d'un Module existant
    const correspondance = window.location.pathname.match(/\/admin\/academie\/module\/(\d+)\/change\//);
    if (!correspondance) return;

    const moduleId = correspondance[1];

    const premierFieldset = document.querySelector('fieldset, .module');
    if (!premierFieldset) return;

    const bouton = document.createElement('button');
    bouton.type = 'button';
    bouton.textContent = '🎓 Générer le contenu de TOUTES les leçons de ce module';
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
            "⚠️ Ceci va générer le contenu COMPLET de toutes les leçons " +
            "de ce module (peut prendre 1-3 minutes selon le nombre de leçons). " +
            "Le contenu existant sera remplacé. Continuer ?"
        );
        if (!confirmation) return;

        bouton.textContent = '⏳ Génération en cours... (patiente, ne ferme pas cette page)';
        bouton.disabled = true;

        try {
            const reponse = await fetch('/api/generer-contenu-module/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken'),
                },
                body: JSON.stringify({ module_id: moduleId })
            });

            const data = await reponse.json();

            if (data.erreur) {
                alert('❌ Erreur : ' + data.erreur);
                bouton.textContent = '🎓 Générer le contenu de TOUTES les leçons de ce module';
                bouton.disabled = false;
                return;
            }

            alert(`✅ ${data.message}\n\nLa page va se recharger.`);
            window.location.reload();

        } catch (erreur) {
            alert('❌ Impossible de contacter le serveur.');
            bouton.textContent = '🎓 Générer le contenu de TOUTES les leçons de ce module';
            bouton.disabled = false;
        }
    });
});