from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum
from billing.models import Order

@staff_member_required
def vue_monitoring_conversion(request):
    il_y_a_7j = timezone.now() - timedelta(days=7)
    il_y_a_24h = timezone.now() - timedelta(hours=24)

    # Paniers abandonnés (créés il y a plus de 24h, jamais payés, dans les 7 derniers jours)
    paniers_abandonnes = Order.objects.filter(
        statut='en_attente',
        date_creation__lt=il_y_a_24h,
        date_creation__gte=il_y_a_7j
    ).select_related('utilisateur').order_by('-date_creation')[:20]

    total_commandes_7j = Order.objects.filter(date_creation__gte=il_y_a_7j).count()
    commandes_payees_7j = Order.objects.filter(date_creation__gte=il_y_a_7j, statut='paye').count()
    taux_conversion = round((commandes_payees_7j / total_commandes_7j) * 100) if total_commandes_7j else 0

    # Valeur totale des paniers abandonnés sur la même période
    valeur_paniers_abandonnes = Order.objects.filter(
        statut='en_attente',
        date_creation__lt=il_y_a_24h,
        date_creation__gte=il_y_a_7j
    ).aggregate(t=Sum('total'))['t'] or 0

    return render(request, 'admin/monitoring_conversion.html', {
        'title': '🎯 Monitoring Conversion',
        'site_header': 'Administration BTA',
        'taux_conversion': taux_conversion,
        'total_commandes_7j': total_commandes_7j,
        'valeur_paniers_abandonnes': valeur_paniers_abandonnes,
        'paniers_abandonnes': paniers_abandonnes,
    })