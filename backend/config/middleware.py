class PrivateResponseMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.path.startswith("/api/"):
            response["Cache-Control"] = "no-store, private"
            response["X-Content-Type-Options"] = "nosniff"
        return response


class DemoAccountMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        from django.contrib.auth import logout
        from modules.identity.demo_access import demo_access_denied

        if request.user.is_authenticated and demo_access_denied(request.user):
            logout(request)
        return self.get_response(request)
