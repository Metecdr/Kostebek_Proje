from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.contrib import messages
from .models import OgrenciProfili, OyunModuIstatistik, DersIstatistik, Rozet, KonuIstatistik
from quiz.models import Rozet, KullaniciRozet, Soru, KullaniciCevap
from django.db.models import F, Q, Count, Sum
from .rozet_kontrol import rozet_kontrol_yap
from profile.rozet_aciklama import ROZET_ACIKLAMALARI
from profile.models import Rozet
from django.core.cache import cache  # ✅ EKLE
from django.db import transaction  # ✅ EKLE

# ==================== ANASAYFA ====================

def anasayfa(request):
    """Ana sayfa"""
    return render(request, 'giris_sayfasi.html')


# ==================== OTURUM YÖNETİMİ ====================

def kayit_view(request):
    """Kullanıcı kayıt sayfası"""
    
    if request.method == 'POST':
        kullanici_adi = request.POST.get('username')
        email = request.POST.get('email')
        sifre = request.POST.get('password')
        sifre_tekrar = request.POST.get('password2')
        
        # Validasyon kontrolleri (aynı)
        if not kullanici_adi or not email or not sifre or not sifre_tekrar:
            messages.error(request, 'Tüm alanları doldurun!')
            return render(request, 'kayit.html')
        
        if sifre != sifre_tekrar:
            messages.error(request, 'Şifreler eşleşmiyor!')
            return render(request, 'kayit.html')
        
        if User.objects.filter(username=kullanici_adi).exists():
            messages.error(request, 'Bu kullanıcı adı zaten alınmış!')
            return render(request, 'kayit.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Bu email zaten kayıtlı!')
            return render(request, 'kayit.html')
        
        if len(sifre) < 6:
            messages.error(request, 'Şifre en az 6 karakter olmalı!')
            return render(request, 'kayit.html')
        
        try:
            # ✅ Transaction içinde kullanıcı ve profil oluştur
            with transaction.atomic():
                user = User.objects.create_user(
                    username=kullanici_adi,
                    email=email,
                    password=sifre
                )
                
                profil, created = OgrenciProfili.objects.get_or_create(
                    kullanici=user,
                    defaults={'alan': 'sayisal'}
                )
                
                if created:
                    yeni_rozetler = rozet_kontrol_yap(profil)
                else:
                    yeni_rozetler = []
                
                login(request, user)
                
                if yeni_rozetler:
                    messages.success(request, f'🎉 Hoş geldin {kullanici_adi}! {len(yeni_rozetler)} rozet kazandın!')
                else:
                    messages.success(request, f'Hoş geldin {kullanici_adi}! Kayıt başarılı!')
                
                return redirect('profil')
        
        except Exception as e:
            messages.error(request, f'Kayıt sırasında bir hata oluştu: {str(e)}')
            return render(request, 'kayit.html')
    
    return render(request, 'kayit.html')


# ==================== GİRİŞ ====================

def giris_view(request):
    """Kullanıcı giriş sayfası"""

    if request.method == 'POST':
        kullanici_adi = request.POST.get('username')
        sifre = request.POST.get('password')

        user = authenticate(request, username=kullanici_adi, password=sifre)

        if user is not None:
            login(request, user)
            messages.success(request, f'Hoş geldin {kullanici_adi}!')
            return redirect('profil')
        else:
            messages.error(request, 'Kullanıcı adı veya şifre hatalı!')

    return render(request, 'giris.html')


# ==================== ÇIKIŞ ====================

@login_required
def cikis_view(request):
    """Kullanıcı çıkış - Optimized"""
    
    # ✅ Kullanıcıya ait cache'leri temizle
    try:
        profil = request.user.profil
        cache_keys = [
            f'rozet_kontrol_{profil.id}_{profil.cozulen_soru_sayisi}',
            f'oyun_ist_{profil.id}',
            f'ders_ist_{profil.id}',
            f'liderlik_sira_{profil.id}_{profil.toplam_puan}',
            f'rozetler_view_{request.user.id}',
            f'karsilasma_ist_{profil.id}',
        ]
        for key in cache_keys:
            cache.delete(key)
    except:
        pass
    
    logout(request)
    messages.success(request, 'Başarıyla çıkış yaptın!')
    return redirect('giris')


