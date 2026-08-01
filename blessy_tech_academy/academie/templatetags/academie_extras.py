# ================================================
# TEMPLATETAGS/ACADEMIE_EXTRAS.PY — Filtre get_item pour dashboard cohorte
# ================================================
from django import template
register = template.Library()

@register.filter
def get_item(dictionnaire, cle):
    return dictionnaire.get(cle, 0)