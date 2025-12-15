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
from django.core.cache import cache
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)


def anasayfa(request):
    return render(request, 'giris_sayfasi.html')


def kayit_view(request):
    if request.method == 'POST':
        kullanici_adi = request.POST.get('username')
        email = request.POST.get('email')
        sifre = request.POST.get('password')
        sifre_tekrar = request.POST.get('password2')
        
        if not kullanici_adi or not email or not sifre or not sifre_tekrar:
            messages.error(request, 'Tüm alanları doldurun!')
            logger.warning(f"Kayıt denemesi: Eksik alan - Kullanıcı: {kullanici_adi}")
            return render(request, 'kayit.html')
        
        if sifre != sifre_tekrar:
            messages.error(request, 'Şifreler eşleşmiyor!')
            logger.warning(f"Kayıt denemesi: Şifre eşleşmedi - Kullanıcı: {kullanici_adi}")
            return render(request, 'kayit.html')
        
        if User.objects.filter(username=kullanici_adi).exists():
            messages.error(request, 'Bu kullanıcı adı zaten alınmış!')
            logger.warning(f"Kayıt denemesi: Kullanıcı adı mevcut - {kullanici_adi}")
            return render(request, 'kayit.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Bu email zaten kayıtlı!')
            logger.warning(f"Kayıt denemesi: Email mevcut - {email}")
            return render(request, 'kayit.html')
        
        if len(sifre) < 6:
            messages.error(request, 'Şifre en az 6 karakter olmalı!')
            logger.warning(f"Kayıt denemesi: Kısa şifre - Kullanıcı: {kullanici_adi}")
            return render(request, 'kayit.html')
        
        try:
            with transaction.atomic():
                user = User.objects.create_user(username=kullanici_adi, email=email, password=sifre)
                profil, created = OgrenciProfili.objects.get_or_create(kullanici=user, defaults={'alan': 'sayisal'})
                
                if created:
                    yeni_rozetler = rozet_kontrol_yap(profil)
                    logger.info(f"Yeni kullanıcı kaydı: {kullanici_adi}, Rozet sayısı: {len(yeni_rozetler) if yeni_rozetler else 0}")
                else:
                    yeni_rozetler = []
                    logger.info(f"Kullanıcı kaydı (profil mevcut): {kullanici_adi}")
                
                login(request, user)
                
                if yeni_rozetler:
                    messages.success(request, f'🎉 Hoş geldin {kullanici_adi}! {len(yeni_rozetler)} rozet kazandın!')
                else:
                    messages.success(request, f'Hoş geldin {kullanici_adi}! Kayıt başarılı!')
                
                return redirect('profil')
        
        except IntegrityError as e:
            logger.error(f"Kayıt veritabanı hatası: Kullanıcı={kullanici_adi}, Hata={e}", exc_info=True)
            messages.error(request, 'Kayıt sırasında bir veritabanı hatası oluştu.Lütfen tekrar deneyin.')
            return render(request, 'kayit.html')
        except ValidationError as e:
            logger.error(f"Kayıt validasyon hatası: Kullanıcı={kullanici_adi}, Hata={e}", exc_info=True)
            messages.error(request, 'Girdiğiniz bilgiler geçersiz.Lütfen kontrol edin.')
            return render(request, 'kayit.html')
        except ImportError as e:
            logger.error(f"Rozet modülü import hatası: Kullanıcı={kullanici_adi}, Hata={e}", exc_info=True)
            messages.warning(request, 'Kayıt başarılı ancak rozet sistemi şu an kullanılamıyor.')
            return redirect('profil')
        except Exception as e:
            logger.error(f"Kayıt beklenmeyen hata: Kullanıcı={kullanici_adi}, Hata={e}", exc_info=True)
            messages.error(request, f'Kayıt sırasında bir hata oluştu: {str(e)}')
            return render(request, 'kayit.html')
    
    return render(request, 'kayit.html')


