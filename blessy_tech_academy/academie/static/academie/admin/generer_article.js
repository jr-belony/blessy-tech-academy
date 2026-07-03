document.addEventListener('DOMContentLoaded', function() {
    const titreField = document.querySelector('#id_titre');
    if (!titreField) return;

    const generateBtn = document.createElement('button');
    generateBtn.type = 'button';
    generateBtn.textContent = '🤖 Générer avec l\'IA';
    generateBtn.style.cssText = 'margin-left: 10px; padding: 8px 16px; background: #0B2447; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 13px;';
    
    generateBtn.addEventListener('click', async function() {
        const titre = document.querySelector('#id_titre').value;
        const tags = document.querySelector('#id_tags').value;
        
        if (!titre) {
            alert('Veuillez d\'abord entrer un titre.');
            return;
        }
        
        generateBtn.textContent = '⏳ Génération en cours...';
        generateBtn.disabled = true;

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

        try {
            const response = await fetch('/admin/api/generer-article/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken'),
                },
                body: JSON.stringify({ titre: titre, tags: tags })
            });
            
            const data = await response.json();
            
            if (data.contenu) {
                // Résumé
                const resumeField = document.querySelector('#id_resume');
                if (resumeField && data.resume) resumeField.value = data.resume;
                
                // Tags
                const tagsField = document.querySelector('#id_tags');
                if (tagsField && data.tags) tagsField.value = data.tags;
                
                // Contenu – textarea source (pour la sauvegarde Django)
                const contenuField = document.querySelector('#id_contenu');
                if (contenuField) {
                    contenuField.value = data.contenu;
                }

                // Contenu – éditeur visuel CKEditor 5
                const editorVisual = document.querySelector('.ck-editor__editable');
                if (editorVisual) {
                    editorVisual.innerHTML = data.contenu;
                }
                
                alert('✅ Article généré avec succès !');
            } else {
                alert('❌ Erreur : ' + (data.erreur || 'Réponse vide de l\'IA'));
            }
        } catch (err) {
            alert('❌ Erreur réseau.');
            console.error('Erreur:', err);
        } finally {
            generateBtn.textContent = '🤖 Générer avec l\'IA';
            generateBtn.disabled = false;
        }
    });
    
    titreField.parentNode.appendChild(generateBtn);
});