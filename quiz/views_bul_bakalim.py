from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.core.cache import cache
from django.db import IntegrityError
from django.urls import reverse
from quiz.models import Soru, Cevap, BulBakalimOyun
from profile.models import OyunModuIstatistik
from profile.rozet_kontrol import rozet_kontrol_yap
from profile.xp_helper import soru_cozuldu_xp, bul_bakalim_tamamlandi_xp
from profile.gorev_helper import gorev_ilerleme_guncelle, calisma_kaydi_guncelle
from profile.puan_helper import puan_ekle
import json
import random
import logging

logger = logging.getLogger(__name__)


@login_required
def bul_bakalim_sinav_tipi_secimi(request):
    sinav_tipi = request.GET.get('sinav_tipi')
    if sinav_tipi:
        request.session['bulbakalim_sinav_tipi'] = sinav_tipi.upper()
        logger.info(f"Bul Bakalım sınav tipi seçildi: Kullanıcı={request.user.username}, Sınav Tipi={sinav_tipi}")
        return redirect('bul_bakalim_ders_secimi')
    return render(request, 'quiz/bul_bakalim_sinav_tipi_secimi.html')


@login_required
def bul_bakalim_ders_secimi(request):
    sinav_tipi = request.GET.get('sinav_tipi') or request.session.get('bulbakalim_sinav_tipi', 'TYT')
    sinav_tipi = sinav_tipi.upper()
    request.session['bulbakalim_sinav_tipi'] = sinav_tipi
    context = {'sinav_tipi': sinav_tipi}
    return render(request, 'quiz/bul_bakalim_ders_secimi.html', context)


@login_required
def bul_bakalim_basla(request):
    ders = request.GET.get('ders', '').strip()
    sinav_tipi = request.GET.get('sinav_tipi') or request.session.get('bulbakalim_sinav_tipi', 'TYT')
    sinav_tipi = sinav_tipi.upper()

    if not ders:
        messages.error(request, 'Lütfen bir ders seçin!')
        return redirect('bul_bakalim_ders_secimi')

    logger.info(f"Bul Bakalım başlatılıyor: Kullanıcı={request.user.username}, Ders={ders}, Sınav Tipi={sinav_tipi}")

    cache_key = f'bulbakalim_sorular_{sinav_tipi}_{ders}'
    sorular = cache.get(cache_key)

    if sorular is None:
        if ders == 'karisik_sayisal':
            sorular = list(
                Soru.objects.filter(
                    ders__in=['matematik', 'fizik', 'kimya', 'biyoloji'],
                    bul_bakalimda_cikar=True,
                    sinav_tipi__iexact=sinav_tipi
                ).only('id').values_list('id', flat=True)
            )
        elif ders == 'karisik_sozel':
            sorular = list(
                Soru.objects.filter(
                    ders__in=['edebiyat', 'tarih', 'cografya', 'felsefe'],
                    bul_bakalimda_cikar=True,
                    sinav_tipi__iexact=sinav_tipi
                ).only('id').values_list('id', flat=True)
            )
        elif ders == 'karisik':
            sorular = list(
                Soru.objects.filter(
                    bul_bakalimda_cikar=True,
                    sinav_tipi__iexact=sinav_tipi
                ).only('id').values_list('id', flat=True)
            )
        else:
            sorular = list(
                Soru.objects.filter(
                    ders__iexact=ders,
                    bul_bakalimda_cikar=True,
                    sinav_tipi__iexact=sinav_tipi
                ).only('id').values_list('id', flat=True)
            )
        cache.set(cache_key, sorular, 300)
        logger.debug(f"Sorular cache'lendi: Ders={ders}, Sınav Tipi={sinav_tipi}, Sayı={len(sorular)}")

    if len(sorular) < 10:
        messages.error(request, f'"{ders}" dersinde yeterli soru bulunamadı! En az 10 soru gerekli.')
        logger.warning(f"Yetersiz soru: Ders={ders}, Sınav Tipi={sinav_tipi}, Sayı={len(sorular)}")
        return redirect('bul_bakalim_ders_secimi')

    secilen_sorular = random.sample(sorular, min(10, len(sorular)))
    yeni_oyun = BulBakalimOyun.objects.create(
        oyuncu=request.user,
        sorular=secilen_sorular,
        selected_ders=ders,
        sinav_tipi=sinav_tipi,
    )
    logger.info(f"Oyun oluşturuldu: Oyun ID={yeni_oyun.oyun_id}, Kullanıcı={request.user.username}")
    return redirect('bul_bakalim_oyun', oyun_id=yeni_oyun.oyun_id)


