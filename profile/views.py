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
from profile.models import Rozet, Bildirim, Arkadaslik
from django.core.cache import cache
from django.db import transaction, IntegrityError, models
from django.core.exceptions import ValidationError
from django.utils import timezone
import datetime
import logging
from django.http import JsonResponse
from profile.bildirim_helper import liderlik_bildirimi_gonder
from profile.xp_helper import gunluk_giris_xp
from profile.arkadaslik_helper import (
    arkadaslik_istegi_gonder,
    arkadaslik_istegi_kabul_et,
    arkadaslik_istegi_reddet,
    arkadasliktan_cikar
)

logger = logging.getLogger(__name__)

GUN_KISA_MAP = {0: 'Pzt', 1: 'Sal', 2: 'Çar', 3: 'Per', 4: 'Cum', 5: 'Cmt', 6: 'Paz'}


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

        if len(sifre) < 8:
            messages.error(request, 'Şifre en az 8 karakter olmalı!')
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
            messages.error(request, 'Kayıt sırasında bir veritabanı hatası oluştu. Lütfen tekrar deneyin.')
            return render(request, 'kayit.html')
        except ValidationError as e:
            logger.error(f"Kayıt validasyon hatası: Kullanıcı={kullanici_adi}, Hata={e}", exc_info=True)
            messages.error(request, 'Girdiğiniz bilgiler geçersiz. Lütfen kontrol edin.')
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


def _son_7_gun_hesapla():
    """Son 7 günü hesaplar ve liste olarak döner."""
    bugun = timezone.now().date()
    son_7_gun = []
    for i in range(6, -1, -1):
        tarih = bugun - datetime.timedelta(days=i)
        son_7_gun.append({
            'tarih': tarih.strftime('%d.%m'),
            'gun_kisa': GUN_KISA_MAP[tarih.weekday()],
            'aktif': False,
        })
    return son_7_gun


