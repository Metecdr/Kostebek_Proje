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

# ==================== ANASAYFA ====================

def anasayfa(request):
    """Ana sayfa"""
    return render(request, 'giris_sayfasi.html')


# ==================== OTURUM YÖNETİMİ ====================

def kayit_view(request):
    """Kullanıcı kayıt sayfası"""
    
    if request.method == 'POST':
        # HTML formdaki name'lere göre al
        kullanici_adi = request.POST.get('username')
        email = request.POST.get('email')
        sifre = request.POST.get('password')
        sifre_tekrar = request.POST.get('password2')
        
        # Validasyon kontrolleri
        if not kullanici_adi or not email or not sifre or not sifre_tekrar:
            messages.error(request, 'Tüm alanları doldurun!')
            return render(request, 'kayit.html')
        
        # Şifre eşleşme kontrolü
        if sifre != sifre_tekrar:
            messages.error(request, 'Şifreler eşleşmiyor!')
            return render(request, 'kayit.html')
        
        # Kullanıcı adı kontrolü
        if User.objects.filter(username=kullanici_adi).exists():
            messages.error(request, 'Bu kullanıcı adı zaten alınmış!')
            return render(request, 'kayit.html')
        
        # Email kontrolü
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Bu email zaten kayıtlı!')
            return render(request, 'kayit.html')
        
        # Şifre uzunluk kontrolü
        if len(sifre) < 6:
            messages.error(request, 'Şifre en az 6 karakter olmalı!')
            return render(request, 'kayit.html')
        
        try:
            # Kullanıcı oluştur
            user = User.objects.create_user(
                username=kullanici_adi,
                email=email,
                password=sifre
            )
            
            # ✅ Profil oluştur veya al (get_or_create)
            profil, created = OgrenciProfili.objects.get_or_create(
                kullanici=user,
                defaults={'alan': 'sayisal'}
            )
            
            # ✅ İLK ROZET KONTROLÜ (sadece yeni profil oluşturulduysa)
            if created:
                from .rozet_kontrol import rozet_kontrol_yap
                yeni_rozetler = rozet_kontrol_yap(profil)
            else:
                yeni_rozetler = []
            
            # Kullanıcıyı otomatik giriş yap
            login(request, user)
            
            # Başarı mesajı
            if yeni_rozetler:
                messages.success(request, f'🎉 Hoş geldin {kullanici_adi}! {len(yeni_rozetler)} rozet kazandın!')
            else:
                messages.success(request, f'Hoş geldin {kullanici_adi}! Kayıt başarılı!')
            
            return redirect('profil')
        
        except Exception as e:
            messages.error(request, f'Kayıt sırasında bir hata oluştu: {str(e)}')
            return render(request, 'kayit.html')
    
    # GET isteği
    return render(request, 'kayit.html')
    
    # GET isteği - kayıt formu göster
    context = {
        'alan_secenekleri': OgrenciProfili.ALAN_SECENEKLERI
    }
    return render(request, 'kayit.html', context)


def giris_view(request):
    """Kullanıcı giriş sayfası"""

    if request.method == 'POST':
        # DÜZELTME: FRONTEND'DE 'username' ve 'password' olarak POST ediliyor
        kullanici_adi = request.POST.get('username')
        sifre = request.POST.get('password')

        # Authenticate
        user = authenticate(request, username=kullanici_adi, password=sifre)

        if user is not None:
            login(request, user)
            messages.success(request, f'Hoş geldin {kullanici_adi}!')
            return redirect('profil')
        else:
            messages.error(request, 'Kullanıcı adı veya şifre hatalı!')

    return render(request, 'giris.html')


@login_required
def cikis_view(request):
    """Kullanıcı çıkış"""
    logout(request)
    messages.success(request, 'Başarıyla çıkış yaptın!')
    return redirect('giris')


# ==================== PROFİL ====================

