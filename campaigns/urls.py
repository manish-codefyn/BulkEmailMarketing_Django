from django.urls import path
from . import views
app_name = "campaign"

urlpatterns = [
    path('campaigns/<uuid:campaign_id>/analytics/', views.CampaignAnalyticsView.as_view(), name='campaign_analytics'),
    path('track/open/<uuid:campaign_id>/<uuid:subscriber_id>/', views.track_open, name='track_open'),
    path('track/click/<uuid:campaign_id>/<uuid:subscriber_id>/<path:url>/', views.track_click, name='track_click'),
    # Campaign URLs
    path('', views.CampaignListView.as_view(), name='campaign_list'),
    path('new/', views.CampaignCreateView.as_view(), name='campaign_create'),
    path('<uuid:pk>/', views.CampaignDetailView.as_view(), name='campaign_detail'),
    path('<uuid:pk>/edit/', views.CampaignUpdateView.as_view(), name='campaign_update'),
    path('<uuid:pk>/delete/', views.CampaignDeleteView.as_view(), name='campaign_delete'),
    
    # Email Sending URLs
    path('<uuid:pk>/send-test/', views.send_test_email, name='send_test_email'),
    path('<uuid:pk>/send/', views.send_campaign, name='send_campaign'),
    path('<uuid:pk>/send-live/', views.send_campaign_live, name='send_campaign_live'),
    path('<uuid:pk>/status/', views.check_campaign_status, name='campaign_status'),
    path('<uuid:pk>/analysis/', views.campaign_analysis, name='campaign_analysis'),
    path('<uuid:pk>/monitor/', views.campaign_monitor, name='campaign_monitor'),
    path('<uuid:pk>/progress/', views.campaign_progress, name='campaign_progress'),
    
    # Email Template URLs
    path('email-templates/', views.EmailTemplateListView.as_view(), name='emailtemplate_list'),
    path('email-templates/new/', views.EmailTemplateCreateView.as_view(), name='emailtemplate_create'),
    path('email-templates/<uuid:pk>/delete/', views.EmailTemplateDeleteView.as_view(), name='emailtemplate_delete'),
    path('email-templates/<uuid:pk>/edit/', views.EmailTemplateUpdateView.as_view(), name='emailtemplate_update'),
    path('email-templates/gallery', views.EmailTemplateGalleryView.as_view(), name='emailtemplate_gallery'),
    path('email-templates/<uuid:pk>/', views.EmailTemplatePreviewView.as_view(), name='emailtemplate_preview'),
    # Plugin URLs
    path('plugins/', views.PluginListView.as_view(), name='plugin_list'),
    path('plugins/new/', views.PluginCreateView.as_view(), name='plugin_create'),
    path('plugins/<uuid:pk>/edit/', views.PluginUpdateView.as_view(), name='plugin_update'),
    path('plugins/<uuid:pk>/delete/', views.PluginDeleteView.as_view(), name='plugin_delete'),
]