@login_required
def profil_view(request):
    """Profil sayfası - Kendi veya başkasının profili"""

    goruntulenen_kullanici_adi = request.GET.get('user')

    if goruntulenen_kullanici_adi:
        try:
            goruntulenen_kullanici = User.objects.get(username=goruntulenen_kullanici_adi)
        except User.DoesNotExist:
            messages.error(request, 'Kullanıcı bulunamadı!')
            return redirect('profil')
    else:
        goruntulenen_kullanici = request.user

    # ==================== POST ====================
    if request.method == 'POST':
        return redirect('profil')

    # ==================== PROFİL ====================
    try:
        profil = OgrenciProfili.objects.select_related('kullanici').get(kullanici=goruntulenen_kullanici)
    except OgrenciProfili.DoesNotExist:
        if goruntulenen_kullanici == request.user:
            try:
                profil = OgrenciProfili.objects.create(kullanici=request.user, alan='sayisal')
                logger.info(f"Yeni profil oluşturuldu: Kullanıcı={request.user.username}")
            except IntegrityError as e:
                logger.error(f"Profil oluşturma hatası: Kullanıcı={request.user.username}, Hata={e}", exc_info=True)
                messages.error(request, 'Profil oluşturulurken bir hata oluştu.')
                return redirect('anasayfa')
        else:
            messages.error(request, 'Bu kullanıcının profili bulunamadı!')
            return redirect('profil')

    # ==================== GÜNLÜK GİRİŞ BONUSU ====================
    if goruntulenen_kullanici == request.user:
        try:
            giris_bilgi = profil.gunluk_giris_kontrol()
            if giris_bilgi['bonus_verildi']:
                xp_sonuc = gunluk_giris_xp(profil, giris_bilgi['bonus_xp'])
                if giris_bilgi.get('ilk_giris'):
                    messages.success(request, f"🎉 Hoş geldin! İlk giriş bonusu: +{giris_bilgi['bonus_xp']} XP!")
                elif giris_bilgi.get('streak_devam'):
                    messages.success(request, f"🔥 {giris_bilgi['streak']} gündür üst üste giriş! Bonus: +{giris_bilgi['bonus_xp']} XP!")
                elif giris_bilgi.get('streak_koptu'):
                    messages.warning(request, f"💔 Streak koptu! Yeniden başlıyorsun. +{giris_bilgi['bonus_xp']} XP")
                else:
                    messages.success(request, f"🎁 Günlük giriş bonusu: +{giris_bilgi['bonus_xp']} XP!")
                if xp_sonuc.get('seviye_atlandi'):
                    messages.success(request, f"🚀 SEVİYE ATLADIN! Seviye {xp_sonuc['yeni_seviye']} - {xp_sonuc['unvan']}")
        except Exception as e:
            logger.error(f"Günlük giriş bonus hatası: {e}", exc_info=True)

    # ==================== ROZET KONTROLÜ ====================
    yeni_rozetler = []
    if goruntulenen_kullanici == request.user:
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

    # ==================== KULLANICI ROZETLERİ ====================
    try:
        kullanici_rozetleri = Rozet.objects.filter(profil=profil).select_related('profil__kullanici').order_by('-kazanilma_tarihi')[:10]
    except Exception as e:
        logger.error(f"Rozet listesi hatası: Kullanıcı={goruntulenen_kullanici.username}, Hata={e}", exc_info=True)
        kullanici_rozetleri = []

    # ==================== OYUN İSTATİSTİKLERİ ====================
    cache_key_oyun = f'oyun_ist_{profil.id}'
    oyun_istatistikleri = cache.get(cache_key_oyun)
    if oyun_istatistikleri is None:
        try:
            oyun_istatistikleri = list(OyunModuIstatistik.objects.filter(profil=profil).select_related('profil'))
            cache.set(cache_key_oyun, oyun_istatistikleri, 60)
        except Exception as e:
            logger.error(f"Oyun istatistik hatası: Kullanıcı={goruntulenen_kullanici.username}, Hata={e}", exc_info=True)
            oyun_istatistikleri = []

    # Template'in beklediği ayrı değişkenler
    karsilasma_ist = None
    bulbakalim_ist = None
    tabu_ist = None
    for ist in oyun_istatistikleri:
        if ist.oyun_modu == 'karsilasma':
            karsilasma_ist = ist
        elif ist.oyun_modu == 'bul_bakalim':
            bulbakalim_ist = ist
        elif ist.oyun_modu == 'tabu':
            tabu_ist = ist

    # ==================== DERS İSTATİSTİKLERİ ====================
    cache_key_ders = f'ders_ist_{profil.id}'
    ders_istatistikleri = cache.get(cache_key_ders)
    if ders_istatistikleri is None:
        try:
            ders_istatistikleri = list(
                DersIstatistik.objects.filter(profil=profil).select_related('profil').order_by('-toplam_puan')[:5]
            )
            cache.set(cache_key_ders, ders_istatistikleri, 60)
        except Exception as e:
            logger.error(f"Ders istatistik hatası: Kullanıcı={goruntulenen_kullanici.username}, Hata={e}", exc_info=True)
            ders_istatistikleri = []

    # ==================== LİDERLİK SIRASI ====================
    cache_key_sira = f'liderlik_sira_{profil.id}_{profil.toplam_puan}'
    kullanici_sira = cache.get(cache_key_sira)
    if kullanici_sira is None:
        try:
            kullanici_sira = OgrenciProfili.objects.filter(toplam_puan__gt=profil.toplam_puan).count() + 1
            cache.set(cache_key_sira, kullanici_sira, 120)
        except Exception as e:
            logger.error(f"Liderlik sıra hatası: Kullanıcı={goruntulenen_kullanici.username}, Hata={e}", exc_info=True)
            kullanici_sira = 0

    # ==================== BAŞARI ORANI ====================
    toplam_soru = profil.toplam_dogru + profil.toplam_yanlis
    basari_orani = round((profil.toplam_dogru / toplam_soru) * 100, 1) if toplam_soru > 0 else 0

    # ==================== ARKADAŞLIK DURUMU ====================
    arkadaslik_durumu = None
    if goruntulenen_kullanici != request.user:
        istek = Arkadaslik.objects.filter(
            Q(gonderen=request.user, alan=goruntulenen_kullanici) |
            Q(gonderen=goruntulenen_kullanici, alan=request.user)
        ).first()
        if istek:
            if istek.durum == 'kabul_edildi':
                arkadaslik_durumu = 'arkadas'
            elif istek.durum == 'beklemede':
                arkadaslik_durumu = 'beklemede'

    # ==================== GELEN MEYDAN OKUMA SAYISI ====================
    gelen_meydan_sayisi = 0
    if goruntulenen_kullanici == request.user:
        try:
            from quiz.models import MeydanOkuma
            gelen_meydan_sayisi = MeydanOkuma.objects.filter(
                alan=request.user,
                durum='beklemede'
            ).count()
        except Exception as e:
            logger.error(f"Meydan okuma sayısı hatası: {e}", exc_info=True)

    # ==================== GÜNLÜK GÖREVLER ====================
    bugun_tamamlanan = 0
    bugun_toplam = 0
    if goruntulenen_kullanici == request.user:
        try:
            from profile.gorev_helper import bugunun_gorevlerini_getir
            gorevler = bugunun_gorevlerini_getir(profil)
            bugun_toplam = gorevler.count()
            bugun_tamamlanan = gorevler.filter(tamamlandi_mi=True).count()
        except Exception as e:
            logger.error(f"Günlük görev context hatası: {e}", exc_info=True)

    # ==================== SON 7 GÜN STREAK ====================
    son_7_gun = _son_7_gun_hesapla()

    # ==================== CONTEXT ====================
    context = {
        'goruntulenen_kullanici': goruntulenen_kullanici,
        'profil': profil,
        'kullanici_rozetleri': kullanici_rozetleri,
        'oyun_istatistikleri': oyun_istatistikleri,
        'karsilasma_ist': karsilasma_ist,
        'bulbakalim_ist': bulbakalim_ist,
        'tabu_ist': tabu_ist,
        'ders_istatistikleri': ders_istatistikleri,
        'sira': kullanici_sira,
        'basari_orani': basari_orani,
        'arkadaslik_durumu': arkadaslik_durumu,
        'son_7_gun': son_7_gun,
        'bugun_tamamlanan': bugun_tamamlanan,
        'bugun_toplam': bugun_toplam,
        'gelen_meydan_sayisi': gelen_meydan_sayisi,
    }

    return render(request, 'profil.html', context)


