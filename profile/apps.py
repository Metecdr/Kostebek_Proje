# profile/apps.py dosyasının içeriği

from django.apps import AppConfig

class ProfileConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'profile'
    
    # BU METODU EKLEYİN:
    def ready(self):
        # Uygulama hazır olduğunda sinyal dosyasını içeri aktar
        import profile.signals