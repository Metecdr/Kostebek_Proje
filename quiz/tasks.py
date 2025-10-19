from background_task import background
from django.core.management import call_command
from django.core.management.base import CommandError
import logging

logger = logging.getLogger(__name__)

# Schedule: 604800 saniye = 7 gün
@background(schedule=604800)
def haftalik_sifirlama_gorevi():
    """Haftalık puanları sıfırlar"""
    logger.info("Haftalık puan sıfırlama görevi başlatıldı")
    
    try:
        call_command('sifirla_haftalik_puan')
        logger.info("Haftalık puanlar başarıyla sıfırlandı")
        
    except CommandError as e:
        logger.error(f"Management komut hatası: {e}")
        
    except Exception as e:
        logger.exception(f"Beklenmeyen hata oluştu: {e}")