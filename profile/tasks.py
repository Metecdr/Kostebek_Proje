from background_task import background
from background_task.models import Task
from profile.models import OgrenciProfili
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


@background(schedule=0)
def liderlik_reset_kontrolu():
    """Liderlik reset kontrolü - Her gün çalışır"""
    bugun = timezone.now().date()
    guncellenecek_profiller = []
    
    for profil in OgrenciProfili.objects.all():
        degisti = False
        
        # Günlük reset
        if profil.son_gunluk_reset < bugun:
            profil.gunluk_puan = 0
            profil.gunluk_cozulen = 0
            profil.gunluk_dogru = 0
            profil.gunluk_yanlis = 0
            profil.son_gunluk_reset = bugun
            degisti = True
        
        # Haftalık reset (Pazartesi)
        haftanin_basi = bugun - timedelta(days=bugun.weekday())
        if profil.son_haftalik_reset < haftanin_basi:
            profil.haftalik_puan = 0
            profil.haftalik_cozulen = 0
            profil.haftalik_dogru = 0
            profil.haftalik_yanlis = 0
            profil.son_haftalik_reset = haftanin_basi
            profil.hafta_baslangic = timezone.now()
            degisti = True
        
        # Aylık reset (Ayın 1'i)
        ayin_basi = bugun.replace(day=1)
        if profil.son_aylik_reset < ayin_basi:
            profil.aylik_puan = 0
            profil.aylik_cozulen = 0
            profil.aylik_dogru = 0
            profil.aylik_yanlis = 0
            profil.son_aylik_reset = ayin_basi
            degisti = True
        
        if degisti: 
            guncellenecek_profiller.append(profil)
    
    # Toplu güncelleme
    if guncellenecek_profiller: 
        OgrenciProfili.objects.bulk_update(
            guncellenecek_profiller,
            ['gunluk_puan', 'gunluk_cozulen', 'gunluk_dogru', 'gunluk_yanlis', 'son_gunluk_reset',
             'haftalik_puan', 'haftalik_cozulen', 'haftalik_dogru', 'haftalik_yanlis', 'son_haftalik_reset', 'hafta_baslangic',
             'aylik_puan', 'aylik_cozulen', 'aylik_dogru', 'aylik_yanlis', 'son_aylik_reset']
        )
        logger.info(f'Liderlik reset:  {len(guncellenecek_profiller)} profil güncellendi')
    
    # Kendini tekrar planla (24 saat sonra)
    liderlik_reset_kontrolu(schedule=86400)  # 86400 saniye = 24 saat


def reset_zamanlayici_baslat():
    """İlk görev zaten var mı kontrol et"""
    if not Task.objects.filter(task_name='profile.tasks.liderlik_reset_kontrolu').exists():
        liderlik_reset_kontrolu(schedule=60)  # 60 saniye sonra başla