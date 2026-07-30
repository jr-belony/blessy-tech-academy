# ================================================
# THROTTLES.PY — Limitation de débit pour les API partenaires
# ================================================

from rest_framework.throttling import BaseThrottle
from django.core.cache import cache

class ThrottlePartenaireAPI(BaseThrottle):
    """
    Limite les requêtes des partenaires API à 100 requêtes par heure.
    Utilise le cache Django (Redis en production, LocMem en dev).
    """
    rate = 100  # requêtes par heure

    def allow_request(self, request, view):
        if not request.user or not hasattr(request.user, 'id'):
            return True

        partenaire_id = request.user.id
        cache_key = f"throttle_partenaire_{partenaire_id}"
        count = cache.get(cache_key, 0)

        if count >= self.rate:
            return False

        cache.set(cache_key, count + 1, timeout=3600)  # 1 heure
        return True