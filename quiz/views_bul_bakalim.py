from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.core.cache import cache
from django.db import IntegrityError
from quiz.models import Soru, Cevap, BulBakalimOyun
from profile.models import OyunModuIstatistik
from profile.rozet_kontrol import rozet_kontrol_yap
from profile.xp_helper import soru_cozuldu_xp, bul_bakalim_tamamlandi_xp  # XP HELPER IMPORT
import json
import random
import logging

logger = logging.getLogger(__name__)


@login_required
def bul_bakalim_sinav_tipi_secimi(request):
    if request.method == 'POST': 
        sinav_tipi = request.POST.get('sinav_tipi')
        request.session['bulbakalim_sinav_tipi'] = sinav_tipi
        logger.info(f"Bul Bakalım sınav tipi seçildi: Kullanıcı={request.user.username}, Sınav Tipi={sinav_tipi}")
        return redirect('bul_bakalim_ders_secimi')
    return render(request, 'quiz/bul_bakalim_sinav_tipi_secimi.html')


@login_required
def bul_bakalim_ders_secimi(request):
    sinav_tipi = request.session.get('bulbakalim_sinav_tipi', 'ayt')
    ders_secenekleri = BulBakalimOyun.DERS_SECENEKLERI
    if request.method == 'POST': 
        selected_ders = request.POST.get('selected_ders')
        logger.info(f"Bul Bakalım ders seçildi: Kullanıcı={request.user.username}, Ders={selected_ders}")
        return redirect('bul_bakalim_basla') + f'?ders={selected_ders}'
    context = {'ders_secenekleri':  ders_secenekleri, 'sinav_tipi':  sinav_tipi}
    return render(request, 'quiz/bul_bakalim_ders_secimi.html', context)


@login_required
def bul_bakalim_basla(request):
    ders = request.GET.get('ders')
    sinav_tipi = request.session.get('bulbakalim_sinav_tipi', 'ayt')
    logger.info(f"Bul Bakalım başlatılıyor: Kullanıcı={request.user.username}, Ders={ders}, Sınav Tipi={sinav_tipi}")
    
    cache_key = f'bulbakalim_sorular_{ders}_{sinav_tipi}'
    sorular = cache.get(cache_key)
    
    if sorular is None:
        if ders == "karisik":
            sorular = list(Soru.objects.filter(bul_bakalimda_cikar=True).only('id').values_list('id', flat=True))
        else:
            sorular = list(Soru.objects.filter(ders=ders, bul_bakalimda_cikar=True).only('id').values_list('id', flat=True))
        cache.set(cache_key, sorular, 300)
        logger.debug(f"Bul Bakalım soruları cache'lendi: Ders={ders}, Sayı={len(sorular)}")
    
    if len(sorular) < 5:
        messages.error(request, 'Yeterli soru yok!')
        logger.warning(f"Yetersiz soru:  Ders={ders}, Sayı={len(sorular)}")
        return redirect('quiz_anasayfa')
    
    secilen_sorular = random.sample(sorular, min(5, len(sorular)))
    yeni_oyun = BulBakalimOyun.objects.create(oyuncu=request.user, sorular=secilen_sorular)
    logger.info(f"Bul Bakalım oyunu oluşturuldu: Oyun ID={yeni_oyun.oyun_id}, Kullanıcı={request.user.username}")
    return redirect('bul_bakalim_oyun', oyun_id=yeni_oyun.oyun_id)


@login_required
def bul_bakalim_oyun(request, oyun_id):
    oyun = get_object_or_404(BulBakalimOyun.objects.select_related('oyuncu'), oyun_id=oyun_id, oyuncu=request.user)
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
        'aktif_soru':  aktif_soru, 
        'cevaplar': cevaplar, 
        'soru_no': cevaplanan_soru_sayisi + 1, 
        'toplam_soru': len(oyun.sorular), 
        'sure':  90
    }
    return render(request, 'quiz/bul_bakalim_oyun.html', context)


