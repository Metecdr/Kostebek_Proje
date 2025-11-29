import random
import logging
from django.core.cache import cache
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from quiz.models import Soru
from profile.models import OyunModuIstatistik

logger = logging.getLogger(__name__)


def get_random_soru_by_ders(ders='karisik'):
    """Seçilen derse göre rastgele soru getir"""
    logger.debug(f"Soru aranıyor: Ders={ders}")
    cache_key = f'karsilasma_soru_ids_{ders}'
    soru_ids = cache.get(cache_key)
    
    if soru_ids is None:
        if ders == 'karisik':
            soru_ids = list(Soru.objects.filter(karsilasmada_cikar=True).values_list('id', flat=True))
        else:
            soru_ids = list(Soru.objects.filter(ders=ders, karsilasmada_cikar=True).values_list('id', flat=True))
        cache.set(cache_key, soru_ids, 300)
        logger.debug(f"Soru ID'leri cache'lendi: Ders={ders}, Sayı={len(soru_ids)}")
    
    if soru_ids:
        random_id = random.choice(soru_ids)
        soru = Soru.objects. get(id=random_id)
        logger.debug(f"Soru seçildi: ID={random_id}, Ders={ders}")
        return soru
    
    logger.warning(f"Hiç soru bulunamadı: Ders={ders}")
    return None


def update_stats_with_combo(user, oda, cevap_obj, is_oyuncu1):
    """Combo ve hız bonusu ile istatistik güncelle"""
    try:
        profil = user.profil
        base_puan = 10
        bonus_puan = 0
        
        if is_oyuncu1 and oda.oyuncu1_cevap_zamani and oda.soru_baslangic_zamani:
            sure = (oda.oyuncu1_cevap_zamani - oda.soru_baslangic_zamani).total_seconds()
            if sure < 5:
                bonus_puan += 5
                logger.debug(f"Hız bonusu: Kullanıcı={user.username}, Süre={sure:.1f}s")
        elif not is_oyuncu1 and oda.oyuncu2_cevap_zamani and oda.soru_baslangic_zamani:
            sure = (oda.oyuncu2_cevap_zamani - oda.soru_baslangic_zamani).total_seconds()
            if sure < 5:
                bonus_puan += 5
                logger. debug(f"Hız bonusu: Kullanıcı={user.username}, Süre={sure:.1f}s")
        
        if cevap_obj.dogru_mu:
            if is_oyuncu1:
                oda.oyuncu1_combo += 1
                combo = oda.oyuncu1_combo
                oda.oyuncu1_dogru += 1
            else:
                oda.oyuncu2_combo += 1
                combo = oda.oyuncu2_combo
                oda.oyuncu2_dogru += 1
            
            combo_bonus = min(combo * 2, 20)
            bonus_puan += combo_bonus
            logger.debug(f"Combo bonusu: Kullanıcı={user.username}, Combo={combo}, Bonus={combo_bonus}")
            
            if oda.ilk_dogru_cevaplayan is None:
                oda.ilk_dogru_cevaplayan = user
                bonus_puan += 3
                logger.debug(f"İlk doğru bonusu: Kullanıcı={user.username}")
            
            toplam_puan = base_puan + bonus_puan
            
            if is_oyuncu1:
                oda.oyuncu1_skor += toplam_puan
            else:
                oda.oyuncu2_skor += toplam_puan
            
            profil.toplam_dogru += 1
            profil.haftalik_dogru += 1
            profil.cozulen_soru_sayisi += 1
            profil.haftalik_cozulen += 1
            profil.toplam_puan += toplam_puan
            profil.haftalik_puan += toplam_puan
            profil.save()
            
            oyun_ist, created = OyunModuIstatistik.objects.get_or_create(profil=profil, oyun_modu='karsilasma')
            oyun_ist.cozulen_soru += 1
            oyun_ist.dogru_sayisi += 1
            oyun_ist.toplam_puan += toplam_puan
            oyun_ist.save()
            
            logger.info(f"İstatistik güncellendi: Kullanıcı={user.username}, Puan={toplam_puan}, Doğru=True")
        else:
            if is_oyuncu1:
                oda.oyuncu1_combo = 0
                oda. oyuncu1_yanlis += 1
            else:
                oda.oyuncu2_combo = 0
                oda.oyuncu2_yanlis += 1
            
            logger.debug(f"Yanlış cevap: Kullanıcı={user.username}, Combo sıfırlandı")
            
            profil.toplam_yanlis += 1
            profil.haftalik_yanlis += 1
            profil.cozulen_soru_sayisi += 1
            profil.haftalik_cozulen += 1
            profil.save()
            
            oyun_ist, created = OyunModuIstatistik.objects. get_or_create(profil=profil, oyun_modu='karsilasma')
            oyun_ist.cozulen_soru += 1
            oyun_ist.yanlis_sayisi += 1
            oyun_ist.save()
        
        cache_key = f'karsilasma_ist_{profil.id}'
        cache. delete(cache_key)
    
    except AttributeError as e:
        logger.error(f"Profil erişim hatası: Kullanıcı={user. username}, Hata={e}", exc_info=True)
    except IntegrityError as e:
        logger.error(f"Veritabanı bütünlük hatası: Kullanıcı={user.username}, Hata={e}", exc_info=True)
    except ValidationError as e:
        logger.error(f"Validasyon hatası: Kullanıcı={user.username}, Hata={e}", exc_info=True)
    except Exception as e:
        logger.error(f"İstatistik güncelleme beklenmeyen hata: Kullanıcı={user.username}, Hata={e}", exc_info=True)