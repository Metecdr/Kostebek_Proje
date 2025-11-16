from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import (
    TabuKelime, 
    TabuOyun, 
    Soru, 
    KarsilasmaOdasi, 
    Cevap, 
    BulBakalimOyun
)
from django.http import JsonResponse
from profile.models import KonuIstatistik
from django.db import models, transaction
from django.contrib import messages
from django.core.cache import cache
from django.db.models import Prefetch
from django.utils import timezone
from datetime import timedelta
import json
import random

# ✅ ROZET SİSTEMİ İMPORT'LARI
from profile.models import OgrenciProfili, OyunModuIstatistik, DersIstatistik
from profile.rozet_kontrol import rozet_kontrol_yap


# ✅ QUIZ ANASAYFA
@login_required
def quiz_anasayfa(request):
    """Quiz ana sayfa - Oyun modları seçimi"""
    try:
        profil = request.user.profil
        
        cache_key = f'karsilasma_ist_{profil.id}'
        karsilasma_ist = cache.get(cache_key)
        
        if karsilasma_ist is None:
            karsilasma_ist = OyunModuIstatistik.objects.filter(
                profil=profil,
                oyun_modu='karsilasma'
            ).first()
            cache.set(cache_key, karsilasma_ist, 60)
        
        context = {
            'profil': profil,
            'karsilasma_ist': karsilasma_ist,
        }
    except:
        context = {}
    
    return render(request, 'quiz/anasayfa.html', context)


# ==================== TABU OYUNU ====================

TABU_BOLUMLERI = [
    ('sozel', 'Sözel'),
    ('esit_agirlik', 'Eşit Ağırlık'),
    ('sayisal', 'Sayısal'),
    ('dil', 'Dil'),
]

BOLUM_KATEGORILERI = {
    'sayisal': ['biyoloji', 'kimya', 'fizik'],
    'esit_agirlik': ['cografya', 'tarih', 'edebiyat'],
    'sozel': ['cografya', 'tarih', 'edebiyat'],
}

def tabu_bolum_sec(request):
    if request.method == 'POST':
        secilen_bolum = request.POST.get('bolum')
        request.session['tabu_bolum'] = secilen_bolum
        return redirect('tabu_lobi')
    return render(request, 'quiz/tabu_bolum_sec.html', {'bolumler': TABU_BOLUMLERI})

MAX_KELIME = 10
SURE = 60

def tabu_anasayfa(request):
    """Tabu oyunu ana sayfası"""
    return render(request, 'quiz/tabu_anasayfa.html')

@login_required
def tabu_lobi(request):
    bolum = request.session.get('tabu_bolum', None)
    kategoriler = BOLUM_KATEGORILERI.get(bolum, [])
    kelimeler = TabuKelime.objects.filter(kategori__in=kategoriler)
    
    if request.method == 'POST':
        takim_a_adi = request.POST.get('takim_a', 'Takım A')
        takim_b_adi = request.POST.get('takim_b', 'Takım B')
        yeni_oyun = TabuOyun.objects.create(
            takim_a_adi=takim_a_adi,
            takim_b_adi=takim_b_adi,
            tur_sayisi=1,
            aktif_takim="A",
            oyun_modu="normal",
            oyun_durumu="devam"
        )
        request.session['gorulen_kelime_idler'] = []
        request.session['tabu_ara_ekran'] = True
        return redirect('tabu_oyun', oyun_id=yeni_oyun.id)
    return render(request, 'quiz/tabu_lobi.html')

@login_required
def tabu_oyun_basla(request):
    if request.method == 'POST':
        takim_a_adi = request.POST.get('takim_a', 'Takım A')
        takim_b_adi = request.POST.get('takim_b', 'Takım B')
        yeni_oyun = TabuOyun.objects.create(
            takim_a_adi=takim_a_adi,
            takim_b_adi=takim_b_adi,
            tur_sayisi=1,
            aktif_takim="A",
            oyun_modu="normal",
            oyun_durumu="devam"
        )
        request.session['gorulen_kelime_idler'] = []
        request.session['tabu_ara_ekran'] = True
        return redirect('tabu_oyun', oyun_id=yeni_oyun.id)
    return render(request, 'quiz/tabu_basla.html')

