"""Viewsets exposed under /api/v1/."""

from rest_framework import viewsets

from companies.models import Company

from .serializers import CompanySerializer


class CompanyViewSet(viewsets.ModelViewSet):
    """Company list/create/detail endpoints."""

    queryset = Company.objects.all().order_by("id")
    serializer_class = CompanySerializer