@login_required
def profil_duzenle_view(request):
    try:
        profil = OgrenciProfili.objects.select_related('kullanici').get(kullanici=request.user)
    except OgrenciProfili.DoesNotExist:
        try:
            profil = OgrenciProfili.objects.create(kullanici=request.user, alan='sayisal')
        except IntegrityError as e:
            logger.error(f"Profil oluşturma hatası: {e}", exc_info=True)
            messages.error(request, 'Profil oluşturulurken bir hata oluştu.')
            return redirect('profil')

    # Envanter getir
    from magaza.models import KullaniciEnvanter, SatinAlma
    envanter, _ = KullaniciEnvanter.objects.get_or_create(kullanici=request.user)
    sahip_olunan_ids = set(
        SatinAlma.objects.filter(kullanici=request.user).values_list('urun_id', flat=True)
    )

    # Sahip olunan ürünleri kategoriye göre ayır
    from magaza.models import MagazaUrun
    sahip_unvanlar = MagazaUrun.objects.filter(id__in=sahip_olunan_ids, kategori='unvan')
    sahip_cerceveler = MagazaUrun.objects.filter(id__in=sahip_olunan_ids, kategori='cerceve')
    sahip_temalar = MagazaUrun.objects.filter(id__in=sahip_olunan_ids, kategori='tema')
    sahip_avatar_urunler = MagazaUrun.objects.filter(id__in=sahip_olunan_ids, kategori='avatar')

    # Avatar listesi: ücretsizler + satın alınanlar
    from profile.avatar_listesi import UCRETSIZ_AVATARLAR, UCRETSIZ_EMOJI_SETI
    premium_avatarlar = [
        {'emoji': u.avatar_emoji, 'isim': u.isim, 'premium': True}
        for u in sahip_avatar_urunler if u.avatar_emoji
    ]
    tum_kullanilabilir_avatarlar = [
        {**a, 'premium': False} for a in UCRETSIZ_AVATARLAR
    ] + premium_avatarlar

    if request.method == 'POST':
        alan = request.POST.get('alan')
        ad = request.POST.get('ad', '').strip()
        soyad = request.POST.get('soyad', '').strip()
        hedef_puan = request.POST.get('hedef_puan')
        secilen_avatar = request.POST.get('avatar')

        # Mağaza seçimleri
        aktif_unvan_id = request.POST.get('aktif_unvan')
        aktif_cerceve_id = request.POST.get('aktif_cerceve')
        aktif_tema_id = request.POST.get('aktif_tema')

        try:
            with transaction.atomic():
                if alan:
                    profil.alan = alan
                # Avatar güvenlik kontrolü
                if secilen_avatar:
                    satin_alinan_emojiler = {u.avatar_emoji for u in sahip_avatar_urunler if u.avatar_emoji}
                    from profile.avatar_listesi import avatar_gecerli_mi
                    if avatar_gecerli_mi(secilen_avatar, satin_alinan_emojiler):
                        profil.avatar = secilen_avatar
                if ad:
                    profil.ad = ad
                if soyad:
                    profil.soyad = soyad
                if hedef_puan:
                    profil.hedef_puan = hedef_puan
                profil.save()

                # Envanter güncelle
                if aktif_unvan_id:
                    if aktif_unvan_id == 'kaldir':
                        envanter.aktif_unvan = None
                    else:
                        try:
                            unvan = MagazaUrun.objects.get(id=aktif_unvan_id, kategori='unvan')
                            if int(aktif_unvan_id) in sahip_olunan_ids:
                                envanter.aktif_unvan = unvan
                        except MagazaUrun.DoesNotExist:
                            pass

                if aktif_cerceve_id:
                    if aktif_cerceve_id == 'kaldir':
                        envanter.aktif_cerceve = None
                    else:
                        try:
                            cerceve = MagazaUrun.objects.get(id=aktif_cerceve_id, kategori='cerceve')
                            if int(aktif_cerceve_id) in sahip_olunan_ids:
                                envanter.aktif_cerceve = cerceve
                        except MagazaUrun.DoesNotExist:
                            pass

                if aktif_tema_id:
                    if aktif_tema_id == 'kaldir':
                        envanter.aktif_tema = None
                    else:
                        try:
                            tema = MagazaUrun.objects.get(id=aktif_tema_id, kategori='tema')
                            if int(aktif_tema_id) in sahip_olunan_ids:
                                envanter.aktif_tema = tema
                        except MagazaUrun.DoesNotExist:
                            pass

                envanter.save()

                # Cache temizle
                cache_keys = [
                    f'rozet_kontrol_{profil.id}_{profil.cozulen_soru_sayisi}',
                    f'oyun_ist_{profil.id}',
                    f'liderlik_sira_{profil.id}_{profil.toplam_puan}',
                ]
                for key in cache_keys:
                    cache.delete(key)

            messages.success(request, '✅ Profil güncellendi!')
            return redirect('profil')

        except ValidationError as e:
            messages.error(request, 'Girdiğiniz bilgiler geçersiz.')
        except Exception as e:
            logger.error(f"Profil güncelleme hatası: {e}", exc_info=True)
            messages.error(request, 'Bir hata oluştu.')

    context = {
        'profil': profil,
        'envanter': envanter,
        'sahip_unvanlar': sahip_unvanlar,
        'sahip_cerceveler': sahip_cerceveler,
        'sahip_temalar': sahip_temalar,
        'tum_kullanilabilir_avatarlar': tum_kullanilabilir_avatarlar,
        'alan_secenekleri': OgrenciProfili.ALAN_SECENEKLERI,
    }
    return render(request, 'profil_duzenle.html', context)