@login_required
def tabu_oyun(request, oyun_id):
    oyun = get_object_or_404(TabuOyun, id=oyun_id)
    aktif_takim = oyun.aktif_takim
    gorulen_idler = request.session.get('gorulen_kelime_idler', [])
    ara_ekran = request.session.get('tabu_ara_ekran', True)

    if ara_ekran:
        takim_adi = oyun.takim_a_adi if aktif_takim == 'A' else oyun.takim_b_adi
        context = {
            'oyun': oyun,
            'aktif_takim': aktif_takim,
            'takim_adi': takim_adi,
            'MAX_KELIME': MAX_KELIME,
            'SURE': SURE,
            'ara_ekran': True,
        }
        if request.method == 'POST':
            request.session['tabu_ara_ekran'] = False
            return redirect('tabu_oyun', oyun_id=oyun.id)
        return render(request, 'quiz/tabu.html', context)

    kelime = TabuKelime.objects.exclude(id__in=gorulen_idler).order_by('?').first()
    
    if not kelime or len(gorulen_idler) >= MAX_KELIME:
        request.session['tabu_ara_ekran'] = True
        if aktif_takim == 'A':
            oyun.aktif_takim = 'B'
            oyun.save()
            request.session['gorulen_kelime_idler'] = []
            return redirect('tabu_oyun', oyun_id=oyun.id)
        else:
            oyun.oyun_durumu = 'bitti'
            oyun.save()
            return redirect('tabu_sonuc', oyun_id=oyun.id)

    yasaklilar = kelime.yasakli_kelimeler.all()
    context = {
        'oyun': oyun,
        'kelime': kelime,
        'yasaklilar': yasaklilar,
        'aktif_takim': aktif_takim,
        'takim_adi': oyun.takim_a_adi if aktif_takim == 'A' else oyun.takim_b_adi,
        'MAX_KELIME': MAX_KELIME,
        'SURE': SURE,
        'ara_ekran': False,
    }
    return render(request, 'quiz/tabu.html', context)

@login_required
def tabu_tur_guncelle(request, oyun_id):
    if request.method == 'POST':
        oyun = get_object_or_404(TabuOyun, id=oyun_id)
        data = json.loads(request.body)
        action = data.get('action')
        mevcut_kelime_id = data.get('mevcut_kelime_id')
        gorulen_idler = request.session.get('gorulen_kelime_idler', [])
        aktif_takim = oyun.aktif_takim

        if aktif_takim == 'A':
            if action == 'dogru':
                oyun.takim_a_skor += 1
            elif action == 'tabu':
                oyun.takim_a_skor -= 1
        else:
            if action == 'dogru':
                oyun.takim_b_skor += 1
            elif action == 'tabu':
                oyun.takim_b_skor -= 1
        oyun.save()

        if mevcut_kelime_id and mevcut_kelime_id not in gorulen_idler:
            gorulen_idler.append(mevcut_kelime_id)
        request.session['gorulen_kelime_idler'] = gorulen_idler

        if len(gorulen_idler) >= MAX_KELIME:
            return JsonResponse({'tur_bitti_kelime_yok': True})

        yeni_kelime = TabuKelime.objects.exclude(id__in=gorulen_idler).order_by('?').first()
        if not yeni_kelime:
            return JsonResponse({'tur_bitti_kelime_yok': True})

        yasaklilar = list(yeni_kelime.yasakli_kelimeler.values_list('yasakli_kelime', flat=True))
        return JsonResponse({
            'kelime_id': yeni_kelime.id,
            'kelime': yeni_kelime.kelime,
            'yasaklilar': yasaklilar,
            'takim_a_skor': oyun.takim_a_skor,
            'takim_b_skor': oyun.takim_b_skor,
        })
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def tabu_tur_degistir(request, oyun_id):
    if request.method == 'POST':
        oyun = get_object_or_404(TabuOyun, id=oyun_id)
        aktif_takim = oyun.aktif_takim
        if aktif_takim == 'A':
            oyun.aktif_takim = 'B'
            oyun.save()
            request.session['gorulen_kelime_idler'] = []
            request.session['tabu_ara_ekran'] = True
            return JsonResponse({'oyun_bitti': False, 'redirect_url': f'/tabu/oyun/{oyun.id}/'})
        else:
            oyun.oyun_durumu = 'bitti'
            oyun.save()
            return JsonResponse({'oyun_bitti': True, 'redirect_url': f'/tabu/sonuc/{oyun.id}/'})
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def tabu_sonuc(request, oyun_id):
    oyun = get_object_or_404(TabuOyun, id=oyun_id)
    if oyun.takim_a_skor > oyun.takim_b_skor:
        kazanan = oyun.takim_a_adi
    elif oyun.takim_b_skor > oyun.takim_a_skor:
        kazanan = oyun.takim_b_adi
    else:
        kazanan = "Berabere"
    context = {
        'oyun': oyun,
        'kazanan': kazanan
    }
    return render(request, 'quiz/tabu_sonuc.html', context)


