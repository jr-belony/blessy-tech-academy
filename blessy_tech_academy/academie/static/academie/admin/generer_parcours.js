// ================================================
// GENERER_PARCOURS.JS — Bouton "Générer un parcours pro complet avec IA"
// ================================================

document.addEventListener('DOMContentLoaded', function() {
    const zoneAjout = document.querySelector('#content-main') || document.querySelector('.module');
    if (!zoneAjout) return;

    const bouton = document.createElement('button');
    bouton.type = 'button';
    bouton.textContent = '🚀 Générer un nouveau parcours pro avec IA';
    bouton.style.cssText = 'background:linear-gradient(135deg,#FF6B00,#e85a2a); color:white; border:none; padding:12px 24px; border-radius:8px; font-weight:700; cursor:pointer; margin:16px 0; display:block;';

    bouton.addEventListener('click', async function() {
        const titreMetier = prompt('Quel métier ce parcours doit-il préparer ? (ex: Développeur Full Stack)');
        if (!titreMetier) return;

        const niveau = prompt('Niveau de départ (debutant/intermediaire/avance) :', 'intermediaire') || 'intermediaire';

        bouton.textContent = '⏳ Génération en cours (peut prendre 20s)...';
        bouton.disabled = true;

        const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
                           document.cookie.match(/csrftoken=([^;]+)/)?.[1];

        try {
            const reponse = await fetch('/api/generer-parcours-admin/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
                body: JSON.stringify({ titre_metier: titreMetier, niveau: niveau })
            });
            const data = await reponse.json();

            if (data.succes) {
                alert(`✅ Parcours créé (brouillon) !\n${data.formations_liees}/${data.formations_suggerees_total} formations existantes liées automatiquement.\n\nVérifie et active-le manuellement.`);
                window.location.href = `/admin/academie/parcours/${data.parcours_id}/change/`;
            } else {
                alert('❌ ' + (data.erreur || 'Erreur inconnue'));
                bouton.textContent = '🚀 Générer un nouveau parcours pro avec IA';
                bouton.disabled = false;
            }
        } catch (e) {
            alert('❌ Erreur réseau : ' + e.message);
            bouton.textContent = '🚀 Générer un nouveau parcours pro avec IA';
            bouton.disabled = false;
        }
    });

    zoneAjout.prepend(bouton);
});