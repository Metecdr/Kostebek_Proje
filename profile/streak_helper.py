from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


def streak_guncelle(profil):
    """
    Her soru çözümünde çağrılır. Streak'i günceller.
    Returns: dict
    """
    bugun = timezone.now().date()
    son_aktif = profil.son_aktif_tarih  # modelde bu alan varsa

    # Eğer modelde ardasik_gun_sayisi varsa onu kullanalım
    onceki_seri = getattr(profil, 'ardasik_gun_sayisi', 0)
    seri_artti = False
    seri_kirildi = False

    try:
        if son_aktif is None:
            profil.ardasik_gun_sayisi = 1
            seri_artti = True
        elif son_aktif == bugun:
            pass  # Bugün zaten aktif
        elif (bugun - son_aktif).days == 1:
            profil.ardasik_gun_sayisi = onceki_seri + 1
            seri_artti = True
        else:
            seri_kirildi = onceki_seri > 0
            profil.ardasik_gun_sayisi = 1

        # En uzun seriyi güncelle
        mevcut_seri = getattr(profil, 'ardasik_gun_sayisi', 1)
        en_uzun = getattr(profil, 'en_uzun_streak', 0)
        if mevcut_seri > en_uzun:
            profil.en_uzun_streak = mevcut_seri

        profil.son_aktif_tarih = bugun
        profil.save(update_fields=[
            'ardasik_gun_sayisi', 'en_uzun_streak', 'son_aktif_tarih'
        ])

        # Bildirim gönder (milestone günlerde)
        _streak_bildirimi_gonder(profil, seri_artti, seri_kirildi, onceki_seri)

        logger.info(
            f"Streak güncellendi: Kullanıcı={profil.kullanici.username}, "
            f"Seri={profil.ardasik_gun_sayisi}, Arttı={seri_artti}"
        )

    except Exception as e:
        logger.error(f"Streak güncelleme hatası: {e}", exc_info=True)

    return {
        'mevcut_seri': getattr(profil, 'ardasik_gun_sayisi', 0),
        'en_uzun_seri': getattr(profil, 'en_uzun_streak', 0),
        'seri_artti': seri_artti,
        'seri_kirildi': seri_kirildi,
        'onceki_seri': onceki_seri,
    }


def streak_ikonu_al(seri):
    """Seri sayısına göre ikon döndürür."""
    if seri == 0:   return '💤'
    elif seri < 3:  return '🔥'
    elif seri < 7:  return '🔥🔥'
    elif seri < 14: return '🔥🔥🔥'
    elif seri < 30: return '⚡'
    elif seri < 60: return '💎'
    else:           return '👑'


def streak_unvani_al(seri):
    """Seri sayısına göre unvan döndürür."""
    if seri == 0:   return 'Pasif'
    elif seri < 3:  return 'Başlangıç'
    elif seri < 7:  return 'İstikrarlı'
    elif seri < 14: return 'Kararlı'
    elif seri < 30: return 'Azimli'
    elif seri < 60: return 'Efsane'
    else:           return 'Yenilmez 👑'


def _streak_bildirimi_gonder(profil, seri_artti, seri_kirildi, onceki_seri):
    """Milestone veya kırılma bildirimlerini gönderir."""
    try:
        from profile.models import Bildirim
        mevcut = getattr(profil, 'ardasik_gun_sayisi', 0)

        if seri_kirildi and onceki_seri >= 3:
            Bildirim.objects.create(
                kullanici=profil.kullanici,
                baslik='Seriniz Kırıldı! 💔',
                mesaj=f'{onceki_seri} günlük seriniz kırıldı. Yeniden başlayın! 🔥',
                tip='sistem',
            )
        elif seri_artti and mevcut in [3, 7, 14, 30, 60, 100]:
            Bildirim.objects.create(
                kullanici=profil.kullanici,
                baslik=f'{mevcut} Günlük Seri! 🔥',
                mesaj=f'Tebrikler! {mevcut} gün üst üste çalıştınız! {streak_ikonu_al(mevcut)}',
                tip='sistem',
            )
    except Exception as e:
        logger.error(f"Streak bildirimi gönderilemedi: {e}")