# ==================== PROFİL ====================

@login_required
def profil_view(request):
    """Kullanıcı profil sayfası - Optimized"""
    
    # ✅ select_related ile kullanıcıyı önceden çek
    try:
        profil = OgrenciProfili.objects.select_related('kullanici').get(kullanici=request.user)
    except OgrenciProfili.DoesNotExist:
        profil = OgrenciProfili.objects.create(kullanici=request.user, alan='sayisal')
    
    # ✅ Cache'den rozet kontrolü durumunu al
    cache_key = f'rozet_kontrol_{profil.id}_{profil.cozulen_soru_sayisi}'
    yeni_rozetler = cache.get(cache_key)
    
    if yeni_rozetler is None:
        try:
            yeni_rozetler = rozet_kontrol_yap(profil)
            cache.set(cache_key, yeni_rozetler, 300)  # 5 dakika
            
            if yeni_rozetler:
                for rozet in yeni_rozetler:
                    messages.success(request, f'🏆 Yeni rozet kazandın: {rozet.icon} {rozet.get_kategori_display()} ({rozet.get_seviye_display()})!')
        except Exception as e:
            print(f"❌ Rozet kontrol hatası: {e}")
            yeni_rozetler = []
    
    # ✅ Kullanıcının rozetleri (select_related eklendi)
    kullanici_rozetleri = Rozet.objects.filter(profil=profil).select_related('profil__kullanici').order_by('-kazanilma_tarihi')[:10]
    
    # ✅ Oyun modu istatistikleri (select_related + cache)
    cache_key_oyun = f'oyun_ist_{profil.id}'
    oyun_istatistikleri = cache.get(cache_key_oyun)
    
    if oyun_istatistikleri is None:
        oyun_istatistikleri = OyunModuIstatistik.objects.filter(profil=profil).select_related('profil')
        cache.set(cache_key_oyun, list(oyun_istatistikleri), 60)  # 1 dakika
    
    # ✅ Ders istatistikleri (cache)
    cache_key_ders = f'ders_ist_{profil.id}'
    ders_istatistikleri = cache.get(cache_key_ders)
    
    if ders_istatistikleri is None:
        ders_istatistikleri = DersIstatistik.objects.filter(profil=profil).select_related('profil').order_by('-toplam_puan')[:5]
        cache.set(cache_key_ders, list(ders_istatistikleri), 60)
    
    # ✅ Liderlik sırası (cache)
    cache_key_sira = f'liderlik_sira_{profil.id}_{profil.toplam_puan}'
    kullanici_sira = cache.get(cache_key_sira)
    
    if kullanici_sira is None:
        kullanici_sira = OgrenciProfili.objects.filter(toplam_puan__gt=profil.toplam_puan).count() + 1
        cache.set(cache_key_sira, kullanici_sira, 120)  # 2 dakika
    
    context = {
        'profil': profil,
        'kullanici_rozetleri': kullanici_rozetleri,
        'oyun_istatistikleri': oyun_istatistikleri,
        'ders_istatistikleri': ders_istatistikleri,
        'kullanici_sira': kullanici_sira,
    }
    
    return render(request, 'profil.html', context)


