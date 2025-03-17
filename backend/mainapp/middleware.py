from django.core.cache import cache
from django.utils.timezone import now
import hashlib


class TrackVisitorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Identify user by IP + User-Agent (better uniqueness)
        visitor_key = hashlib.md5(
            (request.META.get("REMOTE_ADDR", "") + request.META.get("HTTP_USER_AGENT", "")).encode()
        ).hexdigest()

        # Store in cache with a timeout (e.g., 5 minutes)
        cache.set(visitor_key, now(), timeout=300)

        response = self.get_response(request)
        return response


def get_active_visitors():
    keys = cache.keys("*")  # Get all cached visitor keys
    return len([key for key in keys if key.startswith("active_visitor_")])
