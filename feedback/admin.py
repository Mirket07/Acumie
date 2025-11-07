from django.contrib import admin
from .models import Feedback

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('course', 'created_at',)
    list_filter = ('course', 'created_at')
    search_fields = ('feedback_text',)
    readonly_fields = ('created_at',)