@login_required
def profil_duzenle_view(request):
    """Profil düzenleme sayfası - Optimized"""
    
    # ✅ select_related ile kullanıcıyı önceden çek
    try:
        profil = OgrenciProfili.objects.select_related('kullanici').get(kullanici=request.user)
    except OgrenciProfili.DoesNotExist:
        profil = OgrenciProfili.objects.create(kullanici=request.user, alan='sayisal')
    
    if request.method == 'POST':
        alan = request.POST.get('alan')
        profil_fotografi = request.FILES.get('profil_fotografi')
        
        # ✅ Transaction içinde güncelle
        with transaction.atomic():
            if alan:
                profil.alan = alan
            
            if profil_fotografi:
                profil.profil_fotografi = profil_fotografi
            
            profil.save()
            
            # ✅ Cache'i temizle
            cache_keys = [
                f'rozet_kontrol_{profil.id}_{profil.cozulen_soru_sayisi}',
                f'oyun_ist_{profil.id}',
                f'ders_ist_{profil.id}',
                f'liderlik_sira_{profil.id}_{profil.toplam_puan}',
                f'rozetler_view_{request.user.id}',
            ]
            for key in cache_keys:
                cache.delete(key)
        
        messages.success(request, 'Profil güncellendi!')
        return redirect('profil')
    
    context = {
        'profil': profil,
        'alan_secenekleri': OgrenciProfili.ALAN_SECENEKLERI
    }
    
    return render(request, 'profil_duzenle.html', context)


# ==================== LİDERLİK TABLOSU ====================

@login_required
def liderlik_view(request):
    """Ana Liderlik Sayfası - Optimized"""
    
    # ✅ Cache'den liderlik verilerini al
    cache_key = 'liderlik_ana_sayfa'
    cached_data = cache.get(cache_key)
    
    if cached_data is None:
        # ✅ select_related ve only ile optimizasyon
        genel_liderler = OgrenciProfili.objects.select_related('kullanici').only(
            'kullanici__username', 'toplam_puan', 'haftalik_puan', 'cozulen_soru_sayisi'
        ).order_by('-toplam_puan')[:10]
        
        haftalik_liderler = OgrenciProfili.objects.select_related('kullanici').only(
            'kullanici__username', 'haftalik_puan', 'toplam_puan'
        ).order_by('-haftalik_puan')[:10]
        
        karsilasma_liderler = OyunModuIstatistik.objects.filter(
            oyun_modu='karsilasma'
        ).select_related('profil__kullanici').only(
            'profil__kullanici__username', 'toplam_puan', 'oynanan_oyun_sayisi'
        ).order_by('-toplam_puan')[:10]
        
        matematik_liderler = DersIstatistik.objects.filter(
            ders='matematik'
        ).select_related('profil__kullanici').only(
            'profil__kullanici__username', 'dogru_sayisi', 'cozulen_soru'
        ).order_by('-dogru_sayisi')[:10]
        
        cached_data = {
            'genel_liderler': list(genel_liderler),
            'haftalik_liderler': list(haftalik_liderler),
            'karsilasma_liderler': list(karsilasma_liderler),
            'matematik_liderler': list(matematik_liderler),
        }
        
        cache.set(cache_key, cached_data, 300)  # 5 dakika
    
    # Kullanıcının sırası
    kullanici_profil = request.user.profil
    kullanici_sira = OgrenciProfili.objects.filter(
        toplam_puan__gt=kullanici_profil.toplam_puan
    ).count() + 1
    
    context = {
        'genel_liderler': cached_data['genel_liderler'],
        'haftalik_liderler': cached_data['haftalik_liderler'],
        'karsilasma_liderler': cached_data['karsilasma_liderler'],
        'matematik_liderler': cached_data['matematik_liderler'],
        'kullanici_sira': kullanici_sira,
    }
    
    return render(request, 'liderlik.html', context)