def giris_view(request):
    if request.method == 'POST':
        kullanici_adi = request.POST.get('username')
        sifre = request.POST.get('password')
        
        try:
            user = authenticate(request, username=kullanici_adi, password=sifre)
            
            if user is not None:
                login(request, user)
                messages.success(request, f'Hoş geldin {kullanici_adi}!')
                logger.info(f"Başarılı giriş: {kullanici_adi}")
                return redirect('profil')
            else:
                messages.error(request, 'Kullanıcı adı veya şifre hatalı!')
                logger.warning(f"Başarısız giriş denemesi: {kullanici_adi}")
        
        except Exception as e:
            logger.error(f"Giriş beklenmeyen hata: Kullanıcı={kullanici_adi}, Hata={e}", exc_info=True)
            messages.error(request, 'Giriş sırasında bir hata oluştu.')
    
    return render(request, 'giris.html')


@login_required
def cikis_view(request):
    kullanici_adi = request.user.username
    
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
        logger.debug(f"Cache temizlendi: Kullanıcı={kullanici_adi}")
    except AttributeError as e:
        logger.warning(f"Çıkış profil erişim hatası: Kullanıcı={kullanici_adi}, Hata={e}")
    except Exception as e:
        logger.error(f"Çıkış cache temizleme hatası: Kullanıcı={kullanici_adi}, Hata={e}", exc_info=True)
    
    logout(request)
    messages.success(request, 'Başarıyla çıkış yaptın!')
    logger.info(f"Kullanıcı çıkış yaptı: {kullanici_adi}")
    return redirect('giris')


