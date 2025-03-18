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

        print("Visitor key:", visitor_key)

        # Store visitor in cache with 5-minute expiration
        cache.set(visitor_key, now(), timeout=300)

        response = self.get_response(request)
        print("Visitor response:", response)
        return response


def get_active_visitors():
    from django.core.cache import caches
    print("Getting active visitors...")
    cache_backend = caches["default"]
    print("Cache backend:", cache_backend)

    if hasattr(cache_backend, "client"):  # Ensure Redis is being used
        redis_client = cache_backend.client.get_client(write=True)
        print(f"{redis_client=}")
        visitor_keys = list(redis_client.scan_iter("visitor_*"))
        return len(visitor_keys)
    print("no redis")
    return 0  # If not using Redis, return 0 (or handle differently)