@login_required
def bul_bakalim_oyun(request, oyun_id):
    oyun = get_object_or_404(
        BulBakalimOyun.objects.select_related('oyuncu'),
        oyun_id=oyun_id,
        oyuncu=request.user
    )

    if oyun.oyun_durumu == 'bitti':
        return redirect('bul_bakalim_sonuc', oyun_id=oyun.oyun_id)

    cevaplanan_soru_sayisi = len(oyun.cevaplar)

    if cevaplanan_soru_sayisi >= len(oyun.sorular):
        oyun.oyun_bitir()
        logger.info(f"Bul Bakalım otomatik bitirildi: Oyun ID={oyun_id}")
        return redirect('bul_bakalim_sonuc', oyun_id=oyun.oyun_id)

    aktif_soru_id = oyun.sorular[cevaplanan_soru_sayisi]
    aktif_soru = Soru.objects.prefetch_related('cevaplar').get(id=aktif_soru_id)
    cevaplar = aktif_soru.cevaplar.all()

    context = {
        'oyun': oyun,
        'aktif_soru': aktif_soru,
        'cevaplar': cevaplar,
        'soru_no': cevaplanan_soru_sayisi + 1,
        'toplam_soru': len(oyun.sorular),
        'sure': 240,
    }
    return render(request, 'quiz/bul_bakalim_oyun.html', context)


