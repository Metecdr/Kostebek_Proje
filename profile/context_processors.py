from django.conf import settings


def analytics_settings(request):
    """Google Analytics ve Search Console ID'lerini tüm template'lere ilet"""
    return {
        'GOOGLE_ANALYTICS_ID': getattr(settings, 'GOOGLE_ANALYTICS_ID', ''),
        'GOOGLE_SC_TOKEN': getattr(settings, 'GOOGLE_SC_TOKEN', ''),
    }
