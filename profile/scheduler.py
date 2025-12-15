from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from django.core.management import call_command
import logging

logger = logging.getLogger(__name__)

scheduler = None


def reset_liderlik_job():
    """Liderlik reset görevi"""
    try:
        call_command('reset_liderlik')
        logger.info('✅ Liderlik reset başarılı')
    except Exception as e: 
        logger.error(f'❌ Liderlik reset hatası: {e}')


def start_scheduler():
    """Zamanlayıcıyı başlat"""
    global scheduler
    
    if scheduler is not None: 
        return  # Zaten çalışıyor
    
    scheduler = BackgroundScheduler()
    
    # Her gün saat 00:05'te çalıştır
    scheduler.add_job(
        reset_liderlik_job,
        trigger=CronTrigger(hour=0, minute=5),
        id='liderlik_reset',
        name='Liderlik Otomatik Reset',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info('🚀 Liderlik zamanlayıcı başlatıldı!  (Her gün 00:05)')


def stop_scheduler():
    """Zamanlayıcıyı durdur"""
    global scheduler
    if scheduler is not None:
        scheduler.shutdown()
        scheduler = None
        logger.info('🛑 Liderlik zamanlayıcı durduruldu')