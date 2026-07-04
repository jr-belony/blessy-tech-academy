// Fade-in au scroll
const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('is-visible');
        }
    });
}, { threshold: 0.15 });

document.querySelectorAll('.fade-in-section').forEach(el => observer.observe(el));

// Compteurs animés – compatible avec .stat-nombre et .compteur
function animateCounter(el) {
    // lit data-target puis data-cible
    let target = parseInt(el.getAttribute('data-target'), 10);
    if (isNaN(target)) {
        target = parseInt(el.getAttribute('data-cible'), 10);
    }
    if (isNaN(target)) return;

    let suffix = el.getAttribute('data-suffix') || '';
    let current = 0;
    const increment = Math.ceil(target / 40);
    const timer = setInterval(() => {
        current += increment;
        if (current >= target) {
            current = target;
            clearInterval(timer);
        }
        el.textContent = current + suffix;
    }, 20);
}

const counterObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            animateCounter(entry.target);
            counterObserver.unobserve(entry.target);
        }
    });
}, { threshold: 0.5 });

// Cible les deux sélecteurs
document.querySelectorAll('.stat-nombre, .compteur').forEach(el => counterObserver.observe(el));