@login_required
def profil_view(request):
    """Kullanıcı profil sayfası"""
    
    # Profil al veya oluştur
    try:
        profil = OgrenciProfili.objects.get(kullanici=request.user)
    except OgrenciProfili.DoesNotExist:
        profil = OgrenciProfili.objects.create(kullanici=request.user, alan='sayisal')
    
    # ✅ ROZET KONTROLÜ YAP (Her profil ziyaretinde)
    from .rozet_kontrol import rozet_kontrol_yap
    try:
        yeni_rozetler = rozet_kontrol_yap(profil)
        
        # Yeni rozet kazandıysa bildirim göster
        if yeni_rozetler:
            for rozet in yeni_rozetler:
                messages.success(request, f'🏆 Yeni rozet kazandın: {rozet.icon} {rozet.get_kategori_display()} ({rozet.get_seviye_display()})!')
    except Exception as e:
        print(f"❌ Rozet kontrol hatası: {e}")
    
    # ✅ Kullanıcının rozetleri (DOĞRU MODEL)
    from .models import Rozet
    kullanici_rozetleri = Rozet.objects.filter(profil=profil).order_by('-kazanilma_tarihi')[:10]
    
    # Oyun modu istatistikleri
    oyun_istatistikleri = OyunModuIstatistik.objects.filter(profil=profil)
    
    # Ders istatistikleri
    ders_istatistikleri = DersIstatistik.objects.filter(profil=profil).order_by('-toplam_puan')[:5]
    
    # Liderlik sırası
    kullanici_sira = OgrenciProfili.objects.filter(toplam_puan__gt=profil.toplam_puan).count() + 1
    
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
    """Profil düzenleme sayfası"""
    
    try:
        profil = OgrenciProfili.objects.get(kullanici=request.user)
    except OgrenciProfili.DoesNotExist:
        profil = OgrenciProfili.objects.create(kullanici=request.user, alan='sayisal')
    
    if request.method == 'POST':
        # Form verilerini al
        alan = request.POST.get('alan')
        profil_fotografi = request.FILES.get('profil_fotografi')
        
        # Güncelle
        if alan:
            profil.alan = alan
        
        if profil_fotografi:
            profil.profil_fotografi = profil_fotografi
        
        profil.save()
        
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
    # Sıralama tipi (toplam veya haftalık)
    sirala_tipi = request.GET.get('tip', 'toplam')
    
    # Alan filtresi
    alan_filtresi = request.GET.get('alan', 'genel')
    
    # Tüm profilleri al
    if alan_filtresi == 'genel':
        liderler = OgrenciProfili.objects.all()
    else:
        liderler = OgrenciProfili.objects.filter(alan=alan_filtresi)
    
    # Sıralama yap
    if sirala_tipi == 'haftalik':
        liderler = liderler.order_by('-haftalik_puan', '-toplam_puan')
    else:
        liderler = liderler.order_by('-toplam_puan', '-haftalik_puan')
    
    # Alan seçenekleri (manuel)
    alan_tercihleri = [
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
    }
    
    return render(request, 'liderlik.html', context)  # ✅ DOĞRU


    # ========================================