# GENEL LİDERLİK TABLOSU
# ========================================
@login_required
def liderlik_genel_view(request):
    """Genel Liderlik Tablosu - Optimized"""
    
    sirala_tipi = request.GET.get('tip', 'toplam')
    alan_filtresi = request.GET.get('alan', 'genel')
    
    # ✅ Cache key oluştur
    cache_key = f'liderlik_genel_{sirala_tipi}_{alan_filtresi}'
    liderler = cache.get(cache_key)
    
    if liderler is None:
        # Tüm profilleri al
        if alan_filtresi == 'genel':
            liderler = OgrenciProfili.objects.select_related('kullanici').only(
                'kullanici__username', 'toplam_puan', 'haftalik_puan', 'cozulen_soru_sayisi'
            )
        else:
            liderler = OgrenciProfili.objects.select_related('kullanici').filter(
                alan=alan_filtresi
            ).only('kullanici__username', 'toplam_puan', 'haftalik_puan', 'alan')
        
        # Sıralama yap
        if sirala_tipi == 'haftalik':
            liderler = liderler.order_by('-haftalik_puan', '-toplam_puan')[:50]
        else:
            liderler = liderler.order_by('-toplam_puan', '-haftalik_puan')[:50]
        
        liderler = list(liderler)
        cache.set(cache_key, liderler, 180)  # 3 dakika
    
    alan_tercihleri = [
        ('genel', 'Tüm Alanlar'),
        ('sayisal', 'Sayısal'),
        ('sozel', 'Sözel'),
        ('esit_agirlik', 'Eşit Ağırlık'),
        ('dil', 'Dil'),
    ]
    
    context = {
        'liderler': liderler,
        'sirala_tipi': sirala_tipi,
        'alan_filtresi': alan_filtresi,
        'alan_tercihleri': alan_tercihleri,
        'sayfa_baslik': 'Genel Liderlik Tablosu',
    }
    
    return render(request, 'liderlik_genel.html', context)


# ========================================
# OYUN MODU LİDERLİĞİ
# ========================================
@login_required
def liderlik_oyun_modu_view(request):
    """Oyun Modu Bazlı Liderlik - Optimized"""
    
    oyun_modu = request.GET.get('mod', 'karsilasma')
    sirala_tipi = request.GET.get('tip', 'toplam')
    
    # ✅ Cache
    cache_key = f'liderlik_oyun_{oyun_modu}_{sirala_tipi}'
    liderler = cache.get(cache_key)
    
    if liderler is None:
        if sirala_tipi == 'haftalik':
            liderler = OyunModuIstatistik.objects.filter(
                oyun_modu=oyun_modu
            ).select_related('profil__kullanici').only(
                'profil__kullanici__username', 'haftalik_puan', 'toplam_puan', 'oynanan_oyun_sayisi'
            ).order_by('-haftalik_puan', '-toplam_puan')[:50]
        else:
            liderler = OyunModuIstatistik.objects.filter(
                oyun_modu=oyun_modu
            ).select_related('profil__kullanici').only(
                'profil__kullanici__username', 'toplam_puan', 'oynanan_oyun_sayisi'
            ).order_by('-toplam_puan', '-haftalik_puan')[:50]
        
        liderler = list(liderler)
        cache.set(cache_key, liderler, 180)
    
    context = {
        'liderler': liderler,
        'oyun_modu': oyun_modu,
        'sirala_tipi': sirala_tipi,
        'sayfa_baslik': f"{'Karşılaşma' if oyun_modu == 'karsilasma' else 'Bul Bakalım'} Liderliği",
    }
    
    return render(request, 'liderlik_oyun_modu.html', context)


# ========================================
# DERS BAZLI LİDERLİK
# ========================================
@login_required
def liderlik_ders_view(request):
    """Ders Bazlı Liderlik - Optimized"""
    
    ders = request.GET.get('ders', 'matematik')
    sirala = request.GET.get('sirala', 'dogru')
    
    # ✅ Cache
    cache_key = f'liderlik_ders_{ders}_{sirala}'
    liderler = cache.get(cache_key)
    
    if liderler is None:
        if sirala == 'net':
            liderler = DersIstatistik.objects.filter(
                ders=ders
            ).select_related('profil__kullanici').annotate(
                hesaplanan_net=F('dogru_sayisi') - (F('yanlis_sayisi') / 4.0)
            ).order_by('-hesaplanan_net', '-dogru_sayisi')[:50]
        elif sirala == 'oran':
            liderler = DersIstatistik.objects.filter(
                ders=ders,
                cozulen_soru__gte=10
            ).select_related('profil__kullanici').order_by('-dogru_sayisi', '-cozulen_soru')[:50]
        else:
            liderler = DersIstatistik.objects.filter(
                ders=ders
            ).select_related('profil__kullanici').order_by('-dogru_sayisi', '-cozulen_soru')[:50]
        
        liderler = list(liderler)
        cache.set(cache_key, liderler, 180)
    
    ders_listesi = [
        ('matematik', 'Matematik'),
        ('fizik', 'Fizik'),
        ('kimya', 'Kimya'),
        ('biyoloji', 'Biyoloji'),
        ('turkce', 'Türkçe'),
        ('tarih', 'Tarih'),
        ('cografya', 'Coğrafya'),
        ('felsefe', 'Felsefe'),
        ('din', 'Din Kültürü'),
        ('ingilizce', 'İngilizce'),
    ]
    
    context = {
        'liderler': liderler,
        'ders': ders,
        'sirala': sirala,
        'ders_listesi': ders_listesi,
        'ders_adi': dict(ders_listesi).get(ders, ders),
        'sayfa_baslik': f"{dict(ders_listesi).get(ders, ders)} Liderliği",
    }
    
    return render(request, 'liderlik_ders.html', context)


