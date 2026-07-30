"""Shared API pagination classes."""

from rest_framework.pagination import PageNumberPagination


class DefaultPageNumberPagination(PageNumberPagination):
    """Default page-number pagination for API list endpoints."""

    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 200