@login_required
def profil_view(request):
    try:
        profil = OgrenciProfili.objects.select_related('kullanici').get(kullanici=request.user)
    except OgrenciProfili.DoesNotExist:
        try:
            profil = OgrenciProfili.objects.create(kullanici=request.user, alan='sayisal')
            logger.info(f"Yeni profil oluşturuldu: Kullanıcı={request.user.username}")
        except IntegrityError as e:
            logger.error(f"Profil oluşturma hatası: Kullanıcı={request.user.username}, Hata={e}", exc_info=True)
            messages.error(request, 'Profil oluşturulurken bir hata oluştu.')
            return redirect('anasayfa')
    
    cache_key = f'rozet_kontrol_{profil.id}_{profil.cozulen_soru_sayisi}'
    yeni_rozetler = cache.get(cache_key)
    
    if yeni_rozetler is None:
        try:
            yeni_rozetler = rozet_kontrol_yap(profil)
            cache.set(cache_key, yeni_rozetler, 300)
            
            if yeni_rozetler:
                for rozet in yeni_rozetler:
                    messages.success(request, f'🏆 Yeni rozet kazandın: {rozet.icon} {rozet.get_kategori_display()} ({rozet.get_seviye_display()})!')
                logger.info(f"Yeni rozetler kazanıldı: Kullanıcı={request.user.username}, Sayı={len(yeni_rozetler)}")
        except ImportError as e:
            logger.error(f"Rozet modülü import hatası: Kullanıcı={request.user.username}, Hata={e}", exc_info=True)
            yeni_rozetler = []
        except Exception as e:
            logger.error(f"Rozet kontrol hatası: Kullanıcı={request.user.username}, Hata={e}", exc_info=True)
            yeni_rozetler = []
    
    try:
        kullanici_rozetleri = Rozet.objects.filter(profil=profil).select_related('profil__kullanici').order_by('-kazanilma_tarihi')[:10]
    except Exception as e:
        logger.error(f"Rozet listesi hatası: Kullanıcı={request.user.username}, Hata={e}", exc_info=True)
        kullanici_rozetleri = []
    
    cache_key_oyun = f'oyun_ist_{profil.id}'
    oyun_istatistikleri = cache.get(cache_key_oyun)
    
    if oyun_istatistikleri is None:
        try:
            oyun_istatistikleri = OyunModuIstatistik.objects.filter(profil=profil).select_related('profil')
            cache.set(cache_key_oyun, list(oyun_istatistikleri), 60)
        except Exception as e:
            logger.error(f"Oyun istatistik hatası: Kullanıcı={request.user.username}, Hata={e}", exc_info=True)
            oyun_istatistikleri = []
    
    cache_key_ders = f'ders_ist_{profil.id}'
    ders_istatistikleri = cache.get(cache_key_ders)
    
    if ders_istatistikleri is None:
        try:
            ders_istatistikleri = DersIstatistik.objects.filter(profil=profil).select_related('profil').order_by('-toplam_puan')[:5]
            cache.set(cache_key_ders, list(ders_istatistikleri), 60)
        except Exception as e:
            logger.error(f"Ders istatistik hatası: Kullanıcı={request.user.username}, Hata={e}", exc_info=True)
            ders_istatistikleri = []
    
    cache_key_sira = f'liderlik_sira_{profil.id}_{profil.toplam_puan}'
    kullanici_sira = cache.get(cache_key_sira)
    
    if kullanici_sira is None:
        try:
            kullanici_sira = OgrenciProfili.objects.filter(toplam_puan__gt=profil.toplam_puan).count() + 1
            cache.set(cache_key_sira, kullanici_sira, 120)
        except Exception as e:
            logger.error(f"Liderlik sıra hatası: Kullanıcı={request.user.username}, Hata={e}", exc_info=True)
            kullanici_sira = 0
    
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
    try:
        profil = OgrenciProfili.objects.select_related('kullanici').get(kullanici=request.user)
    except OgrenciProfili.DoesNotExist:
        try:
            profil = OgrenciProfili.objects.create(kullanici=request.user, alan='sayisal')
            logger.info(f"Profil düzenleme için yeni profil oluşturuldu: Kullanıcı={request.user.username}")
        except IntegrityError as e:
            logger.error(f"Profil oluşturma hatası: Kullanıcı={request.user.username}, Hata={e}", exc_info=True)
            messages.error(request, 'Profil oluşturulurken bir hata oluştu.')
            return redirect('profil')
    
    if request.method == 'POST':
        alan = request.POST.get('alan')
        profil_fotografi = request.FILES.get('profil_fotografi')
        
        try:
            with transaction.atomic():
                if alan:
                    profil.alan = alan
                if profil_fotografi:
                    profil.profil_fotografi = profil_fotografi
                profil.save()
                
                logger.info(f"Profil güncellendi: Kullanıcı={request.user.username}, Alan={alan}, Foto={'Evet' if profil_fotografi else 'Hayır'}")
                
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
        
        except ValidationError as e:
            logger.error(f"Profil güncelleme validasyon hatası: Kullanıcı={request.user.username}, Hata={e}", exc_info=True)
            messages.error(request, 'Girdiğiniz bilgiler geçersiz.')
        except IntegrityError as e:
            logger.error(f"Profil güncelleme veritabanı hatası: Kullanıcı={request.user.username}, Hata={e}", exc_info=True)
            messages.error(request, 'Profil güncellenirken bir hata oluştu.')
        except Exception as e:
            logger.error(f"Profil güncelleme beklenmeyen hata: Kullanıcı={request.user.username}, Hata={e}", exc_info=True)
            messages.error(request, 'Bir hata oluştu.')
    
    context = {'profil': profil, 'alan_secenekleri': OgrenciProfili.ALAN_SECENEKLERI}
    return render(request, 'profil_duzenle.html', context)