@login_required
def bul_bakalim_cevapla(request, oyun_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    oyun = get_object_or_404(BulBakalimOyun.objects.select_related('oyuncu'), oyun_id=oyun_id, oyuncu=request.user)
    if oyun.oyun_durumu == 'bitti':
        return JsonResponse({'error': 'Oyun bitti'}, status=400)
    
    data = json.loads(request.body)
    cevap_id = data.get('cevap_id')
    if not cevap_id: 
        return JsonResponse({'error': 'Cevap bulunamadı'}, status=400)
    
    cevap = Cevap.objects.select_related('soru').get(id=cevap_id)
    soru = cevap.soru
    oyun.cevaplar[str(soru.id)] = cevap_id
    
    # ==================== XP SİSTEMİ ====================
    dogru_mu = cevap.dogru_mu
    
    if dogru_mu: 
        oyun.dogru_sayisi += 1
        logger.debug(f"Bul Bakalım doğru cevap:  Oyun ID={oyun_id}, Soru ID={soru.id}")
    else:
        oyun.yanlis_sayisi += 1
        logger.debug(f"Bul Bakalım yanlış cevap: Oyun ID={oyun_id}, Soru ID={soru.id}")
    
    oyun.save()
    
    try:
        profil = request.user.profil
        profil.cozulen_soru_sayisi += 1
        profil.haftalik_cozulen += 1
        
        if dogru_mu:
            profil.toplam_dogru += 1
            profil.haftalik_dogru += 1
        else:
            profil.toplam_yanlis += 1
            profil.haftalik_yanlis += 1
        
        profil.save()
        
        # ==================== XP EKLE ====================
        xp_sonuc = soru_cozuldu_xp(profil, dogru_mu)
        
        # Seviye atlandı mı?
        seviye_atlandi = xp_sonuc.get('seviye_atlandi', False)
        yeni_seviye = xp_sonuc.get('yeni_seviye', 0)
        yeni_unvan = xp_sonuc.get('unvan', '')
        
        # Oyun istatistikleri
        oyun_ist, created = OyunModuIstatistik.objects.get_or_create(profil=profil, oyun_modu='bul_bakalim')
        oyun_ist.cozulen_soru += 1
        if dogru_mu:
            oyun_ist.dogru_sayisi += 1
        else: 
            oyun_ist.yanlis_sayisi += 1
        oyun_ist.save()
        
    except AttributeError as e:
        logger.error(f"Profil erişim hatası: Oyun ID={oyun_id}, Hata={e}", exc_info=True)
        seviye_atlandi = False
    except IntegrityError as e: 
        logger.error(f"Veritabanı hatası:  Oyun ID={oyun_id}, Hata={e}", exc_info=True)
        seviye_atlandi = False
    except Exception as e:
        logger.error(f"Bul Bakalım istatistik beklenmeyen hata: Oyun ID={oyun_id}, Hata={e}", exc_info=True)
        seviye_atlandi = False
    
    kalan_soru = 5 - len(oyun.cevaplar)
    if kalan_soru == 0:
        oyun.oyun_bitir()
        logger.info(f"Bul Bakalım oyunu bitti: Oyun ID={oyun_id}, Doğru={oyun.dogru_sayisi}, Yanlış={oyun.yanlis_sayisi}")
        
        response_data = {
            'oyun_bitti': True, 
            'redirect_url': f'/quiz/bul-bakalim/{oyun.oyun_id}/sonuc/',
            'seviye_atlandi': seviye_atlandi
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
        'seviye_atlandi': seviye_atlandi
    }
    
    if seviye_atlandi:
        response_data['yeni_seviye'] = yeni_seviye
        response_data['yeni_unvan'] = yeni_unvan
    
    return JsonResponse(response_data)


@login_required
def bul_bakalim_sonuc(request, oyun_id):
    oyun = get_object_or_404(BulBakalimOyun.objects.select_related('oyuncu'), oyun_id=oyun_id, oyuncu=request.user)
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
                verilen_cevap = next((c for c in soru.cevaplar.all() if c.id == int(verilen_cevap_id)), None)
                dogru_mu = verilen_cevap.dogru_mu if verilen_cevap else False
                sonuc_item = {
                    'soru': soru, 
                    'verilen_cevap': verilen_cevap, 
                    'dogru_cevap': dogru_cevap, 
                    'dogru_mu': dogru_mu
                }
                sonuclar.append(sonuc_item)
                if not dogru_mu:
                    yanlislar.append(sonuc_item)
            else:
                sonuc_item = {
                    'soru': soru, 
                    'verilen_cevap': None, 
                    'dogru_cevap': dogru_cevap, 
                    'dogru_mu':  False
                }
                sonuclar.append(sonuc_item)
                yanlislar.append(sonuc_item)
                
        except (ValueError, TypeError) as e:
            logger.error(f"Veri dönüşüm hatası:  Oyun ID={oyun_id}, Soru ID={soru_id}, Hata={e}", exc_info=True)
            continue
        except AttributeError as e:
            logger.error(f"Nitelik hatası: Oyun ID={oyun_id}, Soru ID={soru_id}, Hata={e}", exc_info=True)
            continue
        except Exception as e:
            logger.error(f"Bul Bakalım sonuç beklenmeyen hata:  Oyun ID={oyun_id}, Soru ID={soru_id}, Hata={e}", exc_info=True)
            continue
    
    try:
        profil = request.user.profil
        
        # Puan ekleme
        if oyun.toplam_puan > 0:
            profil.toplam_puan += oyun.toplam_puan
            profil.haftalik_puan += oyun.toplam_puan
            profil.save()
        
        # ==================== OYUN TAMAMLANDI BONUS XP ====================
        xp_sonuc = bul_bakalim_tamamlandi_xp(profil)
        
        if xp_sonuc.get('seviye_atlandi'):
            messages.success(
                request, 
                f"🎉 SEVİYE ATLADIN!   Seviye {xp_sonuc['yeni_seviye']} - {xp_sonuc['unvan']}"
            )
        
        # Oyun istatistikleri
        oyun_ist, created = OyunModuIstatistik.objects.get_or_create(profil=profil, oyun_modu='bul_bakalim')
        oyun_ist.oynanan_oyun_sayisi += 1
        oyun_ist.haftalik_oyun_sayisi += 1
        
        if oyun.dogru_sayisi >= 3:
            oyun_ist.kazanilan_oyun += 1
            logger.info(f"Bul Bakalım kazanıldı: Kullanıcı={request.user.username}, Oyun ID={oyun_id}")
        else:
            oyun_ist.kaybedilen_oyun += 1
            logger.info(f"Bul Bakalım kaybedildi: Kullanıcı={request.user.username}, Oyun ID={oyun_id}")
        
        oyun_ist.toplam_puan += oyun.toplam_puan
        oyun_ist.save()
        
        # Rozet kontrolü
        yeni_rozetler = rozet_kontrol_yap(profil)
        if yeni_rozetler: 
            for rozet in yeni_rozetler:
                messages.success(request, f'🏆 YENİ ROZET!   {rozet.icon} {rozet.get_kategori_display()}')
                
    except Exception as e:
        logger.error(f"Bul Bakalım sonuç istatistik hatası: Oyun ID={oyun_id}, Hata={e}", exc_info=True)
    
    context = {
        'oyun':  oyun, 
        'sonuclar': sonuclar, 
        'yanlislar':  yanlislar, 
        'kazandi':  oyun.dogru_sayisi >= 3, 
        'aktif_ders': request.GET.get('ders', 'karisik')
    }
    return render(request, 'quiz/bul_bakalim_sonuc.html', context)