from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from quiz.models import TabuKelime, TabuOyun
import json
import random
import logging

logger = logging.getLogger(__name__)

# ✅ BÖLÜM TANIMLARI
TABU_BOLUMLERI = [
    ('sayisal', 'Sayısal'),
    ('esit_agirlik', 'Eşit Ağırlık'),
    ('sozel', 'Sözel'),
    ('dil', 'Dil')
]

# ✅ BÖLÜM-KATEGORİ EŞLEŞTİRMESİ (Matematik YOK)
BOLUM_KATEGORILERI = {
    'sayisal': ['fizik', 'kimya', 'biyoloji'],
    'esit_agirlik': ['edebiyat', 'cografya', 'tarih'],
    'sozel':  ['edebiyat', 'cografya', 'tarih', 'felsefe'],
}

MAX_KELIME = 10
SURE = 60


def tabu_anasayfa(request):
    """Tabu ana sayfa - Bölüm seçimine yönlendir"""
    return redirect('tabu_bolum_sec')


def tabu_bolum_sec(request):
    """Bölüm seçim ekranı"""
    if request.method == 'POST':
        secilen_bolum = request.POST.get('bolum')
        request.session['tabu_bolum'] = secilen_bolum
        logger.info(f"Tabu bölüm seçildi: {secilen_bolum}")
        return redirect('tabu_lobi')
    return render(request, 'quiz/tabu_bolum_yeni.html', {'bolumler': TABU_BOLUMLERI})


@login_required
def tabu_lobi(request):
    """Lobi ekranı - Takım isimlerini al"""
    bolum = request.session.get('tabu_bolum', None)
    
    # Bölüm seçilmemişse bölüm seçimine yönlendir
    if not bolum:
        logger.warning("Tabu bölüm seçilmeden lobi'ye girilmeye çalışıldı")
        return redirect('tabu_bolum_sec')
    
    kategoriler = BOLUM_KATEGORILERI.get(bolum, [])
    kelime_sayisi = TabuKelime.objects.filter(kategori__in=kategoriler).count()
    
    # Yeterli kelime yoksa uyarı
    if kelime_sayisi < MAX_KELIME:
        logger.warning(f"Yetersiz tabu kelimesi: Bölüm={bolum}, Mevcut={kelime_sayisi}")
    
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
        logger.info(f"Yeni Tabu oyunu: ID={yeni_oyun.id}, Bölüm={bolum}")
        return redirect('tabu_oyun', oyun_id=yeni_oyun.id)
    
    bolum_adi = dict(TABU_BOLUMLERI).get(bolum, 'Bilinmeyen')
    context = {
        'bolum': bolum,
        'bolum_adi': bolum_adi,
        'kelime_sayisi': kelime_sayisi,
        'kategoriler': kategoriler
    }
    return render(request, 'quiz/tabu_lobi.html', context)


@login_required
def tabu_oyun_basla(request):
    """Alternatif başlatma metodu"""
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
        logger.info(f"Tabu oyunu başlatıldı: ID={yeni_oyun.id}")
        return redirect('tabu_oyun', oyun_id=yeni_oyun.id)
    return render(request, 'quiz/tabu_basla.html')


@login_required
def tabu_oyun(request, oyun_id):
    """Tabu oyun ekranı"""
    oyun = get_object_or_404(TabuOyun, id=oyun_id)
    aktif_takim = oyun.aktif_takim
    gorulen_idler = request.session.get('gorulen_kelime_idler', [])
    ara_ekran = request.session.get('tabu_ara_ekran', True)

    # ✅ POST İSTEĞİ - ARA EKRANDAN TUR BAŞLATMA (AJAX)
    if request.method == 'POST':
        request.session['tabu_ara_ekran'] = False
        logger.debug(f"Ara ekran geçildi: Oyun={oyun_id}, Takım={aktif_takim}")
        return JsonResponse({
            'success': True,
            'message':  'Tur başlatıldı!'
        })

    # Ara ekran göster
    if ara_ekran:
        takim_adi = oyun.takim_a_adi if aktif_takim == 'A' else oyun.takim_b_adi
        context = {
            'oyun':  oyun,
            'aktif_takim': aktif_takim,
            'takim_adi': takim_adi,
            'MAX_KELIME': MAX_KELIME,
            'SURE': SURE,
            'ara_ekran': True
        }
        return render(request, 'quiz/tabu.html', context)

    # Bölüm kategorilerini al
    bolum = request.session.get('tabu_bolum', 'sayisal')
    kategoriler = BOLUM_KATEGORILERI.get(bolum, ['fizik'])
    
    # Kalan kelimeleri bul
    kalan_kelimeler = list(
        TabuKelime.objects
        .filter(kategori__in=kategoriler)
        .exclude(id__in=gorulen_idler)
        .values_list('id', flat=True)
    )
    
    # Kelime biterse veya limit dolunca tur değiştir
    if not kalan_kelimeler or len(gorulen_idler) >= MAX_KELIME:
        request.session['tabu_ara_ekran'] = True
        if aktif_takim == 'A':
            oyun.aktif_takim = 'B'
            oyun.save()
            request.session['gorulen_kelime_idler'] = []
            logger.info(f"Tur değişti: Oyun={oyun_id}, Yeni Takım=B")
            return redirect('tabu_oyun', oyun_id=oyun.id)
        else:
            oyun.oyun_durumu = 'bitti'
            oyun.save()
            logger.info(f"Oyun bitti: Oyun={oyun_id}, A:{oyun.takim_a_skor} B:{oyun.takim_b_skor}")
            return redirect('tabu_sonuc', oyun_id=oyun.id)
    
    # Rastgele kelime seç
    kelime_id = random.choice(kalan_kelimeler)
    kelime = TabuKelime.objects.prefetch_related('yasakli_kelimeler').get(id=kelime_id)
    yasaklilar = kelime.yasakli_kelimeler.all()
    
    context = {
        'oyun':  oyun,
        'kelime': kelime,
        'yasaklilar': yasaklilar,
        'aktif_takim': aktif_takim,
        'takim_adi': oyun.takim_a_adi if aktif_takim == 'A' else oyun.takim_b_adi,
        'MAX_KELIME': MAX_KELIME,
        'SURE': SURE,
        'gorulen_sayi': len(gorulen_idler),
        'ara_ekran': False
    }
    return render(request, 'quiz/tabu.html', context)


