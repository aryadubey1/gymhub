from django.contrib import admin
from .models import MessageTemplate, MessageLog


@admin.register(MessageTemplate)
class MessageTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'is_active')
    list_filter = ('category',)


admin.site.register(MessageLog)