@login_required
def liderlik_view(request):
    """Liderlik tablosu - 5 farklı kategori"""

    try:
        profil = request.user.profil
        profil.reset_kontrolu()
    except AttributeError:
        logger.error(f"Liderlik profil erişim hatası: Kullanıcı={request.user.username}")
        messages.error(request, 'Profil bulunamadı.')
        return redirect('profil')

    kategori = request.GET.get('kategori', 'haftalik')
    cache_key = f'liderlik_{kategori}'
    cached_data = cache.get(cache_key)

    if cached_data is None:
        logger.debug(f"Liderlik cache'den alınamadı: Kategori={kategori}")

        try:
            if kategori == 'gunluk':
                liderler = OgrenciProfili.objects.filter(aktif_mi=True).select_related('kullanici').only(
                    'kullanici__username', 'gunluk_puan', 'toplam_puan',
                    'gunluk_dogru', 'gunluk_yanlis', 'cozulen_soru_sayisi', 'alan', 'seviye', 'xp'
                ).order_by('-gunluk_puan', '-seviye', '-xp', '-toplam_puan')[:50]
                baslik = "Günlük Liderlik"
                puan_alani = 'gunluk_puan'

            elif kategori == 'haftalik':
                liderler = OgrenciProfili.objects.filter(aktif_mi=True).select_related('kullanici').only(
                    'kullanici__username', 'haftalik_puan', 'toplam_puan',
                    'haftalik_dogru', 'haftalik_yanlis', 'cozulen_soru_sayisi', 'alan', 'seviye', 'xp'
                ).order_by('-haftalik_puan', '-seviye', '-xp', '-toplam_puan')[:50]
                baslik = "Haftalık Liderlik"
                puan_alani = 'haftalik_puan'

            elif kategori == 'aylik':
                liderler = OgrenciProfili.objects.filter(aktif_mi=True).select_related('kullanici').only(
                    'kullanici__username', 'aylik_puan', 'toplam_puan',
                    'aylik_dogru', 'aylik_yanlis', 'cozulen_soru_sayisi', 'alan', 'seviye', 'xp'
                ).order_by('-aylik_puan', '-seviye', '-xp', '-toplam_puan')[:50]
                baslik = "Aylık Liderlik"
                puan_alani = 'aylik_puan'

            elif kategori == 'seviye':
                liderler = OgrenciProfili.objects.filter(aktif_mi=True).select_related('kullanici').only(
                    'kullanici__username', 'seviye', 'xp', 'toplam_puan',
                    'toplam_dogru', 'toplam_yanlis', 'cozulen_soru_sayisi', 'alan'
                ).order_by('-seviye', '-xp', '-toplam_puan')[:50]
                baslik = "Seviye Liderliği"
                puan_alani = 'seviye'

            else:  # tum_zamanlar
                liderler = OgrenciProfili.objects.filter(aktif_mi=True).select_related('kullanici').only(
                    'kullanici__username', 'toplam_puan', 'cozulen_soru_sayisi',
                    'toplam_dogru', 'toplam_yanlis', 'alan', 'seviye', 'xp'
                ).order_by('-toplam_puan', '-seviye', '-xp', '-cozulen_soru_sayisi')[:50]
                baslik = "Tüm Zamanlar"
                puan_alani = 'toplam_puan'

            cached_data = {
                'liderler': list(liderler),
                'baslik': baslik,
                'puan_alani': puan_alani,
            }
            cache.set(cache_key, cached_data, 120)

        except Exception as e:
            logger.error(f"Liderlik verileri hatası: Kategori={kategori}, Hata={e}", exc_info=True)
            cached_data = {'liderler': [], 'baslik': 'Liderlik', 'puan_alani': 'toplam_puan'}

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
        elif kategori == 'seviye':
            kullanici_siralama = OgrenciProfili.objects.filter(aktif_mi=True).filter(
                models.Q(seviye__gt=profil.seviye) |
                models.Q(seviye=profil.seviye, xp__gt=profil.xp)
            ).count() + 1
            kullanici_puan = f"Lv.{profil.seviye} ({profil.xp} XP)"
        else:
            kullanici_siralama = profil.genel_siralama
            kullanici_puan = profil.toplam_puan
    except Exception as e:
        logger.error(f"Kullanıcı sıralama hatası: Kullanıcı={request.user.username}, Hata={e}", exc_info=True)
        kullanici_siralama = 0
        kullanici_puan = 0

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
        try:
            if alan_filtresi == 'genel':
                liderler = OgrenciProfili.objects.select_related('kullanici').only(
                    'kullanici__username', 'toplam_puan', 'haftalik_puan', 'cozulen_soru_sayisi'
                )
            else:
                liderler = OgrenciProfili.objects.select_related('kullanici').filter(alan=alan_filtresi).only(
                    'kullanici__username', 'toplam_puan', 'haftalik_puan', 'alan'
                )

            if sirala_tipi == 'haftalik':
                liderler = liderler.order_by('-haftalik_puan', '-toplam_puan')[:50]
            else:
                liderler = liderler.order_by('-toplam_puan', '-haftalik_puan')[:50]

            liderler = list(liderler)
            cache.set(cache_key, liderler, 180)

        except Exception as e:
            logger.error(f"Genel liderlik hatası: Tip={sirala_tipi}, Alan={alan_filtresi}, Hata={e}", exc_info=True)
            liderler = []

    alan_tercihleri = [
        ('genel', 'Tüm Alanlar'), ('sayisal', 'Sayısal'),
        ('sozel', 'Sözel'), ('esit_agirlik', 'Eşit Ağırlık'), ('dil', 'Dil')
    ]
    context = {
        'liderler': liderler,
        'sirala_tipi': sirala_tipi,
        'alan_filtresi': alan_filtresi,
        'alan_tercihleri': alan_tercihleri,
        'sayfa_baslik': 'Genel Liderlik Tablosu',
    }
    return render(request, 'liderlik_genel.html', context)


@login_required
def liderlik_oyun_modu_view(request):
    oyun_modu = request.GET.get('mod', 'karsilasma')
    sirala_tipi = request.GET.get('tip', 'toplam')

    cache_key = f'liderlik_oyun_{oyun_modu}_{sirala_tipi}'
    liderler = cache.get(cache_key)

    if liderler is None:
        try:
            if sirala_tipi == 'haftalik':
                liderler = OyunModuIstatistik.objects.filter(oyun_modu=oyun_modu).select_related(
                    'profil__kullanici'
                ).only(
                    'profil__kullanici__username', 'haftalik_puan', 'toplam_puan', 'oynanan_oyun_sayisi'
                ).order_by('-haftalik_puan', '-toplam_puan')[:50]
            else:
                liderler = OyunModuIstatistik.objects.filter(oyun_modu=oyun_modu).select_related(
                    'profil__kullanici'
                ).only(
                    'profil__kullanici__username', 'toplam_puan', 'oynanan_oyun_sayisi'
                ).order_by('-toplam_puan', '-haftalik_puan')[:50]

            liderler = list(liderler)
            cache.set(cache_key, liderler, 180)

        except Exception as e:
            logger.error(f"Oyun modu liderlik hatası: Mod={oyun_modu}, Tip={sirala_tipi}, Hata={e}", exc_info=True)
            liderler = []

    context = {
        'liderler': liderler,
        'oyun_modu': oyun_modu,
        'sirala_tipi': sirala_tipi,
        'sayfa_baslik': f"{'Karşılaşma' if oyun_modu == 'karsilasma' else 'Bul Bakalım'} Liderliği",
    }
    return render(request, 'liderlik_oyun_modu.html', context)


