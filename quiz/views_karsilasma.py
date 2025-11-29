from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db import models, transaction
from django.contrib import messages
from django.utils import timezone
from django.urls import reverse
from datetime import timedelta
from quiz.models import KarsilasmaOdasi, Cevap
from quiz.helpers import get_random_soru_by_ders, update_stats_with_combo
from profile.models import OyunModuIstatistik
from profile.rozet_kontrol import rozet_kontrol_yap
import json
import logging

logger = logging.getLogger(__name__)


@login_required
def karsilasma_sinav_tipi_secimi(request):
    """Karşılaşma için sınav tipi seçimi (TYT/AYT)"""
    if request.method == 'POST':
        sinav_tipi = request.POST.get('sinav_tipi', 'ayt')
        logger.info(f"Sınav tipi seçildi: {sinav_tipi}, Kullanıcı: {request.user.username}")
        return redirect(f"{reverse('karsilasma_ders_secimi')}?sinav_tipi={sinav_tipi}")
    return render(request, 'quiz/karsilasma_sinav_tipi_secimi.html')


@login_required
def karsilasma_ders_secimi(request):
    """Karşılaşma için ders seçimi"""
    sinav_tipi = request.GET.get('sinav_tipi', 'ayt')
    if sinav_tipi == 'tyt':
        ders_secenekleri = [
            ('matematik', 'Matematik'), ('turkce', 'Türkçe'), ('fizik', 'Fizik'),
            ('kimya', 'Kimya'), ('biyoloji', 'Biyoloji'), ('karisik', 'Karışık')
        ]
    else:
        ders_secenekleri = [
            ('matematik', 'Matematik'), ('fizik', 'Fizik'), ('kimya', 'Kimya'),
            ('biyoloji', 'Biyoloji'), ('edebiyat', 'Edebiyat'), ('tarih', 'Tarih'),
            ('cografya', 'Coğrafya'), ('felsefe', 'Felsefe'), ('karisik', 'Karışık')
        ]
    
    if request.method == 'POST':
        selected_ders = request.POST.get('selected_ders')
        logger.info(f"Ders seçildi: {selected_ders}, Sınav: {sinav_tipi}, User: {request.user.username}")
        return redirect(f"{reverse('karsilasma_rakip_bul')}? ders={selected_ders}&sinav_tipi={sinav_tipi}")
    
    context = {'ders_secenekleri': ders_secenekleri, 'sinav_tipi': sinav_tipi}
    return render(request, 'quiz/karsilasma_ders_secimi.html', context)


@login_required
def karsilasma_oyun(request, oda_id):
    oda = get_object_or_404(KarsilasmaOdasi.objects.select_related('oyuncu1', 'oyuncu2', 'aktif_soru'), oda_id=oda_id)
    context = {'oda': oda}
    return render(request, 'quiz/karsilasma_oyun.html', context)


