from profile.models import OgrenciProfili
from profile.bildirim_helper import bildirim_gonder
import logging

logger = logging.getLogger(__name__)


def xp_ekle(profil, miktar, sebep=''):
    """
    Profil XP ekle ve seviye kontrolü yap
    
    Args:  
        profil:  OgrenciProfili instance
        miktar:   Eklenecek XP miktarı
        sebep:   XP kazanma sebebi (log için)
    
    Returns:
        dict:   Seviye atlama bilgisi
    """
    try: 
        sonuc = profil.xp_ekle(miktar)
        
        if sonuc['seviye_atlandi']:
            # Seviye atladı!   Bildirim gönder
            bildirim_gonder(
                kullanici=profil.kullanici,
                tip='basari',
                baslik=f'🎉 SEVİYE ATLADIN! ',
                mesaj=f'Tebrikler!   Seviye {sonuc["yeni_seviye"]} oldun!   Yeni unvanın:   {sonuc["unvan"]}',
                icon='🚀'
            )
            
            logger.info(f"Seviye atlandı: {profil.kullanici.username} - Seviye {sonuc['eski_seviye']} → {sonuc['yeni_seviye']}")
        
        logger.info(f"XP eklendi: {profil.kullanici.username} +{miktar} XP - Sebep: {sebep}")
        return sonuc
        
    except Exception as e:
        logger.error(f"XP ekleme hatası: {profil.kullanici.username}, Hata: {e}", exc_info=True)
        return {'seviye_atlandi':   False, 'error': str(e)}


# ==================== HAZIR XP FONKSİYONLARI ====================

def soru_cozuldu_xp(profil, dogru_mu):
    """Soru çözüldüğünde XP ver - DOĞRU:   5 XP, YANLIŞ: 1 XP"""
    miktar = 5 if dogru_mu else 1
    return xp_ekle(profil, miktar, f'Soru çözüldü ({"Doğru" if dogru_mu else "Yanlış"})')


def gunluk_giris_xp(profil, bonus_xp=20):
    """
    Günlük giriş bonusu - Dinamik XP
    
    Args:
        profil: OgrenciProfili instance
        bonus_xp:   Verilecek XP miktarı (streak'e göre değişir)
    
    Returns:
        dict: Seviye atlama bilgisi
    """
    return xp_ekle(profil, bonus_xp, f'Günlük giriş bonusu ({bonus_xp} XP)')


def arkadas_eklendi_xp(profil):
    """Arkadaş eklendiğinde XP - 50 XP"""
    return xp_ekle(profil, 50, 'Arkadaş eklendi')


def rozet_kazanildi_xp(profil):
    """Rozet kazanıldığında XP - 100 XP"""
    return xp_ekle(profil, 100, 'Rozet kazanıldı')


def tabu_oynandi_xp(profil):
    """Tabu oyunu oynandığında XP - 15 XP"""
    return xp_ekle(profil, 15, 'Tabu oyunu')


def karsilasma_kazanildi_xp(profil):
    """Karşılaşma kazanıldığında XP - 30 XP"""
    return xp_ekle(profil, 30, 'Karşılaşma kazanıldı')


def bul_bakalim_tamamlandi_xp(profil):
    """Bul Bakalım tamamlandığında XP - 25 XP"""
    return xp_ekle(profil, 25, 'Bul Bakalım tamamlandı')