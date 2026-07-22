# ================================================
# ACADEMIE/IA.PY — Fichier de compatibilité rétroactive
# Permet à TOUT le code existant qui fait "from .ia import X" 
# ou "from academie.ia import X" de continuer à fonctionner 
# SANS AUCUNE MODIFICATION, même après le déplacement physique.
# ================================================

from .services.ia_service import *  # noqa