document.addEventListener('DOMContentLoaded', function () {

    // Trouve le champ "titre" du formulaire Quiz
    const champTitre = document.querySelector('#id_titre');
    if (!champTitre) return;

    // Crée le bouton "Générer questions avec l'IA"
    const bouton = document.createElement('button');
    bouton.type = 'button';
    bouton.textContent = '✨ Générer 5 questions avec Blessy AI';
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

    champTitre.parentNode.appendChild(bouton);

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
        const titre = champTitre.value.trim();

        if (!titre) {
            alert('Tape d\'abord le titre du quiz (ex: "Bases de Python").');
            return;
        }

        bouton.textContent = '⏳ Génération en cours (peut prendre 10-20s)...';
        bouton.disabled = true;

        try {
            const reponse = await fetch('/api/generer-quiz/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken'),
                },
                body: JSON.stringify({ sujet: titre, nombre: 5 })
            });

            const data = await reponse.json();

            if (data.erreur) {
                alert('Erreur : ' + data.erreur);
                bouton.textContent = '✨ Générer 5 questions avec Blessy AI';
                bouton.disabled = false;
                return;
            }

            // Remplit les lignes "Question" déjà présentes (inline formset)
            const questions = data.questions;
            const lignesQuestions = document.querySelectorAll('.dynamic-questions');

            questions.forEach((q, index) => {
                if (index >= lignesQuestions.length) return; // pas assez de lignes vides

                const ligne = lignesQuestions[index];

                const champOrdre = ligne.querySelector('input[name$="-ordre"]');
                const champTexte = ligne.querySelector('textarea[name$="-texte"], input[name$="-texte"]');
                const champA = ligne.querySelector('input[name$="-choix_a"]');
                const champB = ligne.querySelector('input[name$="-choix_b"]');
                const champC = ligne.querySelector('input[name$="-choix_c"]');
                const champD = ligne.querySelector('input[name$="-choix_d"]');
                const champBonne = ligne.querySelector('select[name$="-bonne_reponse"]');

                if (champOrdre) champOrdre.value = index + 1;
                if (champTexte) champTexte.value = q.texte;
                if (champA) champA.value = q.choix_a;
                if (champB) champB.value = q.choix_b;
                if (champC) champC.value = q.choix_c;
                if (champD) champD.value = q.choix_d;
                if (champBonne) champBonne.value = q.bonne_reponse;
            });

            alert(`✅ ${questions.length} questions générées ! Vérifie et ajuste si nécessaire, puis sauvegarde. Tu devras peut-être cliquer "Ajouter une autre Question" si toutes les lignes ne sont pas remplies.`);

        } catch (erreur) {
            alert('❌ Impossible de contacter le serveur.');
        }

        bouton.textContent = '✨ Générer 5 questions avec Blessy AI';
        bouton.disabled = false;
    });
});