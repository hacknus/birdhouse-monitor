from django.core.cache import cache
from django.utils.timezone import now
import hashlib

class TrackVisitorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Generate a unique visitor key using IP + User-Agent
        visitor_key = "visitor_" + hashlib.md5(
            (request.META.get("REMOTE_ADDR", "") + request.META.get("HTTP_USER_AGENT", "")).encode()
        ).hexdigest()

        # Store visitor in cache with 5-minute expiration
        cache.set(visitor_key, now(), timeout=300)

        response = self.get_response(request)
        return response


def get_active_visitors():
    from django.core.cache import caches
    cache_backend = caches["default"]

    if hasattr(cache_backend, "client"):  # Ensure Redis is being used
        redis_client = cache_backend.client.get_client(write=True)
        visitor_keys = list(redis_client.scan_iter("visitor_*"))
        return len(visitor_keys)

    return 0  # If not using Redis, return 0 (or handle differently)
