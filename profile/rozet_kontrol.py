from django.utils import timezone
from datetime import timedelta
from .models import OgrenciProfili, Rozet, DersIstatistik, OyunModuIstatistik
import logging
from profile.bildirim_helper import rozet_bildirimi_gonder

logger = logging.getLogger(__name__)


def rozet_kontrol_yap(profil):
    """
    Kullanıcının tüm rozetlerini kontrol et ve yeni kazandıklarını ver
    """
    yeni_rozetler = []
    
    # GENEL ROZETLER
    yeni_rozetler.extend(genel_rozet_kontrol(profil))
    
    # SORU ÇÖZME ROZETLER
    yeni_rozetler.extend(soru_rozet_kontrol(profil))
    
    # DERS BAZLI ROZETLER
    yeni_rozetler.extend(ders_rozet_kontrol(profil))
    
    # OYUN MODU ROZETLER
    yeni_rozetler.extend(oyun_rozet_kontrol(profil))
    
    # LİDERLİK ROZETLER
    yeni_rozetler.extend(liderlik_rozet_kontrol(profil))

    # ✅ YENİ ROZETLER İÇİN BİLDİRİM GÖNDER
    for rozet in yeni_rozetler:
        rozet_bildirimi_gonder(profil.kullanici, rozet)
    
    return yeni_rozetler


def genel_rozet_kontrol(profil):
    """Genel rozetleri kontrol et"""
    yeni_rozetler = []
    
    # YENİ ÜYE - Çaylak (İlk kayıt - otomatik)
    if not Rozet.objects.filter(profil=profil, kategori='yeni_uye', seviye='caylak').exists():
        rozet = Rozet.objects.create(profil=profil, kategori='yeni_uye', seviye='caylak')
        yeni_rozetler.append(rozet)
        logger.info(f"✅ {profil.kullanici.username} 'Yeni Üye (Çaylak)' rozetini kazandı!")
    
    # YENİ ÜYE - Usta (6 ay = 180 gün)
    if profil.kayit_tarihi:
        gun_farki = (timezone.now() - profil.kayit_tarihi).days
        if gun_farki >= 180:  # ✅ 6 AY
            if not Rozet.objects.filter(profil=profil, kategori='yeni_uye', seviye='usta').exists():
                rozet = Rozet.objects.create(profil=profil, kategori='yeni_uye', seviye='usta')
                yeni_rozetler.append(rozet)
                logger.info(f"✅ {profil.kullanici.username} 'Yeni Üye (Usta)' rozetini kazandı!")
    
    # AKTİF KULLANICI - Çaylak (7 gün üst üste)
    # TODO: Login tracking sistemi gerekli
    
    # GÜN AŞIMI - Çaylak (İlk gün 10 soru)
    if profil.kayit_tarihi:
        kayit_suresi = (timezone.now() - profil.kayit_tarihi).total_seconds() / 3600
        if kayit_suresi <= 24 and profil.cozulen_soru_sayisi >= 10:
            if not Rozet.objects.filter(profil=profil, kategori='gun_asimi', seviye='caylak').exists():
                rozet = Rozet.objects.create(profil=profil, kategori='gun_asimi', seviye='caylak')
                yeni_rozetler.append(rozet)
                logger.info(f"✅ {profil.kullanici.username} 'Gün Aşımı (Çaylak)' rozetini kazandı!")
    
    # GÜN AŞIMI - Usta (İlk gün 50 soru)
    if profil.kayit_tarihi:
        kayit_suresi = (timezone.now() - profil.kayit_tarihi).total_seconds() / 3600
        if kayit_suresi <= 24 and profil.cozulen_soru_sayisi >= 50:
            if not Rozet.objects.filter(profil=profil, kategori='gun_asimi', seviye='usta').exists():
                rozet = Rozet.objects.create(profil=profil, kategori='gun_asimi', seviye='usta')
                yeni_rozetler.append(rozet)
                logger.info(f"✅ {profil.kullanici.username} 'Gün Aşımı (Usta)' rozetini kazandı!")
    
    # HAFTA ŞAMPİYONU - Çaylak (500 haftalık puan)
    if profil.haftalik_puan >= 500:
        if not Rozet.objects.filter(profil=profil, kategori='hafta_sampionu', seviye='caylak').exists():
            rozet = Rozet.objects.create(profil=profil, kategori='hafta_sampionu', seviye='caylak')
            yeni_rozetler.append(rozet)
            logger.info(f"✅ {profil.kullanici.username} 'Hafta Şampiyonu (Çaylak)' rozetini kazandı!")
    
    # HAFTA ŞAMPİYONU - Usta (2000 haftalık puan)
    if profil.haftalik_puan >= 2000:
        if not Rozet.objects.filter(profil=profil, kategori='hafta_sampionu', seviye='usta').exists():
            rozet = Rozet.objects.create(profil=profil, kategori='hafta_sampionu', seviye='usta')
            yeni_rozetler.append(rozet)
            logger.info(f"✅ {profil.kullanici.username} 'Hafta Şampiyonu (Usta)' rozetini kazandı!")
    
    return yeni_rozetler