@login_required
def liderlik_ders_view(request):
    ders = request.GET.get('ders', 'matematik')
    sirala = request.GET.get('sirala', 'dogru')

    cache_key = f'liderlik_ders_{ders}_{sirala}'
    liderler = cache.get(cache_key)

    if liderler is None:
        try:
            if sirala == 'net':
                liderler = DersIstatistik.objects.filter(ders=ders).select_related('profil__kullanici').annotate(
                    hesaplanan_net=F('dogru_sayisi') - (F('yanlis_sayisi') / 4.0)
                ).order_by('-hesaplanan_net', '-dogru_sayisi')[:50]
            elif sirala == 'oran':
                liderler = DersIstatistik.objects.filter(ders=ders, cozulen_soru__gte=10).select_related(
                    'profil__kullanici'
                ).order_by('-dogru_sayisi', '-cozulen_soru')[:50]
            else:
                liderler = DersIstatistik.objects.filter(ders=ders).select_related('profil__kullanici').order_by(
                    '-dogru_sayisi', '-cozulen_soru'
                )[:50]

            liderler = list(liderler)
            cache.set(cache_key, liderler, 180)

        except Exception as e:
            logger.error(f"Ders liderlik hatası: Ders={ders}, Sıralama={sirala}, Hata={e}", exc_info=True)
            liderler = []

    ders_listesi = [
        ('matematik', 'Matematik'), ('fizik', 'Fizik'), ('kimya', 'Kimya'),
        ('biyoloji', 'Biyoloji'), ('turkce', 'Türkçe'), ('tarih', 'Tarih'),
        ('cografya', 'Coğrafya'), ('felsefe', 'Felsefe'), ('din', 'Din Kültürü'), ('ingilizce', 'İngilizce'),
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


@login_required
def konu_istatistik_view(request):
    cache_key = f'konu_ist_{request.user.id}'
    konu_istatistikleri = cache.get(cache_key)

    if konu_istatistikleri is None:
        from quiz.models import KullaniciCevap
        try:
            konu_istatistikleri = list(
                KullaniciCevap.objects.filter(kullanici=request.user).values('soru__konu__isim').annotate(
                    toplam=Count('id'),
                    dogru=Count('id', filter=Q(dogru_mu=True)),
                    yanlis=Count('id', filter=Q(dogru_mu=False))
                ).order_by('-toplam')
            )
            cache.set(cache_key, konu_istatistikleri, 300)
        except Exception as e:
            logger.error(f"Konu istatistik hatası: Kullanıcı={request.user.username}, Hata={e}", exc_info=True)
            konu_istatistikleri = []

    return render(request, 'konu_istatistik.html', {'konu_istatistikleri': konu_istatistikleri})


@login_required
def konu_analiz_view(request):
    cache_key = f'konu_analiz_{request.user.profil.id}'
    cached_data = cache.get(cache_key)

    if cached_data is None:
        try:
            profil = request.user.profil
            dersler = ['matematik', 'fizik', 'kimya', 'biyoloji', 'turkce']
            konu_istatistikleri = KonuIstatistik.objects.filter(profil=profil).select_related('profil')

            ders_konular_list = [
                {'ders': ders, 'konular': list(konu_istatistikleri.filter(ders=ders))}
                for ders in dersler
            ]

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

            tum_rozet_tanimi = [
                {'kategori': kategori, 'seviye': seviye}
                for kategori, _ in Rozet.KATEGORI_SECENEKLERI
                for seviye, _ in Rozet.SEVIYE_SECENEKLERI
            ]

            kazanilan_set = {(r.kategori, r.seviye) for r in kazanilan_rozetler}

            ICON_MAP = {
                'yeni_uye': '🌱', 'aktif_kullanici': '⚡', 'gun_asimi': '📅',
                'hafta_sampionu': '👑', 'soru_cozucu': '📝', 'dogru_ustasi': '✅',
                'net_avcisi': '🎯', 'hatasiz_kusursuz': '💯', 'matematik_dehasi': '🔢',
                'fizik_profesoru': '⚛️', 'kimya_uzman': '🧪', 'biyoloji_bilgini': '🧬',
                'turkce_edebiyatci': '📖', 'tarih_bilgesi': '🏛️', 'cografya_gezgini': '🌍',
                'felsefe_dusunuru': '💭', 'karsilasma_savaslisi': '⚔️', 'bul_bakalim_ustasi': '💡',
                'tabu_kral': '🎭', 'galip_aslan': '🦁', 'lider_zirve': '🏆',
                'top_10': '🥇', 'top_50': '🥈', 'zirve_fatih': '👑',
                'hizli_cevap': '⚡', 'gece_kusu': '🦉', 'sabah_kusagu': '🌅',
                'maraton_kosucu': '🏃', 'yardimci': '🤝', 'ogretmen': '👨\u200d🏫',
                'ilham_verici': '✨', 'takım_oyuncusu': '👥',
            }

            kazanilmamis_rozetler = [
                {
                    'kategori': t['kategori'],
                    'seviye': t['seviye'],
                    'isim': dict(Rozet.KATEGORI_SECENEKLERI).get(t['kategori'], 'Bilinmeyen'),
                    'emoji': ICON_MAP.get(t['kategori'], '🏅'),
                    'aciklama': ROZET_ACIKLAMALARI.get(t['kategori'], {}).get(t['seviye'], 'Açıklama bulunamadı.'),
                }
                for t in tum_rozet_tanimi
                if (t['kategori'], t['seviye']) not in kazanilan_set
            ]

            cached_context = {
                'kazanilan_rozetler': list(kazanilan_rozetler),
                'kazanilmamis_rozetler': kazanilmamis_rozetler,
                'kazanilan_sayi': kazanilan_rozetler.count(),
                'toplam_rozet': len(tum_rozet_tanimi),
            }
            cache.set(cache_key, cached_context, 180)

        except Exception as e:
            logger.error(f"Rozet listesi hatası: Kullanıcı={request.user.username}, Hata={e}", exc_info=True)
            cached_context = {
                'kazanilan_rozetler': [], 'kazanilmamis_rozetler': [],
                'kazanilan_sayi': 0, 'toplam_rozet': 0,
            }

    return render(request, 'rozetler.html', cached_context)


@login_required
def bildirimler_json(request):
    try:
        bildirimler = Bildirim.objects.filter(
            kullanici=request.user,
            okundu_mu=False,
            silindi_mi=False  # ✅ silinenleri gösterme
        ).select_related('iliskili_rozet').order_by('-olusturma_tarihi')[:15]

        data = [{
            'id': b.id,
            'tip': b.tip,
            'baslik': b.baslik,
            'mesaj': b.mesaj,
            'icon': b.icon,
            'renk': b.renk,
            'link': b.link or '',
            'tarih': b.olusturma_tarihi.strftime('%d.%m.%Y %H:%M'),
            'sure': _zaman_once(b.olusturma_tarihi),
        } for b in bildirimler]

        toplam = Bildirim.objects.filter(
            kullanici=request.user,
            okundu_mu=False,
            silindi_mi=False
        ).count()

        return JsonResponse({'bildirimler': data, 'toplam': toplam})

    except Exception as e:
        logger.error(f'Bildirim JSON hatası: {e}', exc_info=True)
        return JsonResponse({'bildirimler': [], 'toplam': 0}, status=500)


def _zaman_once(tarih):
    """'5 dk önce' formatında zaman döndür"""
    from django.utils import timezone
    fark = timezone.now() - tarih
    saniye = int(fark.total_seconds())
    if saniye < 60:
        return 'Az önce'
    elif saniye < 3600:
        return f'{saniye // 60} dk önce'
    elif saniye < 86400:
        return f'{saniye // 3600} sa önce'
    else:
        return f'{saniye // 86400} gün önce'


@login_required
def bildirim_okundu(request, bildirim_id):
    if request.method != 'POST':
        return JsonResponse({'success': False}, status=400)
    try:
        bildirim = Bildirim.objects.get(id=bildirim_id, kullanici=request.user)
        bildirim.okundu_mu = True
        bildirim.save()
        return JsonResponse({'success': True})
    except Bildirim.DoesNotExist:
        return JsonResponse({'success': False}, status=404)


@login_required
def bildirim_sil(request, bildirim_id):
    """✅ YENİ - Bildirimi sil"""
    if request.method != 'POST':
        return JsonResponse({'success': False}, status=400)
    try:
        bildirim = Bildirim.objects.get(id=bildirim_id, kullanici=request.user)
        bildirim.silindi_mi = True
        bildirim.okundu_mu = True
        bildirim.save()
        return JsonResponse({'success': True})
    except Bildirim.DoesNotExist:
        return JsonResponse({'success': False}, status=404)


@login_required
def tum_bildirimleri_okundu_yap(request):
    if request.method != 'POST':
        return JsonResponse({'success': False}, status=400)
    try:
        guncellenen = Bildirim.objects.filter(
            kullanici=request.user,
            okundu_mu=False,
            silindi_mi=False
        ).update(okundu_mu=True)
        return JsonResponse({'success': True, 'guncellenen': guncellenen})
    except Exception as e:
        return JsonResponse({'success': False}, status=500)


@login_required
def bildirimler_sayfa(request):
    try:
        bildirimler = Bildirim.objects.filter(
            kullanici=request.user,
            silindi_mi=False  # ✅ silinenleri gösterme
        ).select_related('iliskili_rozet').order_by('-olusturma_tarihi')[:50]

        context = {
            'bildirimler': bildirimler,
            'okunmamis_sayisi': Bildirim.objects.filter(
                kullanici=request.user,
                okundu_mu=False,
                silindi_mi=False
            ).count(),
        }
        return render(request, 'bildirimler.html', context)
    except Exception as e:
        logger.error(f'Bildirimler sayfa hatası: {e}', exc_info=True)
        return redirect('profil')


@login_required
def arkadaslarim(request):
    arkadaslar = Arkadaslik.arkadaslari_getir(request.user)
    bekleyen_istekler = Arkadaslik.bekleyen_istekler(request.user)
    gonderilen_istekler = Arkadaslik.objects.filter(
        gonderen=request.user, durum='beklemede'
    ).select_related('alan', 'alan__profil')

    # AKTİVİTE FEEDİ
    from django.utils import timezone
    from datetime import timedelta
    from profile.models import XPGecmisi, CalismaKaydi

    # Arkadaşların profillerini al
    arkadas_profiller = []
    for arkadas in arkadaslar:
        if arkadas != request.user:
            try:
                arkadas_profiller.append(arkadas.profil)
            except:
                pass

    # Son 7 günün aktivitelerini çek
    yedi_gun_once = timezone.now() - timedelta(days=7)

    aktiviteler = []

    # XP kazanımları
    xp_kayitlari = XPGecmisi.objects.filter(
        profil__in=arkadas_profiller,
        tarih__gte=yedi_gun_once
    ).select_related('profil__kullanici').order_by('-tarih')[:50]

    for kayit in xp_kayitlari:
        # İkon belirle
        if 'Doğru' in kayit.sebep:
            icon = '⚡'
            tur = 'soru'
        elif 'giriş' in kayit.sebep.lower():
            icon = '🎁'
            tur = 'giris'
        elif 'Karşılaşma' in kayit.sebep:
            icon = '⚔️'
            tur = 'oyun'
        elif 'Bul Bakalım' in kayit.sebep:
            icon = '💡'
            tur = 'oyun'
        elif 'Rozet' in kayit.sebep:
            icon = '🏆'
            tur = 'rozet'
        elif 'Seviye' in kayit.sebep:
            icon = '⭐'
            tur = 'seviye'
        elif 'Görev' in kayit.sebep or 'görev' in kayit.sebep:
            icon = '🎯'
            tur = 'gorev'
        elif 'Tabu' in kayit.sebep:
            icon = '🎴'
            tur = 'oyun'
        elif 'Streak' in kayit.sebep or 'streak' in kayit.sebep:
            icon = '🔥'
            tur = 'streak'
        else:
            icon = '⭐'
            tur = 'diger'

        aktiviteler.append({
            'profil': kayit.profil,
            'icon': icon,
            'baslik': kayit.sebep,
            'xp': kayit.miktar,
            'tarih': kayit.tarih,
            'tur': tur,
        })

    # Tarihe göre sırala
    aktiviteler.sort(key=lambda x: x['tarih'], reverse=True)
    aktiviteler = aktiviteler[:30]  # En son 30 aktivite

    context = {
        'arkadaslar': arkadaslar,
        'bekleyen_istekler': bekleyen_istekler,
        'gonderilen_istekler': gonderilen_istekler,
        'aktiviteler': aktiviteler,
        'arkadas_profiller': arkadas_profiller,
    }
    return render(request, 'arkadaslarim.html', context)


@login_required
def arkadas_ara(request):
    query = request.GET.get('q', '').strip()
    sonuclar = []

    if query and len(query) >= 2:
        sonuclar = User.objects.filter(
            username__icontains=query
        ).exclude(id=request.user.id).select_related('profil')[:20]

        for kullanici in sonuclar:
            istek = Arkadaslik.objects.filter(
                Q(gonderen=request.user, alan=kullanici) |
                Q(gonderen=kullanici, alan=request.user)
            ).first()

            if istek:
                if istek.durum == 'kabul_edildi':
                    kullanici.arkadaslik_durumu = 'arkadas'
                elif istek.durum == 'beklemede':
                    kullanici.arkadaslik_durumu = 'istek_gonderildi' if istek.gonderen == request.user else 'istek_geldi'
                else:
                    kullanici.arkadaslik_durumu = 'yok'
            else:
                kullanici.arkadaslik_durumu = 'yok'

    context = {'query': query, 'sonuclar': sonuclar}
    return render(request, 'arkadas_ara.html', context)


@login_required
def arkadaslik_istek_gonder(request, kullanici_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'POST gerekli'}, status=400)

    try:
        alan = User.objects.get(id=kullanici_id)

        if alan == request.user:
            return JsonResponse({'success': False, 'message': 'Kendinize istek gönderemezsiniz!'})

        # Zaten arkadaş mı?
        if Arkadaslik.arkadaslar_mi(request.user, alan):
            return JsonResponse({'success': False, 'message': 'Zaten arkadaşsınız!'})

        # Daha önce istek gönderilmiş mi?
        mevcut = Arkadaslik.objects.filter(
            gonderen=request.user,
            alan=alan,
            durum='beklemede'
        ).first()
        if mevcut:
            return JsonResponse({'success': False, 'message': 'Zaten istek gönderildi!'})

        # Karşı taraftan istek gelmiş mi?
        gelen = Arkadaslik.objects.filter(
            gonderen=alan,
            alan=request.user,
            durum='beklemede'
        ).first()
        if gelen:
            # Otomatik kabul et
            gelen.durum = 'kabul_edildi'
            gelen.save()
            return JsonResponse({'success': True, 'message': f'{alan.username} senden zaten istek göndermişti, arkadaş oldunuz! 🎉'})

        # Yeni istek oluştur
        Arkadaslik.objects.create(
            gonderen=request.user,
            alan=alan,
            durum='beklemede'
        )

        # Bildirim gönder (varsa)
        try:
            from profile.models import Bildirim
            Bildirim.objects.create(
                kullanici=alan,
                baslik='Yeni Arkadaşlık İsteği! 👥',
                mesaj=f'{request.user.username} sana arkadaşlık isteği gönderdi!',
                ikon='👥',
                bildirim_turu='arkadaslik',
            )
        except Exception:
            pass

        return JsonResponse({
            'success': True,
            'message': f'{alan.username} kullanıcısına arkadaşlık isteği gönderildi! 🎉'
        })

    except User.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Kullanıcı bulunamadı!'}, status=404)
    except Exception as e:
        logger.error(f"Arkadaşlık isteği hatası: {e}", exc_info=True)
        return JsonResponse({'success': False, 'message': 'Bir hata oluştu!'}, status=500)


