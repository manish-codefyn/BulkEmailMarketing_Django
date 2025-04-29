from django.contrib import admin
from .models import Campaign, EmailTemplate, Plugin,CampaignAnalytics,SubscriberList
from django.utils.translation import gettext_lazy as _



@admin.register(CampaignAnalytics)
class CampaignAnalyticsAdmin(admin.ModelAdmin):
    list_display = ('campaign', 'subscriber', 'event_type', 'event_time', 'ip_address')
    list_filter = ('event_type', 'event_time')
    search_fields = ('campaign__name', 'subscriber__email', 'ip_address', 'clicked_url')
    readonly_fields = ('event_time',)
    ordering = ('-event_time',)

    fieldsets = (
        (None, {
            'fields': ('campaign', 'subscriber', 'event_type', 'event_time')
        }),
        ('Additional Info', {
            'classes': ('collapse',),
            'fields': ('ip_address', 'user_agent', 'clicked_url')
        }),
    )


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = (
        'name', 
        'subject', 
        'owner', 
        'status', 
        'sent_at', 
        'created_at', 
        'is_active'
    )
    list_filter = ('status', 'is_active', 'created_at', 'sent_at', 'owner')
    search_fields = ('name', 'subject', 'content')
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    fieldsets = (
        (None, {
            'fields': ('name', 'subject', 'preview_text', 'content', 'template', 'list', 'owner')
        }),
        (_('Sending Details'), {
            'fields': ('status', 'sent_at', 'task_id', 'sent_count', 'error_count', 'open_count', 'click_count', 'bounce_count', 'unsubscribe_count'),
            'classes': ('collapse',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ('created_at', 'updated_at')  # Makes these fields read-only

    def get_readonly_fields(self, request, obj=None):
        """Makes `sent_at` field readonly when the campaign is sent"""
        if obj and obj.sent_at:
            return self.readonly_fields + ('sent_at',)
        return self.readonly_fields




@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'subject', 'created_at', 'is_active')
    search_fields = ('name', 'subject')
    list_filter = ('is_active', 'created_at')
    ordering = ('-created_at',)


@admin.register(Plugin)
class PluginAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at', 'is_active')
    search_fields = ('name', 'description')
    list_filter = ('is_active', 'created_at')
    ordering = ('-created_at',)
