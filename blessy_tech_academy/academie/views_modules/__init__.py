# ================================================
# VIEWS_MODULES/__INIT__.PY — Ré-export complet
# Garantit que urls.py continue d'écrire "views.nom_de_vue" 
# exactement comme avant — AUCUNE modification d'urls.py requise
# ================================================

from .core_views import *
from .learning_views import *
from .billing_views import *
from .crm_views import *
from .forum_views import *
from .ia_views import *
from .admin_views import *
