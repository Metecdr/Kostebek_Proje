from django.utils import timezone
import random
import logging

logger = logging.getLogger(__name__)


def gunluk_gorevleri_ata(profil):
    """
    Kullanıcıya günlük 3 görev ata.
    Eğer bugün zaten atanmışsa tekrar atama.
    """
    from profile.models import GunlukGorevSablonu, KullaniciGunlukGorev
    
    bugun = timezone.now().date()
    
    # Bugün zaten görev atanmış mı?
    mevcut_gorev_sayisi = KullaniciGunlukGorev.objects.filter(
        profil=profil,
        tarih=bugun
    ).count()
    
    if mevcut_gorev_sayisi >= 3:
        return KullaniciGunlukGorev.objects.filter(profil=profil, tarih=bugun)
    
    # Aktif şablonları al
    aktif_sablonlar = list(GunlukGorevSablonu.objects.filter(aktif_mi=True))
    
    if len(aktif_sablonlar) < 3:
        logger.warning(f"Yeterli aktif görev şablonu yok! Mevcut: {len(aktif_sablonlar)}")
        secilen_sablonlar = aktif_sablonlar
    else:
        # Zorluk dengesine göre seç: 1 kolay, 1 orta, 1 zor
        kolay = [s for s in aktif_sablonlar if s.zorluk == 'kolay']
        orta = [s for s in aktif_sablonlar if s.zorluk == 'orta']
        zor = [s for s in aktif_sablonlar if s.zorluk == 'zor']
        
        secilen_sablonlar = []
        
        if kolay:
            secilen_sablonlar.append(random.choice(kolay))
        if orta:
            secilen_sablonlar.append(random.choice(orta))
        if zor:
            secilen_sablonlar.append(random.choice(zor))
        
        # Yeterli görev yoksa kalanları rastgele doldur
        while len(secilen_sablonlar) < 3 and len(secilen_sablonlar) < len(aktif_sablonlar):
            kalan = [s for s in aktif_sablonlar if s not in secilen_sablonlar]
            if kalan:
                secilen_sablonlar.append(random.choice(kalan))
            else:
                break
    
    # Görevleri oluştur
    olusturulan = []
    for sablon in secilen_sablonlar:
        gorev, created = KullaniciGunlukGorev.objects.get_or_create(
            profil=profil,
            sablon=sablon,
            tarih=bugun,
            defaults={'mevcut_ilerleme': 0, 'tamamlandi_mi': False}
        )
        if created:
            olusturulan.append(gorev)
    
    logger.info(f"Günlük görevler atandı: {profil.kullanici.username} - {len(olusturulan)} görev")
    return KullaniciGunlukGorev.objects.filter(profil=profil, tarih=bugun)


def gorev_ilerleme_guncelle(profil, gorev_tipi, miktar=1):
    """
    Belirli tipteki görevlerin ilerlemesini güncelle.
    Soru çözme, oyun oynama gibi olaylar olduğunda çağrılır.
    
    Args:
        profil: OgrenciProfili instance
        gorev_tipi: 'soru_coz', 'dogru_cevap', 'bul_bakalim_oyna' vb.
        miktar: Eklenecek ilerleme miktarı
    
    Returns:
        list: Tamamlanan görevler listesi
    """
    from profile.models import KullaniciGunlukGorev
    
    bugun = timezone.now().date()
    tamamlanan_gorevler = []
    
    try:
        # Bugünkü ilgili görevleri bul
        bugunun_gorevleri = KullaniciGunlukGorev.objects.filter(
            profil=profil,
            tarih=bugun,
            tamamlandi_mi=False,
            sablon__gorev_tipi=gorev_tipi,
            sablon__aktif_mi=True
        ).select_related('sablon')
        
        for gorev in bugunun_gorevleri:
            tamamlandi = gorev.ilerleme_guncelle(miktar)
            if tamamlandi:
                # Ödülü ver
                gorev.odulu_ver()
                tamamlanan_gorevler.append(gorev)
                logger.info(
                    f"Görev tamamlandı: {profil.kullanici.username} - "
                    f"{gorev.sablon.isim} (+{gorev.sablon.odul_xp} XP)"
                )
        
        return tamamlanan_gorevler
    
    except Exception as e:
        logger.error(f"Görev ilerleme güncelleme hatası: {profil.kullanici.username}, Hata={e}", exc_info=True)
        return []


def bugunun_gorevlerini_getir(profil):
    """
    Bugünkü görevleri getir. Yoksa ata.
    
    Returns:
        QuerySet: Bugünkü görevler
    """
    from profile.models import KullaniciGunlukGorev
    
    bugun = timezone.now().date()
    
    gorevler = KullaniciGunlukGorev.objects.filter(
        profil=profil,
        tarih=bugun
    ).select_related('sablon')
    
    if not gorevler.exists():
        gorevler = gunluk_gorevleri_ata(profil)
    
    return gorevler


def calisma_kaydi_guncelle(profil, cozulen=0, dogru=0, yanlis=0, xp=0, oyun=0):
    """
    Günlük çalışma kaydını güncelle (takvim için).
    
    Args:
        profil: OgrenciProfili instance
        cozulen: Çözülen soru sayısı
        dogru: Doğru sayısı
        yanlis: Yanlış sayısı
        xp: Kazanılan XP
        oyun: Oynanan oyun sayısı
    """
    from profile.models import CalismaKaydi
    
    bugun = timezone.now().date()
    
    try:
        kayit, created = CalismaKaydi.objects.get_or_create(
            profil=profil,
            tarih=bugun,
            defaults={
                'cozulen_soru': 0,
                'dogru_sayisi': 0,
                'yanlis_sayisi': 0,
                'kazanilan_xp': 0,
                'oynanan_oyun': 0,
            }
        )
        
        kayit.cozulen_soru += cozulen
        kayit.dogru_sayisi += dogru
        kayit.yanlis_sayisi += yanlis
        kayit.kazanilan_xp += xp
        kayit.oynanan_oyun += oyun
        kayit.save()
        
        return kayit
    
    except Exception as e:
        logger.error(f"Çalışma kaydı güncelleme hatası: {profil.kullanici.username}, Hata={e}", exc_info=True)
        return None


def son_n_gun_calisma(profil, gun_sayisi=30):
    """
    Son N günün çalışma verilerini getir (takvim için).
    
    Returns:
        dict: {tarih: CalismaKaydi} formatında
    """
    from profile.models import CalismaKaydi
    
    bugun = timezone.now().date()
    baslangic = bugun - timezone.timedelta(days=gun_sayisi - 1)
    
    kayitlar = CalismaKaydi.objects.filter(
        profil=profil,
        tarih__gte=baslangic,
        tarih__lte=bugun
    )
    
    # Tarihe göre dict oluştur
    kayit_dict = {kayit.tarih: kayit for kayit in kayitlar}
    
    # Tüm günleri doldur (olmayan günler için None)
    sonuc = []
    for i in range(gun_sayisi - 1, -1, -1):
        tarih = bugun - timezone.timedelta(days=i)
        kayit = kayit_dict.get(tarih)
        sonuc.append({
            'tarih': tarih,
            'tarih_str': tarih.strftime('%d.%m'),
            'kayit': kayit,
            'seviye': kayit.aktiflik_seviyesi if kayit else 0,
            'cozulen': kayit.cozulen_soru if kayit else 0,
        })
    
    return sonuc