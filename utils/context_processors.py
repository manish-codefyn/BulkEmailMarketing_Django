from datetime import datetime

from django.conf import settings
from core.models import SiteSetting

def site_settings(request):
    setting = SiteSetting.objects.first()

    return {
            # General Info
            'site_name': setting.site_name if setting and setting.site_name else settings.SITE_NAME,
            'tagline': setting.tagline if setting and setting.tagline else '',
            'description': setting.description if setting and setting.description else '',

            # Logo & Favicon
            'logo_url': setting.logo.url if setting and setting.logo else settings.DEFAULT_LOGO_URL,
            'favicon_url': setting.favicon.url if setting and setting.favicon else settings.DEFAULT_FAVICON_URL,

            # Contact Info
            'email': setting.email if setting and setting.email else settings.SITE_EMAIL,
            'mobile': setting.mobile if setting and setting.mobile else settings.SITE_MOBILE,
            'address': setting.address if setting and setting.address else settings.SITE_ADDRESS,

            # Social Media
            'facebook': setting.facebook if setting and setting.facebook else '',
            'instagram': setting.instagram if setting and setting.instagram else '',
            'linkedin': setting.linkedin if setting and setting.linkedin else '',
            'twitter': setting.twitter if setting and setting.twitter else '',
            'youtube': setting.youtube if setting and setting.youtube else '',

            # SEO
            'meta_title': setting.meta_title if setting and setting.meta_title else settings.SITE_NAME,
            'meta_description': setting.meta_description if setting and setting.meta_description else '',
            'meta_keywords': setting.meta_keywords if setting and setting.meta_keywords else '',
        }

def global_context(request):
    return {
        'current_year': datetime.now().year,
        'currency': "₹ Rupee",
        'time_zone': "Indian",
        'app_name': "Fixenix",
    }