# ==================== KARŞILAŞMA ====================


@login_required
def karsilasma_sinav_tipi_secimi(request):
    """Karşılaşma için sınav tipi seçimi (TYT/AYT)"""
    if request.method == 'POST':
        sinav_tipi = request.POST.get('sinav_tipi', 'ayt')
        return redirect('karsilasma_ders_secimi') + f'?sinav_tipi={sinav_tipi}'
    
    return render(request, 'quiz/karsilasma_sinav_tipi_secimi.html')

@login_required
def karsilasma_ders_secimi(request):
    """Karşılaşma için ders seçimi"""
    sinav_tipi = request.GET.get('sinav_tipi', 'ayt')
    
    # TYT veya AYT'ye göre dersleri filtrele
    if sinav_tipi == 'tyt':
        ders_secenekleri = [
            ('matematik', 'Matematik'),
            ('turkce', 'Türkçe'),
            ('fizik', 'Fizik'),
            ('kimya', 'Kimya'),
            ('biyoloji', 'Biyoloji'),
            ('karisik', 'Karışık'),
        ]
    else:  # AYT
        ders_secenekleri = [
            ('matematik', 'Matematik'),
            ('fizik', 'Fizik'),
            ('kimya', 'Kimya'),
            ('biyoloji', 'Biyoloji'),
            ('edebiyat', 'Edebiyat'),
            ('tarih', 'Tarih'),
            ('cografya', 'Coğrafya'),
            ('felsefe', 'Felsefe'),
            ('karisik', 'Karışık'),
        ]
    
    if request.method == 'POST':
        selected_ders = request.POST.get('selected_ders')
        return redirect('karsilasma_rakip_bul') + f'?ders={selected_ders}&sinav_tipi={sinav_tipi}'

    
    context = {
        'ders_secenekleri': ders_secenekleri,
        'sinav_tipi': sinav_tipi,
    }
    
    return render(request, 'quiz/karsilasma_ders_secimi.html', context)