def soru_rozet_kontrol(profil):
    """Soru çözme rozetlerini kontrol et"""
    yeni_rozetler = []
    
    # SORU ÇÖZÜCÜ - Çaylak (50 soru)
    if profil.cozulen_soru_sayisi >= 50:
        if not Rozet.objects.filter(profil=profil, kategori='soru_cozucu', seviye='caylak').exists():
            rozet = Rozet.objects.create(profil=profil, kategori='soru_cozucu', seviye='caylak')
            yeni_rozetler.append(rozet)
            logger.info(f"✅ {profil.kullanici.username} 'Soru Çözücü (Çaylak)' rozetini kazandı!")
    
    # SORU ÇÖZÜCÜ - Usta (500 soru)
    if profil.cozulen_soru_sayisi >= 500:
        if not Rozet.objects.filter(profil=profil, kategori='soru_cozucu', seviye='usta').exists():
            rozet = Rozet.objects.create(profil=profil, kategori='soru_cozucu', seviye='usta')
            yeni_rozetler.append(rozet)
            logger.info(f"✅ {profil.kullanici.username} 'Soru Çözücü (Usta)' rozetini kazandı!")
    
    # DOĞRU USTASI - Çaylak (30 doğru)
    if profil.toplam_dogru >= 30:
        if not Rozet.objects.filter(profil=profil, kategori='dogru_ustasi', seviye='caylak').exists():
            rozet = Rozet.objects.create(profil=profil, kategori='dogru_ustasi', seviye='caylak')
            yeni_rozetler.append(rozet)
            logger.info(f"✅ {profil.kullanici.username} 'Doğru Ustası (Çaylak)' rozetini kazandı!")
    
    # DOĞRU USTASI - Usta (300 doğru)
    if profil.toplam_dogru >= 300:
        if not Rozet.objects.filter(profil=profil, kategori='dogru_ustasi', seviye='usta').exists():
            rozet = Rozet.objects.create(profil=profil, kategori='dogru_ustasi', seviye='usta')
            yeni_rozetler.append(rozet)
            logger.info(f"✅ {profil.kullanici.username} 'Doğru Ustası (Usta)' rozetini kazandı!")
    
    # NET AVCISI - Çaylak (20 net)
    toplam_net = profil.toplam_dogru - (profil.toplam_yanlis / 4)
    if toplam_net >= 20:
        if not Rozet.objects.filter(profil=profil, kategori='net_avcisi', seviye='caylak').exists():
            rozet = Rozet.objects.create(profil=profil, kategori='net_avcisi', seviye='caylak')
            yeni_rozetler.append(rozet)
            logger.info(f"✅ {profil.kullanici.username} 'Net Avcısı (Çaylak)' rozetini kazandı!")
    
    # NET AVCISI - Usta (100 net)
    if toplam_net >= 100:
        if not Rozet.objects.filter(profil=profil, kategori='net_avcisi', seviye='usta').exists():
            rozet = Rozet.objects.create(profil=profil, kategori='net_avcisi', seviye='usta')
            yeni_rozetler.append(rozet)
            logger.info(f"✅ {profil.kullanici.username} 'Net Avcısı (Usta)' rozetini kazandı!")
    
        # ✅ DÜZELTİLDİ:  Başarı Oranı Rozeti (METOD ÇAĞRISI)
        if profil.genel_basari_orani() >= 70 and profil.cozulen_soru_sayisi >= 30:
            rozet = Rozet.objects.filter(kod='yuksek_basari').first()
            if rozet and not KazanilanRozet.objects.filter(profil=profil, rozet=rozet).exists():
                KazanilanRozet.objects.create(profil=profil, rozet=rozet)
                kazanilan.append(rozet)
        
        # ✅ DÜZELTİLDİ: Mükemmellik (METOD ÇAĞRISI)
        if profil.genel_basari_orani() >= 90 and profil.cozulen_soru_sayisi >= 100:
            rozet = Rozet.objects.filter(kod='mukemmellik').first()
            if rozet and not KazanilanRozet.objects.filter(profil=profil, rozet=rozet).exists():
                KazanilanRozet.objects.create(profil=profil, rozet=rozet)
                kazanilan.append(rozet)
    
    return yeni_rozetler