@login_required
@transaction.atomic
def karsilasma_durum_guncelle(request, oda_id):
    oda = get_object_or_404(
        KarsilasmaOdasi.objects.select_for_update().select_related(
            'oyuncu1', 'oyuncu2', 'aktif_soru', 'ilk_dogru_cevaplayan'
        ),
        oda_id=oda_id
    )
    
    logger.debug(f"📊 {request.method} | Oda={oda_id} | Soru={oda.aktif_soru_no}/{oda.toplam_soru} | O1={oda.oyuncu1_cevapladi} O2={oda.oyuncu2_cevapladi} | Bekleme={oda.round_bekleme_durumu}")
    
    # ✅ POST: CEVAP GÖNDERME
    if request.method == 'POST':
        data = json.loads(request.body)
        cevap_id = data.get('cevap_id')
        
        try:
            cevap_obj = Cevap.objects.select_related('soru').get(id=cevap_id)
        except Cevap.DoesNotExist:
            return JsonResponse({'error': 'Geçersiz cevap'}, status=400)
        
        if not oda.aktif_soru or cevap_obj.soru != oda.aktif_soru:
            return JsonResponse({'error': 'Geçersiz soru'}, status=400)
        
        is_oyuncu1 = (oda.oyuncu1 == request.user)
        
        if (is_oyuncu1 and oda.oyuncu1_cevapladi) or (not is_oyuncu1 and oda.oyuncu2_cevapladi):
            return JsonResponse({'error': 'Zaten cevaplandı'}, status=400)
        
        # Cevabı kaydet
        cevap_zamani = timezone.now()
        if is_oyuncu1:
            oda.oyuncu1_cevapladi = True
            oda.oyuncu1_cevap_zamani = cevap_zamani
        else:
            oda.oyuncu2_cevapladi = True
            oda.oyuncu2_cevap_zamani = cevap_zamani
        
        update_stats_with_combo(request.user, oda, cevap_obj, is_oyuncu1)
        
        # ✅ HER İKİSİ DE CEVAPLADIYSA → ROUND BEKLEMEYİ BAŞLAT
        if oda.oyuncu1_cevapladi and oda.oyuncu2_cevapladi and not oda.round_bekleme_durumu:
            oda.round_bekleme_durumu = True
            oda.round_bitis_zamani = timezone.now()
            logger.info(f"⏳ Round bekleme başladı: Oda={oda_id}, Soru={oda.aktif_soru_no}")
        
        oda.save()
        
        try:
            profil = request.user.profil
            if profil.cozulen_soru_sayisi % 10 == 0:
                rozet_kontrol_yap(profil)
        except Exception as e:
            logger.error(f"Rozet hatası: {e}")
    
    # ✅ GET: DURUM KONTROLÜ VE YENİ SORUYA GEÇME
    elif request.method == 'GET':
        # Her iki oyuncu cevapladıysa VE bekleme modundaysa
        if oda.oyuncu1_cevapladi and oda.oyuncu2_cevapladi and oda.round_bekleme_durumu:
            if oda.round_bitis_zamani:
                gecen_sure = (timezone.now() - oda.round_bitis_zamani).total_seconds()
                
                # 3 saniye geçtiyse yeni soruya geç
                if gecen_sure >= 3:
                    logger.info(f"✅ 3 saniye geçti, yeni soruya geçiliyor: Oda={oda_id}")
                    
                    # Son soru mu? 
                    if oda.aktif_soru_no >= oda.toplam_soru:
                        oda.oyun_durumu = 'bitti'
                        oda.aktif_soru = None
                        logger.info(f"🏁 Oyun bitti: Oda={oda_id}")
                    else:
                        # Yeni soruya geç
                        oda.aktif_soru_no += 1
                        yeni_soru = get_random_soru_by_ders(oda.secilen_ders)
                        
                        if yeni_soru:
                            oda.aktif_soru = yeni_soru
                            oda.soru_baslangic_zamani = timezone.now()
                            
                            # Flag'leri sıfırla
                            oda.oyuncu1_cevapladi = False
                            oda.oyuncu2_cevapladi = False
                            oda.oyuncu1_cevap_zamani = None
                            oda.oyuncu2_cevap_zamani = None
                            oda.ilk_dogru_cevaplayan = None
                            oda.round_bekleme_durumu = False
                            oda.round_bitis_zamani = None
                            
                            logger.info(f"❓ Yeni soru: Oda={oda_id}, Soru={oda.aktif_soru_no}, ID={yeni_soru.id}")
                        else:
                            oda.oyun_durumu = 'bitti'
                            logger.error(f"❌ Soru bulunamadı: Oda={oda_id}")
                    
                    oda.save()
    
    # ✅ RESPONSE HAZIRLA
    soru_obj = oda.aktif_soru
    cevaplar = []
    
    if soru_obj:
        cevaplar_qs = Cevap.objects.filter(soru=soru_obj).only('id', 'metin')
        cevaplar = [{'id': c.id, 'metin': c.metin} for c in cevaplar_qs]
    
    # ✅ KALAN SÜRE HESAPLA (modal için)
    kalan_sure = 0
    if oda.round_bekleme_durumu and oda.round_bitis_zamani:
        gecen = (timezone.now() - oda.round_bitis_zamani).total_seconds()
        kalan_sure = max(0, int(3 - gecen))  # ✅ int içine al

        # ✅ DEBUG LOG
        logger.debug(f"⏰ Kalan süre: {kalan_sure}s (geçen: {gecen:.2f}s)")
    
    response_data = {
        'oyuncu1_skor': oda.oyuncu1_skor,
        'oyuncu2_skor': oda.oyuncu2_skor,
        'oyuncu1_combo': oda.oyuncu1_combo,
        'oyuncu2_combo': oda.oyuncu2_combo,
        'oyuncu2_adi': oda.oyuncu2.username if oda.oyuncu2 else None,
        'oyun_durumu': oda.oyun_durumu,
        'soru': soru_obj.metin if soru_obj else None,
        'soru_id': soru_obj.id if soru_obj else None,
        'cevaplar': cevaplar,
        'oyuncu1_cevapladi': oda.oyuncu1_cevapladi,
        'oyuncu2_cevapladi': oda.oyuncu2_cevapladi,
        'aktif_soru_no': oda.aktif_soru_no,
        'toplam_soru': oda.toplam_soru,
        'round_bekleme': oda.round_bekleme_durumu,  # ✅ Modal için
        'kalan_sure': kalan_sure  # ✅ Geri sayım için
    }
    
    return JsonResponse(response_data)