@login_required
def liderlik_view(request):
    """Liderlik tablosu - 4 farklı kategori (Günlük, Haftalık, Aylık, Tüm Zamanlar)"""
    
    try:
        # Kullanıcının kendi profilinde reset kontrolü
        profil = request.user.profil
        profil.reset_kontrolu()
    except AttributeError:
        logger.error(f"Liderlik profil erişim hatası:  Kullanıcı={request.user.username}")
        messages.error(request, 'Profil bulunamadı.')
        return redirect('profil')
    
    # Aktif kategori (varsayılan: haftalık)
    kategori = request.GET.get('kategori', 'haftalik')
    
    # Cache key
    cache_key = f'liderlik_{kategori}'
    cached_data = cache.get(cache_key)
    
    if cached_data is None:
        logger.debug(f"Liderlik cache'den alınamadı:  Kategori={kategori}")
        
        try:
            # Kategoriye göre sıralama
            if kategori == 'gunluk':
                liderler = OgrenciProfili.objects.filter(
                    aktif_mi=True
                ).select_related('kullanici').only(
                    'kullanici__username', 'gunluk_puan', 'toplam_puan', 
                    'gunluk_dogru', 'gunluk_yanlis', 'cozulen_soru_sayisi', 'alan'
                ).order_by('-gunluk_puan', '-toplam_puan')[:50]
                baslik = "Günlük Liderlik"
                puan_alani = 'gunluk_puan'
                
            elif kategori == 'haftalik':
                liderler = OgrenciProfili.objects.filter(
                    aktif_mi=True
                ).select_related('kullanici').only(
                    'kullanici__username', 'haftalik_puan', 'toplam_puan',
                    'haftalik_dogru', 'haftalik_yanlis', 'cozulen_soru_sayisi', 'alan'
                ).order_by('-haftalik_puan', '-toplam_puan')[:50]
                baslik = "Haftalık Liderlik"
                puan_alani = 'haftalik_puan'
                
            elif kategori == 'aylik':
                liderler = OgrenciProfili.objects.filter(
                    aktif_mi=True
                ).select_related('kullanici').only(
                    'kullanici__username', 'aylik_puan', 'toplam_puan',
                    'aylik_dogru', 'aylik_yanlis', 'cozulen_soru_sayisi', 'alan'
                ).order_by('-aylik_puan', '-toplam_puan')[:50]
                baslik = "Aylık Liderlik"
                puan_alani = 'aylik_puan'
                
            else:  # tum_zamanlar
                liderler = OgrenciProfili.objects.filter(
                    aktif_mi=True
                ).select_related('kullanici').only(
                    'kullanici__username', 'toplam_puan', 'cozulen_soru_sayisi',
                    'toplam_dogru', 'toplam_yanlis', 'alan'
                ).order_by('-toplam_puan', '-cozulen_soru_sayisi')[:50]
                baslik = "Tüm Zamanlar"
                puan_alani = 'toplam_puan'
            
            cached_data = {
                'liderler': list(liderler),
                'baslik': baslik,
                'puan_alani': puan_alani,
            }
            cache.set(cache_key, cached_data, 120)  # 2 dakika cache
            
        except Exception as e:
            logger.error(f"Liderlik verileri hatası:  Kategori={kategori}, Hata={e}", exc_info=True)
            cached_data = {
                'liderler': [],
                'baslik': 'Liderlik',
                'puan_alani': 'toplam_puan',
            }
    
    # Kullanıcının kendi sıralaması
    try:
        if kategori == 'gunluk': 
            kullanici_siralama = profil.gunluk_siralama
            kullanici_puan = profil.gunluk_puan
        elif kategori == 'haftalik':
            kullanici_siralama = profil.haftalik_siralama
            kullanici_puan = profil.haftalik_puan
        elif kategori == 'aylik':
            kullanici_siralama = profil.aylik_siralama
            kullanici_puan = profil.aylik_puan
        else: 
            kullanici_siralama = profil.genel_siralama
            kullanici_puan = profil.toplam_puan
    except Exception as e:
        logger.error(f"Kullanıcı sıralama hatası:  Kullanıcı={request.user.username}, Hata={e}", exc_info=True)
        kullanici_siralama = 0
        kullanici_puan = 0
    
    # Toplam kullanıcı sayısı
    try:
        toplam_kullanici = OgrenciProfili.objects.filter(aktif_mi=True).count()
    except Exception as e: 
        logger.error(f"Toplam kullanıcı sayısı hatası: Hata={e}", exc_info=True)
        toplam_kullanici = 0
    
    context = {
        'liderler': cached_data['liderler'],
        'baslik': cached_data['baslik'],
        'kategori': kategori,
        'puan_alani': cached_data['puan_alani'],
        'kullanici_siralama': kullanici_siralama,
        'kullanici_puan': kullanici_puan,
        'toplam_kullanici': toplam_kullanici,
    }
    
    return render(request, 'liderlik.html', context)


