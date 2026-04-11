from profile.models import Bildirim
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

# Bildirim türüne göre cooldown süreleri (dakika)
BILDIRIM_COOLDOWN = {
    'liderlik': 5,
    'basari': 5,
    'sistem': 5,
    'rozet': 0,          # Rozet bildirimleri her zaman gönderilir
    'meydan_okuma': 0,   # Meydan okuma/rövanş her zaman gönderilir
    'arkadas': 0,        # Arkadaşlık istekleri her zaman gönderilir
}


def bildirim_gonder(kullanici, tip, baslik, mesaj, icon='🔔', iliskili_rozet=None):
    """
    Kullanıcıya bildirim gönder (rate limiting ile)
    """
    try:
        # Cooldown kontrolü
        cooldown_dk = BILDIRIM_COOLDOWN.get(tip, 5)
        if cooldown_dk > 0:
            son_bildirim = Bildirim.objects.filter(
                kullanici=kullanici,
                tip=tip,
                olusturma_tarihi__gte=timezone.now() - timedelta(minutes=cooldown_dk)
            ).exists()
            if son_bildirim:
                logger.debug(f"⏳ Bildirim cooldown: {kullanici.username} - {tip} ({cooldown_dk}dk)")
                return None

        bildirim = Bildirim.objects.create(
            kullanici=kullanici,
            tip=tip,
            baslik=baslik,
            mesaj=mesaj,
            icon=icon,
            iliskili_rozet=iliskili_rozet
        )
        logger.info(f"📬 Bildirim gönderildi: {kullanici.username} - {baslik}")
        return bildirim
    except Exception as e:
        logger.error(f"Bildirim hatası: {e}", exc_info=True)
        return None


def rozet_bildirimi_gonder(kullanici, rozet):
    """Rozet kazanıldığında bildirim"""
    return bildirim_gonder(
        kullanici=kullanici,
        tip='rozet',
        baslik='🏅 Yeni Rozet Kazandın!',
        mesaj=f'"{rozet.get_kategori_display()}" rozetini kazandın!  {rozet.icon}',
        icon=rozet.icon,
        iliskili_rozet=rozet
    )


def liderlik_bildirimi_gonder(kullanici, sira, tip='genel'):
    """Liderlikte ilerleme bildirimi"""
    mesajlar = {
        'top_50': f'🎯 Tebrikler! Top 50\'ye girdin!  Sıralaman: {sira}',  # ✅ Düzeltildi
        'top_10': f'🔥 Harika! Top 10\'a girdin! Sıralaman: {sira}',  # ✅ Düzeltildi
        'top_3': f'💎 Muhteşem! Top 3\'tesin! Sıralaman: {sira}',  # ✅ Düzeltildi
        'lider': f'👑 İNANILMAZ! Lider oldun! 1. sıradasın! ',
    }
    
    if sira == 1:
        mesaj_tipi = 'lider'
    elif sira <= 3:
        mesaj_tipi = 'top_3'
    elif sira <= 10:
        mesaj_tipi = 'top_10'
    elif sira <= 50:
        mesaj_tipi = 'top_50'
    else: 
        return None
    
    return bildirim_gonder(
        kullanici=kullanici,
        tip='liderlik',
        baslik='📊 Liderlik Başarısı!',
        mesaj=mesajlar[mesaj_tipi],
        icon='🏆'
    )


def basari_bildirimi_gonder(kullanici, basari_metni, icon='🌟'):
    """Özel başarı bildirimi"""
    return bildirim_gonder(
        kullanici=kullanici,
        tip='basari',
        baslik='✨ Özel Başarı!',
        mesaj=basari_metni,
        icon=icon
    )