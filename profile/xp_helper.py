from profile.models import OgrenciProfili
from profile.bildirim_helper import bildirim_gonder
import logging

logger = logging.getLogger(__name__)


def xp_ekle(profil, miktar, sebep=''):
    try:
        sonuc = profil.xp_ekle(miktar)

        # ==================== XP GEÇMİŞİ KAYDET ====================
        try:
            from profile.models import XPGecmisi
            XPGecmisi.objects.create(
                profil=profil,
                miktar=miktar,
                sebep=sebep
            )
        except Exception as e:
            logger.error(f"XP geçmişi kayıt hatası: {e}", exc_info=True)

        if sonuc['seviye_atlandi']:
            bildirim_gonder(
                kullanici=profil.kullanici,
                tip='basari',
                baslik='🎉 SEVİYE ATLADIN!',
                mesaj=(
                    f'Tebrikler! Seviye {sonuc["yeni_seviye"]} oldun! '
                    f'Yeni unvanın: {sonuc["unvan"]}'
                ),
                icon='🚀'
            )
            logger.info(
                f"Seviye atlandı: {profil.kullanici.username} - "
                f"Seviye {sonuc['eski_seviye']} → {sonuc['yeni_seviye']}"
            )

        logger.info(f"XP eklendi: {profil.kullanici.username} +{miktar} XP - Sebep: {sebep}")
        return sonuc

    except Exception as e:
        logger.error(f"XP ekleme hatası: {profil.kullanici.username}, Hata: {e}", exc_info=True)
        return {'seviye_atlandi': False, 'error': str(e)}


# ==================== HAZIR XP FONKSİYONLARI ====================

def soru_cozuldu_xp(profil, dogru_mu):
    miktar = 5 if dogru_mu else 1
    try:
        from profile.streak_helper import streak_guncelle
        streak_guncelle(profil)
    except Exception as e:
        logger.error(f"Streak güncelleme hatası: {profil.kullanici.username}, Hata: {e}", exc_info=True)
    return xp_ekle(profil, miktar, f'Soru çözüldü ({"Doğru" if dogru_mu else "Yanlış"})')


def gunluk_giris_xp(profil, bonus_xp=20):
    return xp_ekle(profil, bonus_xp, f'Günlük giriş bonusu ({bonus_xp} XP)')


def arkadas_eklendi_xp(profil):
    return xp_ekle(profil, 50, 'Arkadaş eklendi')


def rozet_kazanildi_xp(profil):
    return xp_ekle(profil, 100, 'Rozet kazanıldı')


def tabu_oynandi_xp(profil):
    return xp_ekle(profil, 15, 'Tabu oyunu')


def karsilasma_kazanildi_xp(profil):
    return xp_ekle(profil, 30, 'Karşılaşma kazanıldı')


def bul_bakalim_tamamlandi_xp(profil):
    return xp_ekle(profil, 25, 'Bul Bakalım tamamlandı')