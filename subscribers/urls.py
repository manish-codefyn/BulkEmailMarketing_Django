from django.urls import path
from .import views
  

app_name = "subscriber"
urlpatterns = [
    path('list/<uuid:list_id>/import/', views.subscriber_import_view, name='subscriber_import'),
    path('export-subscribers/', views.export_subscribers, name='download_sample_subscribers'),

    path('subscriber-lists/export/', views.export_subscriber_lists, name='export_subscriber_lists'),
    path('subscriber-lists/import/', views.import_subscriber_lists, name='import_subscriber_lists'),
     path('list/import-subscribers/', views.SubscriberImportView.as_view(), name='import_subscribers_lists'),

    path('', views.SubscriberListView.as_view(), name='subscriber_list'),
    path('new/', views.SubscriberCreateView.as_view(), name='subscriber_create'),
    path('<uuid:pk>/edit/', views.SubscriberUpdateView.as_view(), name='subscriber_update'),
    path('<uuid:pk>/delete/', views.SubscriberDeleteView.as_view(), name='subscriber_delete'),
    
    path('lists/', views.SubscriberListListView.as_view(), name='subscriberlist_list'),
    path('lists/new/', views.SubscriberListCreateView.as_view(), name='subscriberlist_create'),
    path('lists/<uuid:pk>/', views.SubscriberListDetailView.as_view(), name='subscriberlist_detail'),
    path('lists/<uuid:pk>/edit/', views.SubscriberListUpdateView.as_view(), name='subscriberlist_update'),
    path('lists/<uuid:pk>/delete/', views.SubscriberListDeleteView.as_view(), name='subscriberlist_delete'),
    path('unsubscribe/<str:signed_email>/', views.UnsubscribeView.as_view(), name='unsubscribe'),
]