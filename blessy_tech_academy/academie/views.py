from django.shortcuts import render


def accueil(request):
    """Page d'accueil."""
    formations = [
        {
            'icone': '🐍',
            'nom': 'Python & Django',
            'description': 'Crée des applications web professionnelles.',
            'duree': '6 mois',
            'prix': 300,
        },
        {
            'icone': '🎨',
            'nom': 'Design Web',
            'description': 'Maîtrise HTML, CSS et JavaScript.',
            'duree': '4 mois',
            'prix': 200,
        },
        {
            'icone': '🤖',
            'nom': 'Intelligence Artificielle',
            'description': 'Exploite les outils IA modernes.',
            'duree': '4 mois',
            'prix': 250,
        },
        {
            'icone': '🖥️',
            'nom': 'Maintenance Informatique',
            'description': 'Diagnostique et répare les systèmes.',
            'duree': '6 mois',
            'prix': 300,
        },
    ]
    return render(request, 'academie/accueil.html', {'formations': formations})


def formations(request):
    """Page des formations."""
    return render(request, 'academie/formations.html')


def apropos(request):
    """Page à propos."""
    return render(request, 'academie/apropos.html')


def contact(request):
    """Page de contact."""
    return render(request, 'academie/contact.html')