@login_required
def karsilasma_sonuc(request, oda_id):
    oda = get_object_or_404(KarsilasmaOdasi.objects.select_related('oyuncu1', 'oyuncu2'), oda_id=oda_id)
    is_oyuncu1 = (oda.oyuncu1 == request.user)
    
    if is_oyuncu1:
        benim_skorom = oda.oyuncu1_skor
        rakip_skorom = oda.oyuncu2_skor
        benim_dogrum = oda.oyuncu1_dogru
        benim_yanlisim = oda.oyuncu1_yanlis
    else:
        benim_skorom = oda.oyuncu2_skor
        rakip_skorom = oda.oyuncu1_skor
        benim_dogrum = oda.oyuncu2_dogru
        benim_yanlisim = oda.oyuncu2_yanlis
    
    kazandim = benim_skorom > rakip_skorom
    berabere = benim_skorom == rakip_skorom
    puan_degisimi = 0
    
    try:
        session_key = f'karsilasma_sonuc_{oda_id}_{request.user.id}'
        
        if not request.session.get(session_key, False):
            profil = request.user.profil
            oyun_ist, _ = OyunModuIstatistik.objects.get_or_create(profil=profil, oyun_modu='karsilasma')
            oyun_ist.oynanan_oyun_sayisi += 1
            oyun_ist.haftalik_oyun_sayisi += 1
            
            if kazandim:
                oyun_ist.kazanilan_oyun += 1
                puan_degisimi = 1
                profil.toplam_puan += 1
                profil.haftalik_puan += 1
            elif berabere:
                puan_degisimi = 0
            else:
                oyun_ist.kaybedilen_oyun += 1
                puan_degisimi = -1
                profil.toplam_puan = max(0, profil.toplam_puan - 1)
                profil.haftalik_puan = max(0, profil.haftalik_puan - 1)
            
            oyun_ist.save()
            profil.save()
            request.session[session_key] = True
            
            yeni_rozetler = rozet_kontrol_yap(profil)
            if yeni_rozetler:
                for rozet in yeni_rozetler:
                    messages.success(request, f'🏆 YENİ ROZET!  {rozet.icon} {rozet.get_kategori_display()}')
        else:
            puan_degisimi = 1 if kazandim else (-1 if not berabere else 0)
    
    except Exception as e:
        logger.error(f"Sonuç hatası: User={request.user.username}, Oda={oda_id}, Error={e}")
    
    context = {
        'oda': oda,
        'kazandim': kazandim,
        'berabere': berabere,
        'benim_skorom': benim_skorom,
        'rakip_skorom': rakip_skorom,
        'benim_dogrum': benim_dogrum,
        'benim_yanlisim': benim_yanlisim,
        'puan_degisimi': puan_degisimi,
        'is_oyuncu1': is_oyuncu1
    }
    return render(request, 'quiz/karsilasma_sonuc.html', context)