@login_required
def tabu_tur_guncelle(request, oyun_id):
    """AJAX ile tur güncelleme"""
    if request.method == 'POST':
        oyun = get_object_or_404(TabuOyun, id=oyun_id)
        data = json.loads(request.body)
        action = data.get('action')
        mevcut_kelime_id = data.get('mevcut_kelime_id')
        gorulen_idler = request.session.get('gorulen_kelime_idler', [])
        aktif_takim = oyun.aktif_takim

        # Skor güncelle
        if aktif_takim == 'A':
            if action == 'dogru':
                oyun.takim_a_skor += 1
            elif action == 'tabu':
                oyun.takim_a_skor = max(0, oyun.takim_a_skor - 1)
        else:
            if action == 'dogru':
                oyun.takim_b_skor += 1
            elif action == 'tabu':
                oyun.takim_b_skor = max(0, oyun.takim_b_skor - 1)
        oyun.save()

        logger.debug(f"Skor güncellendi: Oyun={oyun_id}, Action={action}, Takım={aktif_takim}")

        # Görülen kelimeyi kaydet
        if mevcut_kelime_id and mevcut_kelime_id not in gorulen_idler: 
            gorulen_idler.append(mevcut_kelime_id)
        request.session['gorulen_kelime_idler'] = gorulen_idler

        # Limit kontrolü
        if len(gorulen_idler) >= MAX_KELIME:
            return JsonResponse({'tur_bitti_kelime_yok': True})

        # Yeni kelime getir
        bolum = request.session.get('tabu_bolum', 'sayisal')
        kategoriler = BOLUM_KATEGORILERI.get(bolum, ['fizik'])
        
        kalan_kelimeler = list(
            TabuKelime.objects
            .filter(kategori__in=kategoriler)
            .exclude(id__in=gorulen_idler)
            .values_list('id', flat=True)
        )
        
        if not kalan_kelimeler: 
            return JsonResponse({'tur_bitti_kelime_yok': True})
        
        yeni_kelime_id = random.choice(kalan_kelimeler)
        yeni_kelime = TabuKelime.objects.prefetch_related('yasakli_kelimeler').get(id=yeni_kelime_id)
        yasaklilar = list(yeni_kelime.yasakli_kelimeler.values_list('yasakli_kelime', flat=True))
        
        return JsonResponse({
            'kelime_id': yeni_kelime.id,
            'kelime': yeni_kelime.kelime,
            'yasaklilar': yasaklilar,
            'takim_a_skor': oyun.takim_a_skor,
            'takim_b_skor': oyun.takim_b_skor
        })
    return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required
def tabu_tur_degistir(request, oyun_id):
    """Tur değiştirme"""
    if request.method == 'POST':
        oyun = get_object_or_404(TabuOyun, id=oyun_id)
        aktif_takim = oyun.aktif_takim
        if aktif_takim == 'A':
            oyun.aktif_takim = 'B'
            oyun.save()
            request.session['gorulen_kelime_idler'] = []
            request.session['tabu_ara_ekran'] = True
            logger.info(f"Tur değişti: Oyun={oyun_id}, Yeni Takım=B")
            return JsonResponse({
                'oyun_bitti': False,
                'redirect_url': f'/quiz/tabu/oyun/{oyun.id}/'
            })
        else:
            oyun.oyun_durumu = 'bitti'
            oyun.save()
            logger.info(f"Oyun tamamlandı: Oyun={oyun_id}")
            return JsonResponse({
                'oyun_bitti': True,
                'redirect_url':  f'/quiz/tabu/sonuc/{oyun.id}/'
            })
    return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required
def tabu_sonuc(request, oyun_id):
    """Sonuç ekranı"""
    oyun = get_object_or_404(TabuOyun, id=oyun_id)
    if oyun.takim_a_skor > oyun.takim_b_skor:
        kazanan = oyun.takim_a_adi
    elif oyun.takim_b_skor > oyun.takim_a_skor:
        kazanan = oyun.takim_b_adi
    else:
        kazanan = "Berabere"
    
    context = {
        'oyun':  oyun,
        'kazanan': kazanan
    }
    return render(request, 'quiz/tabu_sonuc.html', context)