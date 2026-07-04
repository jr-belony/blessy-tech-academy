class SecurityHeadersMiddleware:
    """
    Middleware qui ajoute les en-têtes de sécurité manquants :
    - Content-Security-Policy
    - Permissions-Policy
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Content-Security-Policy renforcée
        response['Content-Security-Policy'] = (
            "default-src 'none'; "
            "script-src 'self' https://cdn.ckeditor.com https://cdn.jsdelivr.net; "
            "style-src 'self' https://cdn.ckeditor.com https://cdn.jsdelivr.net 'unsafe-inline'; "
            "img-src 'self' data: https://*; "
            "font-src 'self' https://cdn.ckeditor.com; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'; "
            "frame-src 'none'; "
            "object-src 'none'; "
            "upgrade-insecure-requests; "
        )

        # Permissions-Policy complète
        response['Permissions-Policy'] = (
            "camera=(), "
            "microphone=(), "
            "geolocation=(), "
            "payment=(), "
            "usb=(), "
            "magnetometer=(), "
            "gyroscope=(), "
            "speaker=(), "
            "vibrate=(), "
            "fullscreen=(self), "
            "display-capture=()"
        )

        return response