# ========================================
# ANA LİDERLİK SAYFASI (Hepsini Göster)
# ========================================
@login_required
def liderlik_view(request):
    """Ana Liderlik Sayfası - Tüm liderlik türlerini göster"""
    
    # En iyi 10 genel lider
    genel_liderler = OgrenciProfili.objects.order_by('-toplam_puan')[:10]
    
    # En iyi 10 haftalık lider
    haftalik_liderler = OgrenciProfili.objects.order_by('-haftalik_puan')[:10]
    
    # Karşılaşma liderleri
    karsilasma_liderler = OyunModuIstatistik.objects.filter(
        oyun_modu='karsilasma'
    ).order_by('-toplam_puan')[:10]
    
    # Matematik liderleri
    matematik_liderler = DersIstatistik.objects.filter(
        ders='matematik'
    ).order_by('-dogru_sayisi')[:10]
    
    # Kullanıcının sırası
    kullanici_profil = request.user.profil
    kullanici_sira = OgrenciProfili.objects.filter(
        toplam_puan__gt=kullanici_profil.toplam_puan
    ).count() + 1
    
    context = {
        'genel_liderler': genel_liderler,
        'haftalik_liderler': haftalik_liderler,
        'karsilasma_liderler': karsilasma_liderler,
        'matematik_liderler': matematik_liderler,
        'kullanici_sira': kullanici_sira,
    }
    
    return render(request, 'liderlik.html', context)


# ==================== İSTATİSTİKLER ====================

@login_required
def konu_istatistik_view(request):
    """Konu bazlı istatistikler - Optimized"""
    
    # ✅ Cache
    cache_key = f'konu_ist_{request.user.id}'
    konu_istatistikleri = cache.get(cache_key)
    
    if konu_istatistikleri is None:
        from quiz.models import KullaniciCevap
        
        konu_istatistikleri = KullaniciCevap.objects.filter(
            kullanici=request.user
        ).values('soru__konu__isim').annotate(
            toplam=Count('id'),
            dogru=Count('id', filter=Q(dogru_mu=True)),
            yanlis=Count('id', filter=Q(dogru_mu=False))
        ).order_by('-toplam')
        
        konu_istatistikleri = list(konu_istatistikleri)
        cache.set(cache_key, konu_istatistikleri, 300)
    
    context = {
        'konu_istatistikleri': konu_istatistikleri,
    }
    
    return render(request, 'konu_istatistik.html', context)


# ====================== KONU ANALİZİ ======================

@login_required
def konu_analiz_view(request):
    """Konu analizi - Optimized"""
    
    # ✅ Cache
    cache_key = f'konu_analiz_{request.user.profil.id}'
    cached_data = cache.get(cache_key)
    
    if cached_data is None:
        profil = request.user.profil
        dersler = ['matematik', 'fizik', 'kimya', 'biyoloji', 'turkce']
        konu_istatistikleri = KonuIstatistik.objects.filter(profil=profil).select_related('profil')
        
        ders_konular_list = []
        for ders in dersler:
            ders_konular_list.append({
                'ders': ders,
                'konular': list(konu_istatistikleri.filter(ders=ders))
            })
        
        cached_data = {
            'dersler': dersler,
            'ders_konular_list': ders_konular_list,
        }
        cache.set(cache_key, cached_data, 300)
    
    return render(request, 'konu_analiz.html', cached_data)