@login_required
def liderlik_genel_view(request):
    sirala_tipi = request.GET.get('tip', 'toplam')
    alan_filtresi = request.GET.get('alan', 'genel')
    
    cache_key = f'liderlik_genel_{sirala_tipi}_{alan_filtresi}'
    liderler = cache.get(cache_key)
    
    if liderler is None:
        logger.debug(f"Genel liderlik cache'den alınamadı: Tip={sirala_tipi}, Alan={alan_filtresi}")
        
        try:
            if alan_filtresi == 'genel':
                liderler = OgrenciProfili.objects.select_related('kullanici').only('kullanici__username', 'toplam_puan', 'haftalik_puan', 'cozulen_soru_sayisi')
            else:
                liderler = OgrenciProfili.objects.select_related('kullanici').filter(alan=alan_filtresi).only('kullanici__username', 'toplam_puan', 'haftalik_puan', 'alan')
            
            if sirala_tipi == 'haftalik':
                liderler = liderler.order_by('-haftalik_puan', '-toplam_puan')[:50]
            else:
                liderler = liderler.order_by('-toplam_puan', '-haftalik_puan')[:50]
            
            liderler = list(liderler)
            cache.set(cache_key, liderler, 180)
        
        except Exception as e:
            logger.error(f"Genel liderlik hatası: Tip={sirala_tipi}, Alan={alan_filtresi}, Hata={e}", exc_info=True)
            liderler = []
    
    alan_tercihleri = [('genel', 'Tüm Alanlar'), ('sayisal', 'Sayısal'), ('sozel', 'Sözel'), ('esit_agirlik', 'Eşit Ağırlık'), ('dil', 'Dil')]
    context = {'liderler': liderler, 'sirala_tipi': sirala_tipi, 'alan_filtresi': alan_filtresi, 'alan_tercihleri': alan_tercihleri, 'sayfa_baslik': 'Genel Liderlik Tablosu'}
    return render(request, 'liderlik_genel.html', context)


@login_required
def liderlik_oyun_modu_view(request):
    oyun_modu = request.GET.get('mod', 'karsilasma')
    sirala_tipi = request.GET.get('tip', 'toplam')
    
    cache_key = f'liderlik_oyun_{oyun_modu}_{sirala_tipi}'
    liderler = cache.get(cache_key)
    
    if liderler is None:
        logger.debug(f"Oyun modu liderlik cache'den alınamadı: Mod={oyun_modu}, Tip={sirala_tipi}")
        
        try:
            if sirala_tipi == 'haftalik':
                liderler = OyunModuIstatistik.objects.filter(oyun_modu=oyun_modu).select_related('profil__kullanici').only('profil__kullanici__username', 'haftalik_puan', 'toplam_puan', 'oynanan_oyun_sayisi').order_by('-haftalik_puan', '-toplam_puan')[:50]
            else:
                liderler = OyunModuIstatistik.objects.filter(oyun_modu=oyun_modu).select_related('profil__kullanici').only('profil__kullanici__username', 'toplam_puan', 'oynanan_oyun_sayisi').order_by('-toplam_puan', '-haftalik_puan')[:50]
            
            liderler = list(liderler)
            cache.set(cache_key, liderler, 180)
        
        except Exception as e:
            logger.error(f"Oyun modu liderlik hatası: Mod={oyun_modu}, Tip={sirala_tipi}, Hata={e}", exc_info=True)
            liderler = []
    
    context = {'liderler': liderler, 'oyun_modu': oyun_modu, 'sirala_tipi': sirala_tipi, 'sayfa_baslik': f"{'Karşılaşma' if oyun_modu == 'karsilasma' else 'Bul Bakalım'} Liderliği"}
    return render(request, 'liderlik_oyun_modu.html', context)


