import logging

logger = logging.getLogger(__name__)


def streak_carpani_hesapla(profil):
    """Streak'e göre puan çarpanı hesapla"""
    streak = profil.ardasik_gun_sayisi or 0
    if streak >= 30:
        return 2.0
    elif streak >= 14:
        return 1.5
    elif streak >= 7:
        return 1.25
    elif streak >= 3:
        return 1.1
    return 1.0


def dogruluk_bonusu_hesapla(dogru, toplam):
    """Doğruluk oranına göre bonus yüzdesi hesapla"""
    if toplam == 0:
        return 0
    oran = (dogru / toplam) * 100
    if oran == 100:
        return 0.25   # +%25
    elif oran >= 90:
        return 0.15   # +%15
    elif oran >= 80:
        return 0.10   # +%10
    return 0


def puan_ekle(profil, taban_puan, sebep='', dogru=0, toplam=0):
    """
    Streak çarpanı ve doğruluk bonusu uygulayarak puan ekle.
    Kazanılan puanı döndürür.
    """
    try:
        carpan = streak_carpani_hesapla(profil)
        bonus = dogruluk_bonusu_hesapla(dogru, toplam)

        # Hesapla
        ara_puan = taban_puan * carpan
        bonus_puan = ara_puan * bonus
        toplam_puan = round(ara_puan + bonus_puan)

        profil.toplam_puan += toplam_puan
        profil.haftalik_puan += toplam_puan
        profil.gunluk_puan += toplam_puan
        profil.save()

        logger.info(
            f"Puan eklendi: {profil.kullanici.username} "
            f"Taban={taban_puan} Çarpan=x{carpan} Bonus=+%{int(bonus*100)} "
            f"→ Toplam +{toplam_puan} puan | Sebep: {sebep}"
        )

        return {
            'taban_puan': taban_puan,
            'carpan': carpan,
            'bonus_yuzdesi': int(bonus * 100),
            'kazanilan_puan': toplam_puan,
        }

    except Exception as e:
        logger.error(f"Puan ekleme hatası: {e}", exc_info=True)
        return {'kazanilan_puan': 0}