@login_required
def arkadaslik_istek_kabul(request, istek_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'POST gerekli'}, status=400)
    return JsonResponse(arkadaslik_istegi_kabul_et(istek_id, request.user))


@login_required
def arkadaslik_istek_reddet(request, istek_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'POST gerekli'}, status=400)
    return JsonResponse(arkadaslik_istegi_reddet(istek_id, request.user))


@login_required
def arkadas_cikar(request, kullanici_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'POST gerekli'}, status=400)

    try:
        arkadas = User.objects.get(id=kullanici_id)
        return JsonResponse(arkadasliktan_cikar(request.user, arkadas))
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Kullanıcı bulunamadı!'}, status=404)


def yardim_merkezi(request):
    return render(request, 'yardim_merkezi.html')


def sss(request):
    return render(request, 'sss.html')


def iletisim(request):
    return render(request, 'iletisim.html')


def gizlilik_politikasi(request):
    return render(request, 'gizlilik_politikasi.html')


def kullanim_kosullari(request):
    return render(request, 'kullanim_kosullari.html')


def hakkimizda(request):
    return render(request, 'hakkimizda.html')


@login_required
def admin_dashboard(request):
    """Özel admin dashboard - sadece superuser"""
    if not request.user.is_superuser:
        messages.error(request, 'Bu sayfaya erişim yetkiniz yok!')
        return redirect('profil')

    from django.contrib.auth.models import User
    from quiz.models import KarsilasmaOdasi, Soru, TabuKelime
    from profile.models import OgrenciProfili

    # Genel istatistikler
    toplam_kullanici = User.objects.count()
    aktif_kullanicilar = User.objects.filter(last_login__gte=timezone.now() - timezone.timedelta(days=7)).count()
    toplam_soru = Soru.objects.count()
    toplam_karsilasma = KarsilasmaOdasi.objects.filter(oyun_durumu='bitti').count()
    aktif_karsilasma = KarsilasmaOdasi.objects.filter(oyun_durumu='oynaniyor').count()
    bekleyen_karsilasma = KarsilasmaOdasi.objects.filter(oyun_durumu='bekleniyor').count()

    # Son kayıt olan kullanıcılar
    son_kullanicilar = User.objects.order_by('-date_joined')[:10]

    # En aktif kullanıcılar (son 7 gün)
    en_aktif = OgrenciProfili.objects.select_related('kullanici').order_by('-haftalik_cozulen')[:10]

    # Ders bazında soru dağılımı
    ders_dagilimi = Soru.objects.values('ders').annotate(sayi=Count('id')).order_by('-sayi')

    context = {
        'toplam_kullanici': toplam_kullanici,
        'aktif_kullanicilar': aktif_kullanicilar,
        'toplam_soru': toplam_soru,
        'toplam_karsilasma': toplam_karsilasma,
        'aktif_karsilasma': aktif_karsilasma,
        'bekleyen_karsilasma': bekleyen_karsilasma,
        'son_kullanicilar': son_kullanicilar,
        'en_aktif': en_aktif,
        'ders_dagilimi': ders_dagilimi,
    }
    return render(request, 'admin_dashboard.html', context)