@login_required
def liderlik_ders_view(request):
    ders = request.GET.get('ders', 'matematik')
    sirala = request.GET.get('sirala', 'dogru')
    
    cache_key = f'liderlik_ders_{ders}_{sirala}'
    liderler = cache.get(cache_key)
    
    if liderler is None:
        logger.debug(f"Ders liderlik cache'den alınamadı: Ders={ders}, Sıralama={sirala}")
        
        try:
            if sirala == 'net':
                liderler = DersIstatistik.objects.filter(ders=ders).select_related('profil__kullanici').annotate(hesaplanan_net=F('dogru_sayisi') - (F('yanlis_sayisi') / 4.0)).order_by('-hesaplanan_net', '-dogru_sayisi')[:50]
            elif sirala == 'oran':
                liderler = DersIstatistik.objects.filter(ders=ders, cozulen_soru__gte=10).select_related('profil__kullanici').order_by('-dogru_sayisi', '-cozulen_soru')[:50]
            else:
                liderler = DersIstatistik.objects.filter(ders=ders).select_related('profil__kullanici').order_by('-dogru_sayisi', '-cozulen_soru')[:50]
            
            liderler = list(liderler)
            cache.set(cache_key, liderler, 180)
        
        except Exception as e:
            logger.error(f"Ders liderlik hatası: Ders={ders}, Sıralama={sirala}, Hata={e}", exc_info=True)
            liderler = []
    
    ders_listesi = [('matematik', 'Matematik'), ('fizik', 'Fizik'), ('kimya', 'Kimya'), ('biyoloji', 'Biyoloji'), ('turkce', 'Türkçe'), ('tarih', 'Tarih'), ('cografya', 'Coğrafya'), ('felsefe', 'Felsefe'), ('din', 'Din Kültürü'), ('ingilizce', 'İngilizce')]
    context = {'liderler': liderler, 'ders': ders, 'sirala': sirala, 'ders_listesi': ders_listesi, 'ders_adi': dict(ders_listesi).get(ders, ders), 'sayfa_baslik': f"{dict(ders_listesi).get(ders, ders)} Liderliği"}
    return render(request, 'liderlik_ders.html', context)


@login_required
def konu_istatistik_view(request):
    cache_key = f'konu_ist_{request.user.id}'
    konu_istatistikleri = cache.get(cache_key)
    
    if konu_istatistikleri is None:
        from quiz.models import KullaniciCevap
        logger.debug(f"Konu istatistikleri cache'den alınamadı: Kullanıcı={request.user.username}")
        
        try:
            konu_istatistikleri = KullaniciCevap.objects.filter(kullanici=request.user).values('soru__konu__isim').annotate(toplam=Count('id'), dogru=Count('id', filter=Q(dogru_mu=True)), yanlis=Count('id', filter=Q(dogru_mu=False))).order_by('-toplam')
            konu_istatistikleri = list(konu_istatistikleri)
            cache.set(cache_key, konu_istatistikleri, 300)
        
        except Exception as e:
            logger.error(f"Konu istatistik hatası: Kullanıcı={request.user.username}, Hata={e}", exc_info=True)
            konu_istatistikleri = []
    
    context = {'konu_istatistikleri': konu_istatistikleri}
    return render(request, 'konu_istatistik.html', context)


@login_required
def konu_analiz_view(request):
    cache_key = f'konu_analiz_{request.user.profil.id}'
    cached_data = cache.get(cache_key)
    
    if cached_data is None:
        logger.debug(f"Konu analizi cache'den alınamadı: Kullanıcı={request.user.username}")
        
        try:
            profil = request.user.profil
            dersler = ['matematik', 'fizik', 'kimya', 'biyoloji', 'turkce']
            konu_istatistikleri = KonuIstatistik.objects.filter(profil=profil).select_related('profil')
            
            ders_konular_list = []
            for ders in dersler:
                ders_konular_list.append({'ders': ders, 'konular': list(konu_istatistikleri.filter(ders=ders))})
            
            cached_data = {'dersler': dersler, 'ders_konular_list': ders_konular_list}
            cache.set(cache_key, cached_data, 300)
        
        except AttributeError as e:
            logger.error(f"Konu analizi profil hatası: Kullanıcı={request.user.username}, Hata={e}", exc_info=True)
            cached_data = {'dersler': [], 'ders_konular_list': []}
        except Exception as e:
            logger.error(f"Konu analizi hatası: Kullanıcı={request.user.username}, Hata={e}", exc_info=True)
            cached_data = {'dersler': [], 'ders_konular_list': []}
    
    return render(request, 'konu_analiz.html', cached_data)


