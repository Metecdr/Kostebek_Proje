from django.apps import AppConfig
import os
from profile import scheduler

class ProfileConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'profile'
    
    def ready(self):
        # Sadece ana process'te çalıştır (reload sırasında 2 kere çalışmasın)
        if os.environ.get('RUN_MAIN') == 'true':
            scheduler.start_scheduler()