@login_required
def seviye_oduller_view(request):
    """Seviye ödülleri ve ilerleme sayfası"""
    profil = request.user.profil

    # Seviye tablosu: seviye, xp eşiği, unvan, ödül puanı
    seviye_tablosu = [
        {'seviye': 1,  'xp': 0,      'unvan': '🐣 Çaylak',           'odul_puan': 0},
        {'seviye': 2,  'xp': 100,    'unvan': '🌱 Acemi',            'odul_puan': 20},
        {'seviye': 3,  'xp': 250,    'unvan': '⚡ Hızlı Başlangıç',  'odul_puan': 30},
        {'seviye': 4,  'xp': 500,    'unvan': '🔥 Ateşli',           'odul_puan': 50},
        {'seviye': 5,  'xp': 1000,   'unvan': '💪 Güçlü',            'odul_puan': 75},
        {'seviye': 6,  'xp': 1500,   'unvan': '🎯 Hedef Odaklı',    'odul_puan': 100},
        {'seviye': 7,  'xp': 2500,   'unvan': '🚀 Roket',            'odul_puan': 150},
        {'seviye': 8,  'xp': 4000,   'unvan': '⭐ Yıldız',           'odul_puan': 200},
        {'seviye': 9,  'xp': 6000,   'unvan': '💎 Elmas',            'odul_puan': 250},
        {'seviye': 10, 'xp': 8500,   'unvan': '🏆 Usta',             'odul_puan': 350},
        {'seviye': 11, 'xp': 12000,  'unvan': '👑 Kral Adayı',      'odul_puan': 450},
        {'seviye': 12, 'xp': 16000,  'unvan': '🦅 Kartal',           'odul_puan': 550},
        {'seviye': 13, 'xp': 20000,  'unvan': '🔱 Gladyatör',       'odul_puan': 700},
        {'seviye': 14, 'xp': 25000,  'unvan': '⚔️ Savaşçı',        'odul_puan': 850},
        {'seviye': 15, 'xp': 30000,  'unvan': '👑 Kral',             'odul_puan': 1000},
        {'seviye': 16, 'xp': 40000,  'unvan': '🌟 Süper Yıldız',    'odul_puan': 1250},
        {'seviye': 17, 'xp': 50000,  'unvan': '🏅 Şampiyon',        'odul_puan': 1500},
        {'seviye': 18, 'xp': 65000,  'unvan': '💫 Efsane Adayı',    'odul_puan': 2000},
        {'seviye': 19, 'xp': 80000,  'unvan': '🌠 Efsane',           'odul_puan': 2500},
        {'seviye': 20, 'xp': 100000, 'unvan': '🔥 Tanrı',            'odul_puan': 5000},
    ]

    for s in seviye_tablosu:
        s['ulasildi'] = profil.seviye >= s['seviye']
        s['aktif'] = profil.seviye == s['seviye']

    context = {
        'profil': profil,
        'seviye_tablosu': seviye_tablosu,
    }
    return render(request, 'seviye_oduller.html', context)