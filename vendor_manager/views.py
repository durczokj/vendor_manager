"""Views for the vendor_manager application."""

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.template import loader


@login_required
def main(request):
    """Render the main page."""
    template = loader.get_template("main.html")
    return HttpResponse(template.render())
