from django.db. models import Q
from profile.models import Arkadaslik
from profile.bildirim_helper import bildirim_gonder
import logging

logger = logging.getLogger(__name__)


def arkadaslik_istegi_gonder(gonderen, alan):
    """Arkadaşlık isteği gönder"""
    try: 
        # Zaten istek var mı kontrol et
        mevcut = Arkadaslik.objects.filter(
            models.Q(gonderen=gonderen, alan=alan) |
            models.Q(gonderen=alan, alan=gonderen)
        ).first()
        
        if mevcut:
            if mevcut.durum == 'kabul_edildi': 
                return {'success': False, 'message': 'Zaten arkadaşsınız! '}
            elif mevcut.durum == 'beklemede':
                return {'success': False, 'message': 'Zaten bekleyen bir istek var!'}
            elif mevcut.durum == 'reddedildi':
                # Reddedilen isteği tekrar aktif et
                mevcut.durum = 'beklemede'
                mevcut.gonderen = gonderen
                mevcut.alan = alan
                mevcut.save()
        else:
            # Yeni istek oluştur
            mevcut = Arkadaslik.objects.create(
                gonderen=gonderen,
                alan=alan,
                durum='beklemede'
            )
        
        # Bildirim gönder
        bildirim_gonder(
            kullanici=alan,
            tip='sistem',
            baslik='👥 Yeni Arkadaşlık İsteği',
            mesaj=f'{gonderen.username} sana arkadaşlık isteği gönderdi! ',
            icon='👥'
        )
        
        logger.info(f"Arkadaşlık isteği:  {gonderen.username} → {alan.username}")
        return {'success': True, 'message': 'Arkadaşlık isteği gönderildi!'}
        
    except Exception as e:
        logger.error(f"Arkadaşlık isteği hatası: {e}", exc_info=True)
        return {'success': False, 'message': 'Bir hata oluştu! '}


def arkadaslik_istegi_kabul_et(istek_id, kullanici):
    """Arkadaşlık isteğini kabul et"""
    try:
        istek = Arkadaslik.objects.get(id=istek_id, alan=kullanici, durum='beklemede')
        istek.durum = 'kabul_edildi'
        istek.save()
        
        # Bildirim gönder
        bildirim_gonder(
            kullanici=istek.gonderen,
            tip='basari',
            baslik='✅ Arkadaşlık Kabul Edildi',
            mesaj=f'{kullanici.username} arkadaşlık isteğini kabul etti!',
            icon='🎉'
        )
        
        logger.info(f"Arkadaşlık kabul:  {istek.gonderen.username} ↔ {kullanici.username}")
        return {'success': True, 'message': 'Arkadaşlık isteği kabul edildi!'}
        
    except Arkadaslik.DoesNotExist:
        return {'success': False, 'message': 'İstek bulunamadı! '}
    except Exception as e: 
        logger.error(f"Arkadaşlık kabul hatası: {e}", exc_info=True)
        return {'success': False, 'message': 'Bir hata oluştu!'}


def arkadaslik_istegi_reddet(istek_id, kullanici):
    """Arkadaşlık isteğini reddet"""
    try:
        istek = Arkadaslik.objects.get(id=istek_id, alan=kullanici, durum='beklemede')
        istek.durum = 'reddedildi'
        istek.save()
        
        logger.info(f"Arkadaşlık reddedildi: {istek.gonderen.username} X {kullanici.username}")
        return {'success': True, 'message': 'Arkadaşlık isteği reddedildi!'}
        
    except Arkadaslik.DoesNotExist:
        return {'success': False, 'message': 'İstek bulunamadı!'}
    except Exception as e:
        logger.error(f"Arkadaşlık reddetme hatası: {e}", exc_info=True)
        return {'success': False, 'message': 'Bir hata oluştu!'}


def arkadasliktan_cikar(kullanici, arkadas):
    """Arkadaşlıktan çıkar"""
    try:
        istek = Arkadaslik.objects.filter(
            models.Q(gonderen=kullanici, alan=arkadas) |
            models.Q(gonderen=arkadas, alan=kullanici),
            durum='kabul_edildi'
        ).first()
        
        if istek:
            istek.delete()
            logger.info(f"Arkadaşlık silindi: {kullanici.username} X {arkadas.username}")
            return {'success': True, 'message': 'Arkadaşlıktan çıkarıldı!'}
        else: 
            return {'success': False, 'message': 'Arkadaşlık bulunamadı!'}
            
    except Exception as e:
        logger.error(f"Arkadaşlıktan çıkarma hatası: {e}", exc_info=True)
        return {'success':  False, 'message': 'Bir hata oluştu!'}