@login_required
def bul_bakalim_cevapla(request, oyun_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request'}, status=400)

    oyun = get_object_or_404(
        BulBakalimOyun.objects.select_related('oyuncu'),
        oyun_id=oyun_id,
        oyuncu=request.user
    )

    if oyun.oyun_durumu == 'bitti':
        return JsonResponse({'error': 'Oyun bitti'}, status=400)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Geçersiz JSON'}, status=400)

    cevap_id = data.get('cevap_id')
    sure_doldu = data.get('sure_doldu', False)

    # Süre dolduysa cevapsız kaydet
    if sure_doldu and not cevap_id:
        cevaplanan = len(oyun.cevaplar)
        if cevaplanan < len(oyun.sorular):
            aktif_soru_id = oyun.sorular[cevaplanan]
            oyun.cevaplar[str(aktif_soru_id)] = None
            oyun.yanlis_sayisi += 1
            oyun.save()

        kalan_soru = len(oyun.sorular) - len(oyun.cevaplar)
        if kalan_soru <= 0:
            oyun.oyun_bitir()
            return JsonResponse({
                'oyun_bitti': True,
                'redirect_url': reverse('bul_bakalim_sonuc', args=[oyun.oyun_id]),
            })
        return JsonResponse({
            'oyun_bitti': False,
            'dogru_mu': False,
            'kalan_soru': kalan_soru,
            'dogru_sayisi': oyun.dogru_sayisi,
            'yanlis_sayisi': oyun.yanlis_sayisi,
        })

    if not cevap_id:
        return JsonResponse({'error': 'Cevap bulunamadı'}, status=400)

    try:
        cevap = Cevap.objects.select_related('soru').get(id=cevap_id)
    except Cevap.DoesNotExist:
        return JsonResponse({'error': 'Cevap geçersiz'}, status=404)

    soru = cevap.soru
    dogru_mu = cevap.dogru_mu

    oyun.cevaplar[str(soru.id)] = cevap_id
    if dogru_mu:
        oyun.dogru_sayisi += 1
        logger.debug(f"Doğru cevap: Oyun ID={oyun_id}, Soru ID={soru.id}")
    else:
        oyun.yanlis_sayisi += 1
        logger.debug(f"Yanlış cevap: Oyun ID={oyun_id}, Soru ID={soru.id}")
    oyun.save()

    seviye_atlandi = False
    yeni_seviye = 0
    yeni_unvan = ''

    try:
        profil = request.user.profil

        # ==================== PROFİL İSTATİSTİKLERİ ====================
        profil.cozulen_soru_sayisi += 1
        profil.haftalik_cozulen += 1
        if dogru_mu:
            profil.toplam_dogru += 1
            profil.haftalik_dogru += 1
        else:
            profil.toplam_yanlis += 1
            profil.haftalik_yanlis += 1
        profil.save()

        # ==================== XP ====================
        xp_sonuc = soru_cozuldu_xp(profil, dogru_mu)
        seviye_atlandi = xp_sonuc.get('seviye_atlandi', False)
        yeni_seviye = xp_sonuc.get('yeni_seviye', 0)
        yeni_unvan = xp_sonuc.get('unvan', '')

        # ==================== OYUN İSTATİSTİĞİ ====================
        oyun_ist, _ = OyunModuIstatistik.objects.get_or_create(
            profil=profil,
            oyun_modu='bul_bakalim'
        )
        oyun_ist.cozulen_soru += 1
        if dogru_mu:
            oyun_ist.dogru_sayisi += 1
        else:
            oyun_ist.yanlis_sayisi += 1
        oyun_ist.save()

        # ==================== GÖREV İLERLEMESİ ====================
        # Soru çözme görevi
        gorev_ilerleme_guncelle(profil, 'soru_coz', 1)

        # Doğru cevap görevi
        if dogru_mu:
            gorev_ilerleme_guncelle(profil, 'dogru_cevap', 1)

        # Çalışma kaydı güncelle
        calisma_kaydi_guncelle(
            profil,
            cozulen=1,
            dogru=1 if dogru_mu else 0,
            yanlis=0 if dogru_mu else 1,
            xp=5 if dogru_mu else 1,
        )

    except AttributeError as e:
        logger.error(f"Profil erişim hatası: Oyun ID={oyun_id}, Hata={e}", exc_info=True)
    except IntegrityError as e:
        logger.error(f"Veritabanı hatası: Oyun ID={oyun_id}, Hata={e}", exc_info=True)
    except Exception as e:
        logger.error(f"Beklenmeyen hata: Oyun ID={oyun_id}, Hata={e}", exc_info=True)

    kalan_soru = len(oyun.sorular) - len(oyun.cevaplar)
    if kalan_soru <= 0:
        oyun.oyun_bitir()
        logger.info(f"Oyun bitti: Oyun ID={oyun_id}, Doğru={oyun.dogru_sayisi}, Yanlış={oyun.yanlis_sayisi}")

        sonuc_url = reverse('bul_bakalim_sonuc', args=[oyun.oyun_id])
        response_data = {
            'oyun_bitti': True,
            'redirect_url': sonuc_url,
            'seviye_atlandi': seviye_atlandi,
        }
        if seviye_atlandi:
            response_data['yeni_seviye'] = yeni_seviye
            response_data['yeni_unvan'] = yeni_unvan
        return JsonResponse(response_data)

    response_data = {
        'dogru_mu': dogru_mu,
        'kalan_soru': kalan_soru,
        'dogru_sayisi': oyun.dogru_sayisi,
        'yanlis_sayisi': oyun.yanlis_sayisi,
        'seviye_atlandi': seviye_atlandi,
    }
    if seviye_atlandi:
        response_data['yeni_seviye'] = yeni_seviye
        response_data['yeni_unvan'] = yeni_unvan

    return JsonResponse(response_data)


@login_required
def bul_bakalim_sonuc(request, oyun_id):
    oyun = get_object_or_404(
        BulBakalimOyun.objects.select_related('oyuncu'),
        oyun_id=oyun_id,
        oyuncu=request.user
    )

    if oyun.oyun_durumu != 'bitti':
        oyun.oyun_bitir()

    sonuclar = []
    yanlislar = []
    soru_ids = oyun.sorular
    sorular = Soru.objects.filter(id__in=soru_ids).prefetch_related('cevaplar')
    soru_dict = {soru.id: soru for soru in sorular}

    for soru_id in oyun.sorular:
        try:
            soru = soru_dict.get(soru_id)
            if not soru:
                logger.warning(f"Soru bulunamadı: Oyun ID={oyun_id}, Soru ID={soru_id}")
                continue

            verilen_cevap_id = oyun.cevaplar.get(str(soru_id))
            dogru_cevap = next((c for c in soru.cevaplar.all() if c.dogru_mu), None)

            if verilen_cevap_id:
                verilen_cevap = next(
                    (c for c in soru.cevaplar.all() if c.id == int(verilen_cevap_id)),
                    None
                )
                dogru_mu = verilen_cevap.dogru_mu if verilen_cevap else False
            else:
                verilen_cevap = None
                dogru_mu = False

            sonuc_item = {
                'soru': soru,
                'verilen_cevap': verilen_cevap,
                'dogru_cevap': dogru_cevap,
                'dogru_mu': dogru_mu,
            }
            sonuclar.append(sonuc_item)
            if not dogru_mu:
                yanlislar.append(sonuc_item)

        except (ValueError, TypeError) as e:
            logger.error(f"Veri dönüşüm hatası: Oyun ID={oyun_id}, Soru ID={soru_id}, Hata={e}", exc_info=True)
            continue
        except AttributeError as e:
            logger.error(f"Nitelik hatası: Oyun ID={oyun_id}, Soru ID={soru_id}, Hata={e}", exc_info=True)
            continue
        except Exception as e:
            logger.error(f"Beklenmeyen hata: Oyun ID={oyun_id}, Soru ID={soru_id}, Hata={e}", exc_info=True)
            continue

    # Değişkenler başta tanımla
    kazanilan_puan = 0
    puan_carpani = 1.0
    puan_bonusu = 0
    kazandi = oyun.dogru_sayisi >= 6

    try:
        profil = request.user.profil

        # ==================== PUAN ====================
        if kazandi:
            puan_sonuc = puan_ekle(
                profil,
                taban_puan=10,
                sebep='Bul Bakalım kazanıldı',
                dogru=oyun.dogru_sayisi,
                toplam=10
            )
            kazanilan_puan = puan_sonuc['kazanilan_puan']
            puan_carpani = puan_sonuc['carpan']
            puan_bonusu = puan_sonuc['bonus_yuzdesi']

        # ==================== XP ====================
        xp_sonuc = bul_bakalim_tamamlandi_xp(profil)
        if xp_sonuc.get('seviye_atlandi'):
            messages.success(
                request,
                f"🎉 SEVİYE ATLADIN! Seviye {xp_sonuc['yeni_seviye']} - {xp_sonuc['unvan']}"
            )

        # ==================== OYUN İSTATİSTİĞİ ====================
        oyun_ist, _ = OyunModuIstatistik.objects.get_or_create(
            profil=profil,
            oyun_modu='bul_bakalim'
        )
        oyun_ist.oynanan_oyun_sayisi += 1
        oyun_ist.haftalik_oyun_sayisi += 1

        if kazandi:
            oyun_ist.kazanilan_oyun += 1
            logger.info(f"Kazanıldı: Kullanıcı={request.user.username}, Oyun ID={oyun_id}")
        else:
            oyun_ist.kaybedilen_oyun += 1
            logger.info(f"Kaybedildi: Kullanıcı={request.user.username}, Oyun ID={oyun_id}")

        oyun_ist.toplam_puan += kazanilan_puan
        oyun_ist.save()

        # ==================== GÖREV: BUL BAKALIM OYNANDI ====================
        tamamlanan = gorev_ilerleme_guncelle(profil, 'bul_bakalim_oyna', 1)
        for g in tamamlanan:
            messages.success(
                request,
                f"🎯 Görev tamamlandı: {g.sablon.icon} {g.sablon.isim} (+{g.sablon.odul_xp} XP)"
            )

        # ==================== ÇALIŞMA TAKVİMİ ====================
        calisma_kaydi_guncelle(profil, oyun=1)

        # ==================== ROZET KONTROLÜ ====================
        yeni_rozetler = rozet_kontrol_yap(profil)
        for rozet in (yeni_rozetler or []):
            messages.success(request, f'🏆 YENİ ROZET! {rozet.icon} {rozet.get_kategori_display()}')

    except Exception as e:
        logger.error(f"Sonuç istatistik hatası: Oyun ID={oyun_id}, Hata={e}", exc_info=True)

    context = {
        'oyun': oyun,
        'sonuclar': sonuclar,
        'yanlislar': yanlislar,
        'kazandi': kazandi,
        'aktif_ders': request.GET.get('ders', 'karisik'),
        # ✅ YENİ puan bilgileri
        'kazanilan_puan': kazanilan_puan,
        'puan_carpani': puan_carpani,
        'puan_bonusu': puan_bonusu,
    }
    return render(request, 'quiz/bul_bakalim_sonuc.html', context)