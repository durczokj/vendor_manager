"""Check if the request is an API request."""


def is_api_request(request):
    """Check if the request is an API request."""
    return request.headers.get("Accept") == "application/json" or request.content_type == "application/json"