# ==================== ROZETLER ====================

@login_required
def rozetler_view(request):
    """Kullanıcının rozetlerini göster - Optimized"""
    
    # ✅ Cache'den rozet verilerini al
    cache_key = f'rozetler_view_{request.user.id}'
    cached_context = cache.get(cache_key)
    
    if cached_context is None:
        try:
            profil = OgrenciProfili.objects.select_related('kullanici').get(kullanici=request.user)
        except OgrenciProfili.DoesNotExist:
            profil = OgrenciProfili.objects.create(kullanici=request.user, alan='sayisal')
        
        # ✅ Kazanılan rozetler (optimize edildi)
        kazanilan_rozetler = Rozet.objects.filter(profil=profil).select_related('profil__kullanici').order_by('-kazanilma_tarihi')
        
        # Tüm rozetlerin kategori/seviye kombinasyonunu al
        tum_rozet_tanimi = []
        for kategori, _ in Rozet.KATEGORI_SECENEKLERI:
            for seviye, _ in Rozet.SEVIYE_SECENEKLERI:
                tum_rozet_tanimi.append({'kategori': kategori, 'seviye': seviye})
        
        # Kullanıcının rozetlerini set olarak al
        kazanilan_set = {(r.kategori, r.seviye) for r in kazanilan_rozetler}

        # ✅ İKON MAPPING (cache'lenebilir)
        ICON_MAP = {
            'yeni_uye': '🌱',
            'aktif_kullanici': '⚡',
            'gun_asimi': '📅',
            'hafta_sampionu': '👑',
            'soru_cozucu': '📝',
            'dogru_ustasi': '✅',
            'net_avcisi': '🎯',
            'hatasiz_kusursuz': '💯',
            'matematik_dehasi': '🔢',
            'fizik_profesoru': '⚛️',
            'kimya_uzman': '🧪',
            'biyoloji_bilgini': '🧬',
            'turkce_edebiyatci': '📖',
            'tarih_bilgesi': '🏛️',
            'cografya_gezgini': '🌍',
            'felsefe_dusunuru': '💭',
            'karsilasma_savaslisi': '⚔️',
            'bul_bakalim_ustasi': '💡',
            'tabu_kral': '🎭',
            'galip_aslan': '🦁',
            'lider_zirve': '🏆',
            'top_10': '🥇',
            'top_50': '🥈',
            'zirve_fatih': '👑',
            'hizli_cevap': '⚡',
            'gece_kusu': '🦉',
            'sabah_kusagu': '🌅',
            'maraton_kosucu': '🏃',
            'yardimci': '🤝',
            'ogretmen': '👨‍🏫',
            'ilham_verici': '✨',
            'takım_oyuncusu': '👥',
        }

        # Kazanılmamış rozetler
        kazanilmamis_rozetler = []
        for tanim in tum_rozet_tanimi:
            if (tanim['kategori'], tanim['seviye']) not in kazanilan_set:
                kategori_kod = tanim['kategori']
                seviye_kod = tanim['seviye']
                
                isim = dict(Rozet.KATEGORI_SECENEKLERI).get(kategori_kod, 'Bilinmeyen')
                emoji = ICON_MAP.get(kategori_kod, '🏅')
                aciklama = ROZET_ACIKLAMALARI.get(kategori_kod, {}).get(seviye_kod, "Açıklama bulunamadı.")
                
                kazanilmamis_rozetler.append({
                    'kategori': kategori_kod,
                    'seviye': seviye_kod,
                    'isim': isim,
                    'emoji': emoji,
                    'aciklama': aciklama
                })
        
        cached_context = {
            'kazanilan_rozetler': list(kazanilan_rozetler),
            'kazanilmamis_rozetler': kazanilmamis_rozetler,
            'kazanilan_sayi': kazanilan_rozetler.count(),
            'toplam_rozet': len(tum_rozet_tanimi),
        }
        
        cache.set(cache_key, cached_context, 180)  # 3 dakika
    
    return render(request, 'rozetler.html', cached_context)