from django.contrib import admin
from .models import Engagement, EngagementOrderVersionAssignment, EngagementUndertakingAssignment

# Register your models here.
admin.site.register(Engagement)
admin.site.register(EngagementOrderVersionAssignment)
admin.site.register(EngagementUndertakingAssignment)


