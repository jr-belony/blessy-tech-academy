# ================================================
# SERVICES/__INIT__.PY — Point d'entrée unique du package services
# Garantit que "from academie.services.ia_service import X" continue de fonctionner 
# partout dans le projet (views.py, admin.py) — AUCUN import existant 
# à modifier ailleurs dans le code
# ================================================

from .ia_service import *
from .email_service import *
from .async_tasks import *