@login_required
def karsilasma_oyun(request, oda_id):
    oda = get_object_or_404(KarsilasmaOdasi, oda_id=oda_id)
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
    
    print(f"\n📡 DURUM: Method={request.method}, Soru={oda.aktif_soru_no}/{oda.toplam_soru}")
    
    if request.method == 'POST':
        data = json.loads(request.body)
        cevap_id = data.get('cevap_id')
        cevap_obj = Cevap.objects.select_related('soru').get(id=cevap_id)
        
        if oda.aktif_soru and cevap_obj.soru == oda.aktif_soru:
            is_oyuncu1 = (oda.oyuncu1 == request.user)
            
            if (is_oyuncu1 and not oda.oyuncu1_cevapladi) or (not is_oyuncu1 and not oda.oyuncu2_cevapladi):
                cevap_zamani = timezone.now()
                if is_oyuncu1:
                    oda.oyuncu1_cevapladi = True
                    oda.oyuncu1_cevap_zamani = cevap_zamani
                else:
                    oda.oyuncu2_cevapladi = True
                    oda.oyuncu2_cevap_zamani = cevap_zamani
                
                _update_stats_with_combo(request.user, oda, cevap_obj, is_oyuncu1)
            
            if oda.oyuncu1_cevapladi and oda.oyuncu2_cevapladi:
                print(f"✅ HER İKİ OYUNCU DA CEVAPLADI!")
                
                if oda.aktif_soru_no >= oda.toplam_soru:
                    oda.aktif_soru_no += 1
                    oda.oyun_durumu = 'bitti'
                    oda.aktif_soru = None
                    print(f"🏁 OYUN BİTTİ!")
                else:
                    oda.aktif_soru_no += 1
                    print(f"🔄 Yeni soruya geçiliyor: Soru {oda.aktif_soru_no}/{oda.toplam_soru}")
                    
                    # ✅ Seçilen derse göre soru getir
                    yeni_soru = _get_random_soru_by_ders(oda.secilen_ders)
                    if yeni_soru:
                        oda.aktif_soru = yeni_soru
                        oda.soru_baslangic_zamani = timezone.now()
                        oda.round_bitis_zamani = timezone.now()
                        
                        print(f"✅ Yeni soru atandı: {yeni_soru.id}")
                        print(f"⏰ Ara ekran zamanı kaydedildi!")
                    else:
                        oda.oyun_durumu = 'bitti'
                
                try:
                    profil = request.user.profil
                    if profil.cozulen_soru_sayisi % 10 == 0:
                        yeni_rozetler = rozet_kontrol_yap(profil)
                except: 
                    pass
            
            oda.save()
    
    soru_obj = oda.aktif_soru
    cevaplar = []
    
    if soru_obj:
        cevaplar_qs = Cevap.objects.filter(soru=soru_obj).only('id', 'metin')
        cevaplar = [{'id': c.id, 'metin': c.metin} for c in cevaplar_qs]
    
    # ✅✅✅ GET isteğinde 3 SANİYE GEÇTİYSE sıfırla ✅✅✅
    if oda.oyuncu1_cevapladi and oda.oyuncu2_cevapladi and request.method == 'GET':
        if oda.round_bitis_zamani:
            gecen_sure = (timezone.now() - oda.round_bitis_zamani).total_seconds()
            
            if gecen_sure >= 3:
                print(f"🔄 3 saniye geçti ({gecen_sure:.1f}s), cevaplar sıfırlanıyor...")
                oda.oyuncu1_cevapladi = False
                oda.oyuncu2_cevapladi = False
                oda.ilk_dogru_cevaplayan = None
                oda.round_bitis_zamani = None
                oda.save()
            else:
                print(f"⏸️ Henüz {gecen_sure:.1f}s geçti, bekleniyor...")
    
    response_data = {
        'oyuncu1_skor': oda.oyuncu1_skor,
        'oyuncu2_skor': oda.oyuncu2_skor,
        'oyuncu1_combo': oda.oyuncu1_combo,
        'oyuncu2_combo': oda.oyuncu2_combo,
        'oyuncu2_adi': oda.oyuncu2.username if oda.oyuncu2 else None,
        'oyun_durumu': oda.oyun_durumu,
        'soru': soru_obj.metin if soru_obj else None,
        'cevaplar': cevaplar,
        'oyuncu1_cevapladi': oda.oyuncu1_cevapladi,
        'oyuncu2_cevapladi': oda.oyuncu2_cevapladi,
        'aktif_soru_no': oda.aktif_soru_no,
        'toplam_soru': oda.toplam_soru,
    }
    
    return JsonResponse(response_data)


