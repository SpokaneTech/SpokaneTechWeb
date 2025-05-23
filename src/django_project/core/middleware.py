from django.utils import timezone


class PstTimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        timezone.activate("America/Los_Angeles")
        return self.get_response(request)
