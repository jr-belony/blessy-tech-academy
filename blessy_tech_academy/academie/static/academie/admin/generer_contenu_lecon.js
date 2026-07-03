document.addEventListener('DOMContentLoaded', function () {
    const correspondance = window.location.pathname.match(/\/admin\/academie\/lecon\/(\d+)\/change\//);
    if (!correspondance) return;

    const leconId = correspondance[1];
    const champContenu = document.querySelector('#id_contenu');
    if (!champContenu) return;

    const bouton = document.createElement('button');
    bouton.type = 'button';
    bouton.textContent = '✨ Générer le contenu avec Blessy AI';
    bouton.style.cssText = `
        background: linear-gradient(135deg, #0B2447, #00B4D8);
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 8px;
        cursor: pointer;
        margin-bottom: 12px;
        font-weight: 700;
        font-size: 13px;
        display: block;
    `;

    champContenu.parentNode.insertBefore(bouton, champContenu);

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
        bouton.textContent = '⏳ Génération en cours...';
        bouton.disabled = true;

        try {
            const reponse = await fetch('/api/generer-contenu-lecon/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken'),
                },
                body: JSON.stringify({ lecon_id: parseInt(leconId) })
            });

            const data = await reponse.json();

            if (data.succes) {
                // Textarea source (pour la sauvegarde Django)
                champContenu.value = data.contenu;

                // Éditeur visuel CKEditor 5
                const editorVisual = document.querySelector('.ck-editor__editable');
                if (editorVisual) {
                    editorVisual.innerHTML = data.contenu;
                }

                alert('✅ Contenu généré ! Sauvegarde pour conserver.');
            } else {
                alert('❌ Erreur : ' + (data.erreur || 'Inconnue'));
            }
        } catch (erreur) {
            alert('❌ Impossible de contacter le serveur.');
        }

        bouton.textContent = '✨ Générer le contenu avec Blessy AI';
        bouton.disabled = false;
    });
});