def ders_rozet_kontrol(profil):
    """Ders bazlı rozetleri kontrol et"""
    yeni_rozetler = []
    
    ders_rozet_map = {
        'matematik': 'matematik_dehasi',
        'fizik': 'fizik_profesoru',
        'kimya':  'kimya_uzman',
        'biyoloji': 'biyoloji_bilgini',
        'turkce': 'turkce_edebiyatci',
        'tarih': 'tarih_bilgesi',
        'cografya': 'cografya_gezgini',
        'felsefe': 'felsefe_dusunuru',
    }
    
    for ders_kod, rozet_kategori in ders_rozet_map.items():
        try:
            ders_ist = DersIstatistik.objects.get(profil=profil, ders=ders_kod)
            
            # Çaylak:  30 doğru
            if ders_ist.dogru_sayisi >= 30:
                if not Rozet.objects.filter(profil=profil, kategori=rozet_kategori, seviye='caylak').exists():
                    rozet = Rozet.objects.create(profil=profil, kategori=rozet_kategori, seviye='caylak')
                    yeni_rozetler.append(rozet)
                    logger.info(f"✅ {profil.kullanici.username} '{rozet.get_kategori_display()} (Çaylak)' rozetini kazandı!")
            
            # Usta:  150 doğru
            if ders_ist.dogru_sayisi >= 150:
                if not Rozet.objects.filter(profil=profil, kategori=rozet_kategori, seviye='usta').exists():
                    rozet = Rozet.objects.create(profil=profil, kategori=rozet_kategori, seviye='usta')
                    yeni_rozetler.append(rozet)
                    logger.info(f"✅ {profil.kullanici.username} '{rozet.get_kategori_display()} (Usta)' rozetini kazandı!")
        except DersIstatistik.DoesNotExist:
            pass
    
    return yeni_rozetler