# GENEL LİDERLİK TABLOSU
# ========================================
@login_required
def liderlik_genel_view(request):
    """Genel Liderlik Tablosu - Toplam Puan"""
    
    # Sıralama tipi (toplam veya haftalık)
    sirala_tipi = request.GET.get('tip', 'toplam')
    
    # Alan filtresi
    alan_filtresi = request.GET.get('alan', 'genel')
    
    # Tüm profilleri al
    if alan_filtresi == 'genel':
        liderler = OgrenciProfili.objects.all()
    else:
        liderler = OgrenciProfili.objects.filter(alan=alan_filtresi)
    
    # Sıralama yap
    if sirala_tipi == 'haftalik':
        liderler = liderler.order_by('-haftalik_puan', '-toplam_puan')[:50]
    else:
        liderler = liderler.order_by('-toplam_puan', '-haftalik_puan')[:50]
    
    # Alan seçenekleri
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
    """Oyun Modu Bazlı Liderlik (Karşılaşma / Bul Bakalım)"""
    
    oyun_modu = request.GET.get('mod', 'karsilasma')
    sirala_tipi = request.GET.get('tip', 'toplam')
    
    # Oyun modu istatistiklerini al
    if sirala_tipi == 'haftalik':
        liderler = OyunModuIstatistik.objects.filter(
            oyun_modu=oyun_modu
        ).order_by('-haftalik_puan', '-toplam_puan')[:50]
    else:
        liderler = OyunModuIstatistik.objects.filter(
            oyun_modu=oyun_modu
        ).order_by('-toplam_puan', '-haftalik_puan')[:50]
    
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
    """Ders Bazlı Liderlik (Matematik, Fizik, Kimya vs.)"""
    
    ders = request.GET.get('ders', 'matematik')
    sirala = request.GET.get('sirala', 'dogru')  # dogru, net, oran
    
    # Ders istatistiklerini al
    if sirala == 'net':
        # Net'e göre sıralama (SQL'de hesaplama)
        liderler = DersIstatistik.objects.filter(
            ders=ders
        ).annotate(
            hesaplanan_net=F('dogru_sayisi') - (F('yanlis_sayisi') / 4.0)
        ).order_by('-hesaplanan_net', '-dogru_sayisi')[:50]
    elif sirala == 'oran':
        # Başarı oranına göre (en az 10 soru çözenler)
        liderler = DersIstatistik.objects.filter(
            ders=ders,
            cozulen_soru__gte=10
        ).order_by('-dogru_sayisi', '-cozulen_soru')[:50]
    else:
        # Doğru sayısına göre
        liderler = DersIstatistik.objects.filter(
            ders=ders
        ).order_by('-dogru_sayisi', '-cozulen_soru')[:50]
    
    # Ders listesi
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
    """Konu bazlı istatistikler"""
    from django.db.models import Count, Q
    
    # Kullanıcının çözdüğü sorular (konu bazında)
    konu_istatistikleri = KullaniciCevap.objects.filter(
        kullanici=request.user
    ).values('soru__konu__isim').annotate(
        toplam=Count('id'),
        dogru=Count('id', filter=Q(dogru_mu=True)),
        yanlis=Count('id', filter=Q(dogru_mu=False))
    ).order_by('-toplam')
    
    context = {
        'konu_istatistikleri': konu_istatistikleri,
    }
    
    return render(request, 'konu_istatistik.html', context)


# ====================== KONU ANALİZİ ======================

def konu_analiz_view(request):
    profil = request.user.profil
    dersler = ['matematik', 'fizik', 'kimya', 'biyoloji', 'turkce']
    konu_istatistikleri = KonuIstatistik.objects.filter(profil=profil)
    ders_konular_list = []
    for ders in dersler:
        ders_konular_list.append({
            'ders': ders,
            'konular': konu_istatistikleri.filter(ders=ders)
        })
    return render(request, 'konu_analiz.html', {
        'dersler': dersler,
        'ders_konular_list': ders_konular_list,
    })

# ==================== ROZETLER ====================