@login_required
def rozetler_view(request):
    cache_key = f'rozetler_view_{request.user.id}'
    cached_context = cache.get(cache_key)
    
    if cached_context is None:
        logger.debug(f"Rozetler cache'den alınamadı: Kullanıcı={request.user.username}")
        
        try:
            profil = OgrenciProfili.objects.select_related('kullanici').get(kullanici=request.user)
        except OgrenciProfili.DoesNotExist:
            try:
                profil = OgrenciProfili.objects.create(kullanici=request.user, alan='sayisal')
                logger.info(f"Rozetler için yeni profil oluşturuldu: Kullanıcı={request.user.username}")
            except IntegrityError as e:
                logger.error(f"Rozet profil oluşturma hatası: Kullanıcı={request.user.username}, Hata={e}", exc_info=True)
                messages.error(request, 'Profil oluşturulurken bir hata oluştu.')
                return redirect('profil')
        
        try:
            kazanilan_rozetler = Rozet.objects.filter(profil=profil).select_related('profil__kullanici').order_by('-kazanilma_tarihi')
            
            tum_rozet_tanimi = []
            for kategori, _ in Rozet.KATEGORI_SECENEKLERI:
                for seviye, _ in Rozet.SEVIYE_SECENEKLERI:
                    tum_rozet_tanimi.append({'kategori': kategori, 'seviye': seviye})
            
            kazanilan_set = {(r.kategori, r.seviye) for r in kazanilan_rozetler}
            
            ICON_MAP = {'yeni_uye': '🌱', 'aktif_kullanici': '⚡', 'gun_asimi': '📅', 'hafta_sampionu': '👑', 'soru_cozucu': '📝', 'dogru_ustasi': '✅', 'net_avcisi': '🎯', 'hatasiz_kusursuz': '💯', 'matematik_dehasi': '🔢', 'fizik_profesoru': '⚛️', 'kimya_uzman': '🧪', 'biyoloji_bilgini': '🧬', 'turkce_edebiyatci': '📖', 'tarih_bilgesi': '🏛️', 'cografya_gezgini': '🌍', 'felsefe_dusunuru': '💭', 'karsilasma_savaslisi': '⚔️', 'bul_bakalim_ustasi': '💡', 'tabu_kral': '🎭', 'galip_aslan': '🦁', 'lider_zirve': '🏆', 'top_10': '🥇', 'top_50': '🥈', 'zirve_fatih': '👑', 'hizli_cevap': '⚡', 'gece_kusu': '🦉', 'sabah_kusagu': '🌅', 'maraton_kosucu': '🏃', 'yardimci': '🤝', 'ogretmen': '👨\u200d🏫', 'ilham_verici': '✨', 'takım_oyuncusu': '👥'}
            
            kazanilmamis_rozetler = []
            for tanim in tum_rozet_tanimi:
                if (tanim['kategori'], tanim['seviye']) not in kazanilan_set:
                    kategori_kod = tanim['kategori']
                    seviye_kod = tanim['seviye']
                    isim = dict(Rozet.KATEGORI_SECENEKLERI).get(kategori_kod, 'Bilinmeyen')
                    emoji = ICON_MAP.get(kategori_kod, '🏅')
                    aciklama = ROZET_ACIKLAMALARI.get(kategori_kod, {}).get(seviye_kod, "Açıklama bulunamadı.")
                    kazanilmamis_rozetler.append({'kategori': kategori_kod, 'seviye': seviye_kod, 'isim': isim, 'emoji': emoji, 'aciklama': aciklama})
            
            cached_context = {'kazanilan_rozetler': list(kazanilan_rozetler), 'kazanilmamis_rozetler': kazanilmamis_rozetler, 'kazanilan_sayi': kazanilan_rozetler.count(), 'toplam_rozet': len(tum_rozet_tanimi)}
            cache.set(cache_key, cached_context, 180)
            logger.debug(f"Rozetler cache'lendi: Kullanıcı={request.user.username}")
        
        except Exception as e:
            logger.error(f"Rozet listesi hatası: Kullanıcı={request.user.username}, Hata={e}", exc_info=True)
            cached_context = {'kazanilan_rozetler': [], 'kazanilmamis_rozetler': [], 'kazanilan_sayi': 0, 'toplam_rozet': 0}
    
    return render(request, 'rozetler.html', cached_context)