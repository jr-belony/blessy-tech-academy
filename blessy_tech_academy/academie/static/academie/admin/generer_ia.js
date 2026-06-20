document.addEventListener('DOMContentLoaded', function () {

    // Trouve le champ "nom" du formulaire Formation
    const champNom = document.querySelector('#id_nom');
    if (!champNom) return; // si on n'est pas sur le formulaire Formation, on arrête

    const champEcole = document.querySelector('#id_ecole');
    const champDescription = document.querySelector('#id_description');
    const champDebouches = document.querySelector('#id_debouches');
    const champPrerequis = document.querySelector('#id_prerequis');
    const champCertifications = document.querySelector('#id_certifications');

    // Crée le bouton "Générer avec l'IA"
    const bouton = document.createElement('button');
    bouton.type = 'button';
    bouton.textContent = '✨ Générer avec Blessy AI';
    bouton.style.cssText = `
        background: #00B4D8;
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: 6px;
        cursor: pointer;
        margin-top: 8px;
        margin-bottom: 16px;
        font-weight: 600;
        font-size: 13px;
    `;

    // Insère le bouton juste après le champ "nom"
    champNom.parentNode.appendChild(bouton);

    // Récupère le cookie CSRF (nécessaire pour les requêtes POST Django)
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
        const nom = champNom.value.trim();

        if (!nom) {
            alert('Tape d\'abord le nom de la formation.');
            return;
        }

        // Récupère le texte de l'école sélectionnée
        let ecoleTexte = '';
        if (champEcole && champEcole.selectedIndex >= 0) {
            ecoleTexte = champEcole.options[champEcole.selectedIndex].text;
        }

        bouton.textContent = '⏳ Génération en cours...';
        bouton.disabled = true;

        try {
            const reponse = await fetch('/api/generer-formation/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken'),
                },
                body: JSON.stringify({ nom: nom, ecole: ecoleTexte })
            });

            const data = await reponse.json();

            if (data.erreur) {
                alert('Erreur : ' + data.erreur);
            } else {
                if (champDescription) champDescription.value = data.description || '';
                if (champDebouches) champDebouches.value = data.debouches || '';
                if (champPrerequis) champPrerequis.value = data.prerequis || '';
                if (champCertifications) champCertifications.value = data.certifications || '';
                alert('✅ Contenu généré ! Vérifie et ajuste si nécessaire avant de sauvegarder.');
            }

        } catch (erreur) {
            alert('❌ Impossible de contacter le serveur.');
        }

        bouton.textContent = '✨ Générer avec Blessy AI';
        bouton.disabled = false;
    });
});