@login_required
def rozetler_view(request):
    """Kullanıcının rozetlerini göster"""
    
    try:
        profil = OgrenciProfili.objects.get(kullanici=request.user)
    except OgrenciProfili.DoesNotExist:
        profil = OgrenciProfili.objects.create(kullanici=request.user, alan='sayisal')
    
    # Kullanıcının rozetleri (YENİ MODEL)
    from .models import Rozet  # ✅ Import ekle
    kullanici_rozetleri = Rozet.objects.filter(profil=profil).select_related('profil')
    
    # Rozet kategorileri
    tum_kategoriler = [
        ('yeni_uye', 'Yeni Üye', '🌱'),
        ('aktif_kullanici', 'Aktif Kullanıcı', '⚡'),
        ('gun_asimi', 'Gün Aşımı', '📅'),
        ('hafta_sampionu', 'Hafta Şampiyonu', '👑'),
        ('soru_cozucu', 'Soru Çözücü', '📝'),
        ('dogru_ustasi', 'Doğru Ustası', '✅'),
        ('net_avcisi', 'Net Avcısı', '🎯'),
        ('hatasiz_kusursuz', 'Hatasız Kusursuz', '💯'),
        ('matematik_dehasi', 'Matematik Dehası', '🔢'),
        ('fizik_profesoru', 'Fizik Profesörü', '⚛️'),
        ('kimya_uzman', 'Kimya Uzmanı', '🧪'),
        ('biyoloji_bilgini', 'Biyoloji Bilgini', '🧬'),
        ('turkce_edebiyatci', 'Türkçe Edebiyatçısı', '📖'),
        ('tarih_bilgesi', 'Tarih Bilgesi', '🏛️'),
        ('cografya_gezgini', 'Coğrafya Gezgini', '🌍'),
        ('felsefe_dusunuru', 'Felsefe Düşünürü', '💭'),
        ('karsilasma_savaslisi', 'Karşılaşma Savaşçısı', '⚔️'),
        ('bul_bakalim_ustasi', 'Bul Bakalım Ustası', '💡'),
        ('tabu_kral', 'Tabu Kralı', '🎭'),
        ('galip_aslan', 'Galip Aslan', '🦁'),
        ('lider_zirve', 'Lider Zirve', '🏆'),
        ('top_10', 'Top 10', '🥇'),
        ('top_50', 'Top 50', '🥈'),
        ('zirve_fatih', 'Zirve Fatihi', '👑'),
        ('hizli_cevap', 'Hızlı Cevap', '⚡'),
        ('gece_kusu', 'Gece Kuşu', '🦉'),
        ('sabah_kusagu', 'Sabah Kuşağı', '🌅'),
        ('maraton_kosucu', 'Maraton Koşucusu', '🏃'),
        ('yardimci', 'Yardımcı', '🤝'),
        ('ogretmen', 'Öğretmen', '👨‍🏫'),
        ('ilham_verici', 'İlham Verici', '✨'),
        ('takım_oyuncusu', 'Takım Oyuncusu', '👥'),
    ]
    
    # Kazanılmış rozetleri organize et
    kazanilmis_rozetler = {}
    for rozet in kullanici_rozetleri:
        if rozet.kategori not in kazanilmis_rozetler:
            kazanilmis_rozetler[rozet.kategori] = {}
        kazanilmis_rozetler[rozet.kategori][rozet.seviye] = rozet
    
    # Rozet durumlarını hazırla
    rozet_durumu = []
    for kategori_kod, kategori_isim, icon in tum_kategoriler:
        caylak_var = kategori_kod in kazanilmis_rozetler and 'caylak' in kazanilmis_rozetler[kategori_kod]
        usta_var = kategori_kod in kazanilmis_rozetler and 'usta' in kazanilmis_rozetler[kategori_kod]
        
        rozet_durumu.append({
            'kod': kategori_kod,
            'isim': kategori_isim,
            'icon': icon,
            'caylak_var': caylak_var,
            'usta_var': usta_var,
            'caylak_rozet': kazanilmis_rozetler.get(kategori_kod, {}).get('caylak'),
            'usta_rozet': kazanilmis_rozetler.get(kategori_kod, {}).get('usta'),
        })
    
    # İstatistikler
    toplam_rozet = kullanici_rozetleri.count()
    toplam_olasi = len(tum_kategoriler) * 2
    tamamlanma_yuzdesi = round((toplam_rozet / toplam_olasi) * 100, 1) if toplam_olasi > 0 else 0
    
    context = {
        'profil': profil,
        'rozet_durumu': rozet_durumu,
        'toplam_rozet': toplam_rozet,
        'toplam_olasi': toplam_olasi,
        'tamamlanma_yuzdesi': tamamlanma_yuzdesi,
    }
    
    # ✅ YENİ TEMPLATE KULLAN (profile/templates/rozetler.html)
    return render(request, 'rozetler.html', context)