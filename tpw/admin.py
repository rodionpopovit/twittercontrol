from django.contrib import admin
from .models import TweetMsg, Community, TriggerFrequency, TriggerRule

# Register your models here.
admin.site.register(Community)
admin.site.register(TriggerFrequency)
admin.site.register(TriggerRule)
admin.site.register(TweetMsg)