def _update_stats_with_combo(user, oda, cevap_obj, is_oyuncu1):
    """Combo ve hız bonusu ile istatistik güncelle"""
    try:
        profil = user.profil
        base_puan = 10
        bonus_puan = 0
        
        if is_oyuncu1 and oda.oyuncu1_cevap_zamani and oda.soru_baslangic_zamani:
            sure = (oda.oyuncu1_cevap_zamani - oda.soru_baslangic_zamani).total_seconds()
            if sure < 5:
                bonus_puan += 5
                print(f"⚡ {user.username} hız bonusu kazandı! ({sure:.1f}s)")
        elif not is_oyuncu1 and oda.oyuncu2_cevap_zamani and oda.soru_baslangic_zamani:
            sure = (oda.oyuncu2_cevap_zamani - oda.soru_baslangic_zamani).total_seconds()
            if sure < 5:
                bonus_puan += 5
                print(f"⚡ {user.username} hız bonusu kazandı! ({sure:.1f}s)")
        
        if cevap_obj.dogru_mu:
            if is_oyuncu1:
                oda.oyuncu1_combo += 1
                combo = oda.oyuncu1_combo
                oda.oyuncu1_dogru += 1
            else:
                oda.oyuncu2_combo += 1
                combo = oda.oyuncu2_combo
                oda.oyuncu2_dogru += 1
            
            combo_bonus = min(combo * 2, 20)
            bonus_puan += combo_bonus
            
            print(f"🔥 {user.username} COMBO x{combo}! Bonus: +{combo_bonus}")
            
            if oda.ilk_dogru_cevaplayan is None:
                oda.ilk_dogru_cevaplayan = user
                bonus_puan += 3
                print(f"🥇 {user.username} ilk doğru cevaplayan! +3 puan")
            
            toplam_puan = base_puan + bonus_puan
            
            if is_oyuncu1:
                oda.oyuncu1_skor += toplam_puan
            else:
                oda.oyuncu2_skor += toplam_puan
            
            profil.toplam_dogru += 1
            profil.haftalik_dogru += 1
            profil.cozulen_soru_sayisi += 1
            profil.haftalik_cozulen += 1
            profil.toplam_puan += toplam_puan
            profil.haftalik_puan += toplam_puan
            profil.save()
            
            oyun_ist, created = OyunModuIstatistik.objects.get_or_create(
                profil=profil,
                oyun_modu='karsilasma'
            )
            oyun_ist.cozulen_soru += 1
            oyun_ist.dogru_sayisi += 1
            oyun_ist.toplam_puan += toplam_puan
            oyun_ist.save()
            
            print(f"✅ {user.username} +{toplam_puan} puan kazandı!")
            
        else:
            if is_oyuncu1:
                oda.oyuncu1_combo = 0
                oda.oyuncu1_yanlis += 1
            else:
                oda.oyuncu2_combo = 0
                oda.oyuncu2_yanlis += 1
            
            print(f"❌ {user.username} yanlış cevap!")
            
            profil.toplam_yanlis += 1
            profil.haftalik_yanlis += 1
            profil.cozulen_soru_sayisi += 1
            profil.haftalik_cozulen += 1
            profil.save()
            
            oyun_ist, created = OyunModuIstatistik.objects.get_or_create(
                profil=profil,
                oyun_modu='karsilasma'
            )
            oyun_ist.cozulen_soru += 1
            oyun_ist.yanlis_sayisi += 1
            oyun_ist.save()
        
        cache_key = f'karsilasma_ist_{profil.id}'
        cache.delete(cache_key)
        
    except Exception as e:
        print(f"❌ İstatistik güncelleme hatası: {e}")


@login_required
def karsilasma_sonuc(request, oda_id):
    oda = get_object_or_404(
        KarsilasmaOdasi.objects.select_related('oyuncu1', 'oyuncu2'), 
        oda_id=oda_id
    )
    
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
        session_key = f'karsilasma_sonuc_kaydedildi_{oda_id}_{request.user.id}'
        
        if not request.session.get(session_key, False):
            profil = request.user.profil
            
            oyun_ist, created = OyunModuIstatistik.objects.get_or_create(
                profil=profil,
                oyun_modu='karsilasma'
            )
            
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
                    messages.success(request, f'🏆 YENİ ROZET! {rozet.icon} {rozet.get_kategori_display()}')
        else:
            if kazandim:
                puan_degisimi = 1
            elif berabere:
                puan_degisimi = 0
            else:
                puan_degisimi = -1
    
    except Exception as e:
        print(f"❌ Karşılaşma sonuç hatası: {e}")
    
    context = {
        'oda': oda,
        'kazandim': kazandim,
        'berabere': berabere,
        'benim_skorom': benim_skorom,
        'rakip_skorom': rakip_skorom,
        'benim_dogrum': benim_dogrum,
        'benim_yanlisim': benim_yanlisim,
        'puan_degisimi': puan_degisimi,
        'is_oyuncu1': is_oyuncu1,
    }
    
    return render(request, 'quiz/karsilasma_sonuc.html', context)


