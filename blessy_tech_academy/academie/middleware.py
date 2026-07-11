from django.conf import settings

class SecurityHeadersMiddleware:
    """
    Middleware qui ajoute les en-têtes de sécurité manquants :
    - Content-Security-Policy
    - Permissions-Policy
    S'adapte automatiquement selon l'environnement (DEBUG).
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.debug = getattr(settings, 'DEBUG', False)

    def __call__(self, request):
        response = self.get_response(request)

        if self.debug:
            # ========== DÉVELOPPEMENT : CSP assoupli ==========
            response['Content-Security-Policy'] = (
                "default-src 'self' http://127.0.0.1:8000 http://localhost:8000; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' "
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
            # ========== PRODUCTION : CSP strict ==========
            response['Content-Security-Policy'] = (
                "default-src 'none'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' "
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
        response['Permissions-Policy'] = (
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
            response['X-Content-Type-Options'] = 'nosniff'
            response['X-Frame-Options'] = 'DENY'
            response['X-XSS-Protection'] = '1; mode=block'
            response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
            # HSTS est géré par Django settings (SECURE_HSTS_SECONDS)

        return response