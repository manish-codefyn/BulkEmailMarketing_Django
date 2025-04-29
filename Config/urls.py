from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # Allauth URLs
    path('accounts/', include('allauth.urls')),

    # Campaigns URLs
    path('campaigns/', include('campaigns.urls')),

    # Subscribers URLs
    path('subscribers/', include('subscribers.urls')),

    # Home page
    path('', include('core.urls')),

]

# Static & Media files in development
if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