@login_required
def karsilasma_rakip_bul(request):
    """Rakip bulma sistemi - Ders bazlı"""
    # URL parametrelerinden al
    secilen_ders = request.GET.get('ders', 'karisik')
    sinav_tipi = request.GET.get('sinav_tipi', 'ayt')
    
    print(f"🎮 Karşılaşma başlatılıyor: Ders={secilen_ders}, Sınav Tipi={sinav_tipi}")
    
    # ✅ ESKİ ODALARI TEMİZLE (5 dakikadan eski ve rakip yoksa)
    from datetime import timedelta
    bes_dakika_once = timezone.now() - timedelta(minutes=5)
    
    eski_odalar = KarsilasmaOdasi.objects.filter(
        oyuncu1=request.user,
        oyun_durumu='bekleniyor',
        oyuncu2=None,
        olusturma_tarihi__lt=bes_dakika_once
    )
    
    if eski_odalar.exists():
        eski_sayisi = eski_odalar.count()
        eski_odalar.update(oyun_durumu='bitti')
        print(f"🗑️ {eski_sayisi} eski oda temizlendi")
    
    # Kullanıcının AYNI DERSTEN aktif odasını kontrol et
    aktif_oda = KarsilasmaOdasi.objects.select_related('oyuncu1', 'oyuncu2').filter(
        models.Q(oyuncu1=request.user) | models.Q(oyuncu2=request.user),
        oyun_durumu__in=['bekleniyor', 'oynaniyor'],
        secilen_ders=secilen_ders,
        sinav_tipi=sinav_tipi
    ).first()
    
    if aktif_oda:
        print(f"✅ Kullanıcının aktif odası bulundu: {aktif_oda.oda_id}")
        return redirect('karsilasma_oyun', oda_id=aktif_oda.oda_id)
    
    # ✅ FARKLI DERSE GEÇMEK İSTİYORSA ESKİ ODALARI BİTİR
    baska_dersler = KarsilasmaOdasi.objects.filter(
        models.Q(oyuncu1=request.user) | models.Q(oyuncu2=request.user),
        oyun_durumu__in=['bekleniyor', 'oynaniyor']
    ).exclude(
        secilen_ders=secilen_ders,
        sinav_tipi=sinav_tipi
    )
    
    if baska_dersler.exists():
        baska_dersler.update(oyun_durumu='bitti')
        print(f"🔄 Farklı dersteki {baska_dersler.count()} oda kapatıldı")
    
    # Aynı dersi seçmiş bekleyen oda bul
    bekleyen_oda = KarsilasmaOdasi.objects.select_related('oyuncu1').filter(
        oyun_durumu='bekleniyor',
        oyuncu2=None,
        secilen_ders=secilen_ders,
        sinav_tipi=sinav_tipi
    ).exclude(oyuncu1=request.user).first()
    
    if bekleyen_oda:
        print(f"🔄 Bekleyen odaya katılıyor: {bekleyen_oda.oda_id}")
        bekleyen_oda.oyuncu2 = request.user
        bekleyen_oda.oyun_durumu = 'oynaniyor'
        
        # İlk soruyu getir
        ilk_soru = _get_random_soru_by_ders(secilen_ders)
        if ilk_soru:
            bekleyen_oda.aktif_soru = ilk_soru
            bekleyen_oda.aktif_soru_no = 1
            bekleyen_oda.soru_baslangic_zamani = timezone.now()
            print(f"✅ İlk soru atandı: {ilk_soru.id}")
        else:
            print(f"❌ Soru bulunamadı!")
        
        bekleyen_oda.save()
        return redirect('karsilasma_oyun', oda_id=bekleyen_oda.oda_id)
    else:
        # Yeni oda oluştur
        print(f"🆕 Yeni oda oluşturuluyor...")
        yeni_oda = KarsilasmaOdasi.objects.create(
            oyuncu1=request.user,
            oyun_durumu='bekleniyor',
            secilen_ders=secilen_ders,
            sinav_tipi=sinav_tipi
        )
        print(f"✅ Yeni oda oluşturuldu: {yeni_oda.oda_id}")
        
        return redirect('karsilasma_oyun', oda_id=yeni_oda.oda_id)

    
    # Kullanıcının aktif odasını kontrol et
    aktif_oda = KarsilasmaOdasi.objects.select_related('oyuncu1', 'oyuncu2').filter(
        models.Q(oyuncu1=request.user) | models.Q(oyuncu2=request.user),
        oyun_durumu__in=['bekleniyor', 'oynaniyor']
    ).first()
    
    if aktif_oda:
        print(f"✅ Kullanıcının aktif odası bulundu: {aktif_oda.oda_id}")
        return redirect('karsilasma_oyun', oda_id=aktif_oda.oda_id)
    
    # Aynı dersi seçmiş bekleyen oda bul
    bekleyen_oda = KarsilasmaOdasi.objects.select_related('oyuncu1').filter(
        oyun_durumu='bekleniyor',
        oyuncu2=None,
        secilen_ders=secilen_ders,
        sinav_tipi=sinav_tipi
    ).exclude(oyuncu1=request.user).first()
    
    if bekleyen_oda:
        print(f"🔄 Bekleyen odaya katılıyor: {bekleyen_oda.oda_id}")
        bekleyen_oda.oyuncu2 = request.user
        bekleyen_oda.oyun_durumu = 'oynaniyor'
        bekleyen_oda.aktif_soru = _get_random_soru_by_ders(secilen_ders)
        bekleyen_oda.aktif_soru_no = 1
        bekleyen_oda.soru_baslangic_zamani = timezone.now()  # ✅ Zaman başlat
        bekleyen_oda.save()

        # İlk soruyu getir
        ilk_soru = _get_random_soru_by_ders(secilen_ders)
        if ilk_soru:
            bekleyen_oda.aktif_soru = ilk_soru
            bekleyen_oda.aktif_soru_no = 1
            bekleyen_oda.soru_baslangic_zamani = timezone.now()
            print(f"✅ İlk soru atandı: {ilk_soru.id}")
        else:
            print(f"❌ Soru bulunamadı!")

        bekleyen_oda.save() 
        return redirect('karsilasma_oyun', oda_id=bekleyen_oda.oda_id)
    else:
        # Yeni oda oluştur
        print(f"🆕 Yeni oda oluşturuluyor...")
        yeni_oda = KarsilasmaOdasi.objects.create(
            oyuncu1=request.user,
            oyun_durumu='bekleniyor',
            secilen_ders=secilen_ders,
            sinav_tipi=sinav_tipi
        )
        
        return redirect('karsilasma_oyun', oda_id=yeni_oda.oda_id)