@login_required
def karsilasma_rakip_bul(request):
    """Rakip bulma sistemi"""
    secilen_ders = request.GET.get('ders', 'karisik')
    sinav_tipi = request.GET.get('sinav_tipi', 'ayt')
    logger.info(f"Rakip aranıyor: User={request.user.username}, Ders={secilen_ders}, Sınav={sinav_tipi}")
    
    # Eski odaları temizle
    bes_dakika_once = timezone.now() - timedelta(minutes=5)
    KarsilasmaOdasi.objects.filter(
        oyuncu1=request.user,
        oyun_durumu='bekleniyor',
        oyuncu2=None,
        olusturma_tarihi__lt=bes_dakika_once
    ).update(oyun_durumu='bitti')
    
    # Aktif oda var mı?
    aktif_oda = KarsilasmaOdasi.objects.select_related('oyuncu1', 'oyuncu2').filter(
        models.Q(oyuncu1=request.user) | models.Q(oyuncu2=request.user),
        oyun_durumu__in=['bekleniyor', 'oynaniyor'],
        secilen_ders=secilen_ders,
        sinav_tipi=sinav_tipi
    ).first()
    
    if aktif_oda:
        logger.info(f"Aktif oda bulundu: {aktif_oda.oda_id}")
        return redirect('karsilasma_oyun', oda_id=aktif_oda.oda_id)
    
    # Farklı dersteki odaları kapat
    KarsilasmaOdasi.objects.filter(
        models.Q(oyuncu1=request.user) | models.Q(oyuncu2=request.user),
        oyun_durumu__in=['bekleniyor', 'oynaniyor']
    ).exclude(secilen_ders=secilen_ders, sinav_tipi=sinav_tipi).update(oyun_durumu='bitti')
    
    # Bekleyen oda bul
    bekleyen_oda = KarsilasmaOdasi.objects.select_related('oyuncu1').filter(
        oyun_durumu='bekleniyor',
        oyuncu2=None,
        secilen_ders=secilen_ders,
        sinav_tipi=sinav_tipi
    ).exclude(oyuncu1=request.user).first()
    
    if bekleyen_oda:
        # Odaya katıl
        bekleyen_oda.oyuncu2 = request.user
        bekleyen_oda.oyun_durumu = 'oynaniyor'
        
        ilk_soru = get_random_soru_by_ders(secilen_ders)
        if ilk_soru:
            bekleyen_oda.aktif_soru = ilk_soru
            bekleyen_oda.aktif_soru_no = 1
            bekleyen_oda.soru_baslangic_zamani = timezone.now()
            logger.info(f"Oyun başladı: Oda={bekleyen_oda.oda_id}")
        
        bekleyen_oda.save()
        return redirect('karsilasma_oyun', oda_id=bekleyen_oda.oda_id)
    else:
        # Yeni oda oluştur
        yeni_oda = KarsilasmaOdasi.objects.create(
            oyuncu1=request.user,
            oyun_durumu='bekleniyor',
            secilen_ders=secilen_ders,
            sinav_tipi=sinav_tipi
        )
        logger.info(f"Yeni oda: {yeni_oda.oda_id}")
        return redirect('karsilasma_oyun', oda_id=yeni_oda.oda_id)