from django.core.cache import cache
from django.utils.timezone import now
import hashlib


class TrackVisitorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Generate a unique visitor key using IP + User-Agent
        visitor_key = hashlib.md5(
            (request.META.get("REMOTE_ADDR", "") + request.META.get("HTTP_USER_AGENT", "")).encode()
        ).hexdigest()

        # Store visitor key with timestamp (5 minutes expiration)
        cache.set(visitor_key, now(), timeout=300)

        # Maintain a separate list of all visitor keys
        active_visitors = cache.get("active_visitors", set())
        active_visitors.add(visitor_key)
        cache.set("active_visitors", active_visitors, timeout=300)

        response = self.get_response(request)
        return response


def get_active_visitors():
    active_visitors = cache.get("active_visitors", set())
    return len(active_visitors)