def oyun_rozet_kontrol(profil):
    """Oyun modu rozetlerini kontrol et"""
    yeni_rozetler = []
    
    # KARŞILAŞMA SAVAŞÇISI
    try:
        karsilasma = OyunModuIstatistik.objects.get(profil=profil, oyun_modu='karsilasma')
        
        # Çaylak: 5 galibiyet
        if karsilasma.kazanilan_oyun >= 5:
            if not Rozet.objects.filter(profil=profil, kategori='karsilasma_savaslisi', seviye='caylak').exists():
                rozet = Rozet.objects.create(profil=profil, kategori='karsilasma_savaslisi', seviye='caylak')
                yeni_rozetler.append(rozet)
                logger.info(f"✅ {profil.kullanici.username} 'Karşılaşma Savaşçısı (Çaylak)' rozetini kazandı!")
        
        # Usta: 30 galibiyet
        if karsilasma.kazanilan_oyun >= 30:
            if not Rozet.objects.filter(profil=profil, kategori='karsilasma_savaslisi', seviye='usta').exists():
                rozet = Rozet.objects.create(profil=profil, kategori='karsilasma_savaslisi', seviye='usta')
                yeni_rozetler.append(rozet)
                logger.info(f"✅ {profil.kullanici.username} 'Karşılaşma Savaşçısı (Usta)' rozetini kazandı!")
    except OyunModuIstatistik.DoesNotExist:
        pass
    
    # BUL BAKALIM USTASI
    try:
        bul_bakalim = OyunModuIstatistik.objects.get(profil=profil, oyun_modu='bul_bakalim')
        
        # Çaylak: 10 oyun
        if bul_bakalim.oynanan_oyun_sayisi >= 10:
            if not Rozet.objects.filter(profil=profil, kategori='bul_bakalim_ustasi', seviye='caylak').exists():
                rozet = Rozet.objects.create(profil=profil, kategori='bul_bakalim_ustasi', seviye='caylak')
                yeni_rozetler.append(rozet)
                logger.info(f"✅ {profil.kullanici.username} 'Bul Bakalım Ustası (Çaylak)' rozetini kazandı!")
        
        # Usta: 50 oyun
        if bul_bakalim.oynanan_oyun_sayisi >= 50:
            if not Rozet.objects.filter(profil=profil, kategori='bul_bakalim_ustasi', seviye='usta').exists():
                rozet = Rozet.objects.create(profil=profil, kategori='bul_bakalim_ustasi', seviye='usta')
                yeni_rozetler.append(rozet)
                logger.info(f"✅ {profil.kullanici.username} 'Bul Bakalım Ustası (Usta)' rozetini kazandı!")
    except OyunModuIstatistik.DoesNotExist:
        pass
    
    # GALİP ASLAN (%70+ galibiyet, min 10 oyun)
    try:
        karsilasma = OyunModuIstatistik.objects.get(profil=profil, oyun_modu='karsilasma')
        if karsilasma.oynanan_oyun_sayisi >= 10 and karsilasma.galibiyet_orani >= 70:
            if not Rozet.objects.filter(profil=profil, kategori='galip_aslan', seviye='caylak').exists():
                rozet = Rozet.objects.create(profil=profil, kategori='galip_aslan', seviye='caylak')
                yeni_rozetler.append(rozet)
                logger.info(f"✅ {profil.kullanici.username} 'Galip Aslan (Çaylak)' rozetini kazandı!")
        
        if karsilasma.oynanan_oyun_sayisi >= 30 and karsilasma.galibiyet_orani >= 80:
            if not Rozet.objects.filter(profil=profil, kategori='galip_aslan', seviye='usta').exists():
                rozet = Rozet.objects.create(profil=profil, kategori='galip_aslan', seviye='usta')
                yeni_rozetler.append(rozet)
                logger.info(f"✅ {profil.kullanici.username} 'Galip Aslan (Usta)' rozetini kazandı!")
    except OyunModuIstatistik.DoesNotExist:
        pass
    
    return yeni_rozetler


def liderlik_rozet_kontrol(profil):
    """Liderlik rozetlerini kontrol et"""
    yeni_rozetler = []
    
    from profile.models import OgrenciProfili
    tum_profilller = OgrenciProfili.objects.filter(aktif_mi=True).order_by('-toplam_puan')
    
    try:
        sira = list(tum_profilller.values_list('id', flat=True)).index(profil.id) + 1
    except ValueError:
            sira = 99999 # Sıralamada olmayanlar için yüksek bir değer

    # TOP 50
    if sira <= 50:
        if not Rozet.objects.filter(profil=profil, kategori='top_50', seviye='caylak').exists():
            rozet = Rozet.objects.create(profil=profil, kategori='top_50', seviye='caylak')
            yeni_rozetler.append(rozet)
            logger.info(f"✅ {profil.kullanici.username} 'Top 50 (Çaylak)' rozetini kazandı!")
    
    # TOP 10
    if sira <= 10:
        if not Rozet.objects.filter(profil=profil, kategori='top_10', seviye='caylak').exists():
            rozet = Rozet.objects.create(profil=profil, kategori='top_10', seviye='caylak')
            yeni_rozetler.append(rozet)
            logger.info(f"✅ {profil.kullanici.username} 'Top 10 (Çaylak)' rozetini kazandı!")
    
    # LİDER ZİRVE (1. sıra)
    if sira == 1:
        if not Rozet.objects.filter(profil=profil, kategori='lider_zirve', seviye='caylak').exists():
            rozet = Rozet.objects.create(profil=profil, kategori='lider_zirve', seviye='caylak')
            yeni_rozetler.append(rozet)
            logger.info(f"✅ {profil.kullanici.username} 'Lider Zirve (Çaylak)' rozetini kazandı!")
    
    return yeni_rozetler