import logging
import time

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger("bta_performance")


class SecurityHeadersMiddleware:
    """
    Middleware qui ajoute les en-têtes de sécurité :
    - Content-Security-Policy
    - Permissions-Policy
    S'adapte automatiquement selon l'environnement (DEBUG).
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.debug = getattr(settings, "DEBUG", False)

    def __call__(self, request):
        response = self.get_response(request)

        if self.debug:
            # DÉVELOPPEMENT : CSP assoupli pour localhost
            response["Content-Security-Policy"] = (
                "default-src 'self' http://127.0.0.1:8000 http://localhost:8000; "
                "script-src 'self' 'unsafe-inline' "
                "https://cdn.ckeditor.com https://cdn.jsdelivr.net "
                "https://www.googletagmanager.com https://www.google-analytics.com; "
                "style-src 'self' 'unsafe-inline' "
                "https://fonts.googleapis.com https://cdn.ckeditor.com https://cdn.jsdelivr.net; "
                "img-src 'self' data: https:; "
                "font-src 'self' https://fonts.googleapis.com https://fonts.gstatic.com https://cdn.ckeditor.com; "
                "connect-src 'self' http://127.0.0.1:8000 http://localhost:8000 "
                "https://cdn.ckeditor.com https://www.google-analytics.com; "
                "manifest-src 'self'; "
                "frame-ancestors 'self'; "
                "base-uri 'self'; "
                "form-action 'self'; "
                "frame-src 'self' https://www.google.com; "
                "object-src 'none';"
            )
        else:
            # PRODUCTION : CSP strict (scripts inline autorisés temporairement)
            response["Content-Security-Policy"] = (
                "default-src 'none'; "
                "script-src 'self' 'unsafe-inline' "
                "https://cdn.ckeditor.com https://cdn.jsdelivr.net "
                "https://www.googletagmanager.com https://www.google-analytics.com; "
                "style-src 'self' 'unsafe-inline' "
                "https://fonts.googleapis.com https://cdn.ckeditor.com https://cdn.jsdelivr.net; "
                "img-src 'self' data: https:; "
                "font-src 'self' https://fonts.googleapis.com https://fonts.gstatic.com https://cdn.ckeditor.com; "
                "connect-src 'self' https://cdn.ckeditor.com https://www.google-analytics.com; "
                "manifest-src 'self'; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self'; "
                "frame-src 'self' https://www.google.com; "
                "object-src 'none'; "
                "upgrade-insecure-requests;"
            )

        # Permissions-Policy (identique en dev et production)
        response["Permissions-Policy"] = (
            "camera=(), "
            "microphone=(), "
            "geolocation=(), "
            "payment=(), "
            "usb=(), "
            "magnetometer=(), "
            "gyroscope=(), "
            "fullscreen=(self), "
            "display-capture=()"
        )

        # En-têtes de sécurité supplémentaires (production uniquement)
        if not self.debug:
            response["X-Content-Type-Options"] = "nosniff"
            response["X-Frame-Options"] = "DENY"
            response["X-XSS-Protection"] = "1; mode=block"
            response["Referrer-Policy"] = "strict-origin-when-cross-origin"

        return response


class MonitoringPerformanceMiddleware:
    """Log les requêtes HTTP prenant plus de 1 seconde — alerte proactive."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        debut = time.time()
        response = self.get_response(request)
        duree = time.time() - debut

        if duree > 1.0:
            logger.warning(f"⚠️ Requête lente ({duree:.2f}s) : {request.path}")

        return response


class AcademieCouranteMiddleware:
    """
    Détecte quelle Academie est active pour la requête :
    1. Via sous-domaine personnalisé (business.blessytechacademy.com)
    2. Sinon via l'Academie par défaut (Blessy Tech Academy)
    Injecte request.academie_courante utilisable partout.
    Utilise le cache pour éviter des requêtes DB à chaque hit.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        from .models import Academie

        host = request.get_host().split(":")[0]

        # Clé de cache unique par domaine
        cache_key = f"academie_courante:{host}"
        academie = cache.get(cache_key)

        if academie is None:
            academie = Academie.objects.filter(domaine_personnalise=host, actif=True).first()

            if not academie:
                academie = Academie.objects.filter(est_academie_par_defaut=True, actif=True).first()

            # Stocke dans le cache pour 1 heure (3600 secondes)
            if academie:
                cache.set(cache_key, academie, 3600)

        request.academie_courante = academie
        return self.get_response(request)