def _get_random_soru_by_ders(ders='karisik'):
    """Seçilen derse göre rastgele soru getir"""
    print(f"🔍 Soru aranıyor: Ders={ders}")
    
    cache_key = f'karsilasma_soru_ids_{ders}'
    soru_ids = cache.get(cache_key)
    
    if soru_ids is None:
        if ders == 'karisik':
            soru_ids = list(Soru.objects.filter(
                karsilasmada_cikar=True
            ).values_list('id', flat=True))
        else:
            soru_ids = list(Soru.objects.filter(
                ders=ders,
                karsilasmada_cikar=True
            ).values_list('id', flat=True))
        
        cache.set(cache_key, soru_ids, 300)
        print(f"📝 {len(soru_ids)} soru bulundu")
    
    if soru_ids:
        random_id = random.choice(soru_ids)
        soru = Soru.objects.get(id=random_id)
        print(f"✅ Soru seçildi: ID={random_id}")
        return soru
    
    print(f"❌ Hiç soru bulunamadı!")
    return None


# ==================== BUL BAKALIM ====================

@login_required
def bul_bakalim_basla(request):
    ders = request.GET.get('ders')
    sinav_tipi = request.session.get('bulbakalim_sinav_tipi', 'ayt')
    
    cache_key = f'bulbakalim_sorular_{ders}_{sinav_tipi}'
    sorular = cache.get(cache_key)
    
    if sorular is None:
        if ders == "karisik":
            sorular = list(Soru.objects.filter(
                bul_bakalimda_cikar=True
            ).only('id').values_list('id', flat=True))
        else:
            sorular = list(Soru.objects.filter(
                ders=ders, 
                bul_bakalimda_cikar=True
            ).only('id').values_list('id', flat=True))
        
        cache.set(cache_key, sorular, 300)
    
    if len(sorular) < 5:
        messages.error(request, 'Yeterli soru yok!')
        return redirect('quiz_anasayfa')
    
    secilen_sorular = random.sample(sorular, min(5, len(sorular)))
    
    yeni_oyun = BulBakalimOyun.objects.create(
        oyuncu=request.user,
        sorular=secilen_sorular
    )
    
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
        'sure': 90,
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
    
    data = json.loads(request.body)
    cevap_id = data.get('cevap_id')
    
    if not cevap_id:
        return JsonResponse({'error': 'Cevap bulunamadı'}, status=400)
    
    cevap = Cevap.objects.select_related('soru').get(id=cevap_id)
    soru = cevap.soru
    
    oyun.cevaplar[str(soru.id)] = cevap_id
    
    if cevap.dogru_mu:
        oyun.dogru_sayisi += 1
    else:
        oyun.yanlis_sayisi += 1
    
    oyun.save()
    
    try:
        profil = request.user.profil
        profil.cozulen_soru_sayisi += 1
        profil.haftalik_cozulen += 1
        
        if cevap.dogru_mu:
            profil.toplam_dogru += 1
            profil.haftalik_dogru += 1
        else:
            profil.toplam_yanlis += 1
            profil.haftalik_yanlis += 1
        
        profil.save()
        
        oyun_ist, created = OyunModuIstatistik.objects.get_or_create(
            profil=profil,
            oyun_modu='bul_bakalim'
        )
        oyun_ist.cozulen_soru += 1
        if cevap.dogru_mu:
            oyun_ist.dogru_sayisi += 1
        else:
            oyun_ist.yanlis_sayisi += 1
        oyun_ist.save()
    
    except Exception as e:
        print(f"❌ İstatistik hatası: {e}")
    
    kalan_soru = 5 - len(oyun.cevaplar)
    
    if kalan_soru == 0:
        oyun.oyun_bitir()
        return JsonResponse({
            'oyun_bitti': True,
            'redirect_url': f'/bul-bakalim/{oyun.oyun_id}/sonuc/'
        })
    
    return JsonResponse({
        'dogru_mu': cevap.dogru_mu,
        'kalan_soru': kalan_soru,
        'dogru_sayisi': oyun.dogru_sayisi,
        'yanlis_sayisi': oyun.yanlis_sayisi,
    })


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
                    'dogru_mu': dogru_mu,
                }
                
                sonuclar.append(sonuc_item)
                
                if not dogru_mu:
                    yanlislar.append(sonuc_item)
            else:
                sonuc_item = {
                    'soru': soru,
                    'verilen_cevap': None,
                    'dogru_cevap': dogru_cevap,
                    'dogru_mu': False,
                }
                sonuclar.append(sonuc_item)
                yanlislar.append(sonuc_item)
        
        except Exception as e:
            print(f"❌ Sonuç hatası: {e}")
            continue
    
    try:
        profil = request.user.profil
        
        if oyun.toplam_puan > 0:
            profil.toplam_puan += oyun.toplam_puan
            profil.haftalik_puan += oyun.toplam_puan
            profil.save()
        
        oyun_ist, created = OyunModuIstatistik.objects.get_or_create(
            profil=profil,
            oyun_modu='bul_bakalim'
        )
        oyun_ist.oynanan_oyun_sayisi += 1
        oyun_ist.haftalik_oyun_sayisi += 1
        
        if oyun.dogru_sayisi >= 3:
            oyun_ist.kazanilan_oyun += 1
        else:
            oyun_ist.kaybedilen_oyun += 1
        
        oyun_ist.toplam_puan += oyun.toplam_puan
        oyun_ist.save()
        
        yeni_rozetler = rozet_kontrol_yap(profil)
        
        if yeni_rozetler:
            for rozet in yeni_rozetler:
                messages.success(request, f'🏆 YENİ ROZET! {rozet.icon} {rozet.get_kategori_display()}')
    
    except Exception as e:
        print(f"❌ Bul Bakalım sonuç hatası: {e}")
    
    context = {
        'oyun': oyun,
        'sonuclar': sonuclar,
        'yanlislar': yanlislar,
        'kazandi': oyun.dogru_sayisi >= 3,
        'aktif_ders': request.GET.get('ders', 'karisik'),
    }
    
    return render(request, 'quiz/bul_bakalim_sonuc.html', context)


@login_required
def bul_bakalim_ders_secimi(request):
    sinav_tipi = request.session.get('bulbakalim_sinav_tipi', 'ayt')
    ders_secenekleri = BulBakalimOyun.DERS_SECENEKLERI

    if request.method == 'POST':
        selected_ders = request.POST.get('selected_ders')
        return redirect('bul_bakalim_basla') + f'?ders={selected_ders}'

    context = {
        'ders_secenekleri': ders_secenekleri,
        'sinav_tipi': sinav_tipi,
    }
    return render(request, 'quiz/bul_bakalim_ders_secimi.html', context)


@login_required
def bul_bakalim_sinav_tipi_secimi(request):
    if request.method == 'POST':
        sinav_tipi = request.POST.get('sinav_tipi')
        request.session['bulbakalim_sinav_tipi'] = sinav_tipi
        return redirect('bul_bakalim_ders_secimi')
    return render(request, 'quiz/bul_bakalim_sinav_tipi_secimi.html')