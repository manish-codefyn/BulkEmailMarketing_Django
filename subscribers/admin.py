from django.contrib import admin
from .models import SubscriberList, Subscriber

@admin.register(SubscriberList)
class SubscriberListAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_at', 'updated_at', 'is_active')
    search_fields = ('name',)
    list_filter = ('is_active', 'created_at')
    ordering = ('-created_at',)

@admin.register(Subscriber)
class SubscriberAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'is_active', 'subscribed_at', 'unsubscribed_at')
    search_fields = ('email', 'first_name', 'last_name')
    list_filter = ('is_active', 'subscribed_at', 'unsubscribed_at')
    ordering = ('-subscribed_at',)
    filter_horizontal = ('lists',)  # To manage ManyToMany field nicely in the admin
