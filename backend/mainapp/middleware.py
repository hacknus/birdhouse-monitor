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

        # Retrieve the active visitors set from cache (default to empty set)
        active_visitors = cache.get("active_visitors", set())

        # Add the current visitor
        active_visitors.add(visitor_key)

        # Store the updated set back in cache (with 5-minute timeout)
        cache.set("active_visitors", active_visitors, timeout=300)

        # Refresh visitor's individual key (to track their last activity time)
        cache.set(visitor_key, now(), timeout=300)

        response = self.get_response(request)
        return response


def get_active_visitors():
    # Get the set of active visitors
    active_visitors = cache.get("active_visitors", set())

    # Filter out expired visitors (whose individual keys are no longer in cache)
    valid_visitors = {key for key in active_visitors if cache.get(key)}

    # Save the cleaned visitor list back to cache
    cache.set("active_visitors", valid_visitors, timeout=300)

    return len(valid_visitors)  # Return the number of active visitors