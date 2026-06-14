from django.shortcuts import render
from django.http import HttpResponse


def accueil(request):
    """Page d'accueil de Blessy Tech Academy."""
    return HttpResponse("""
        <h1>⚡ Blessy Tech Academy</h1>
        <p>L'école de la haute technologie moderne d'Haïti.</p>
        <nav>
            <a href="/">Accueil</a> |
            <a href="/formations/">Formations</a> |
            <a href="/contact/">Contact</a>
        </nav>
    """)


def formations(request):
    """Page des formations."""
    return HttpResponse("""
        <h1>🎓 Nos Formations</h1>
        <ul>
            <li>🐍 Python & Django — 6 mois — 300 USD</li>
            <li>🎨 Design Web — 4 mois — 200 USD</li>
            <li>🤖 Intelligence Artificielle — 4 mois — 250 USD</li>
            <li>🖥️ Maintenance Informatique — 6 mois — 300 USD</li>
        </ul>
        <a href="/">← Retour accueil</a>
    """)


def contact(request):
    """Page de contact."""
    return HttpResponse("""
        <h1>📧 Contactez-nous</h1>
        <p>Email : contact@blessyconnect.com</p>
        <p>Disponible : Lundi-Vendredi, 8h-18h</p>
        <a href="/">← Retour accueil</a>
    """)