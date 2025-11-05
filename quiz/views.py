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
from django.core.cache import cache  # ✅ EKLE
from django.db.models import Prefetch  # ✅ EKLE
from django.utils import timezone
from datetime import timedelta
import json
import random  # ✅ EKLE

# ✅ ROZET SİSTEMİ İMPORT'LARI
from profile.models import OgrenciProfili, OyunModuIstatistik, DersIstatistik
from profile.rozet_kontrol import rozet_kontrol_yap


# ✅ QUIZ ANASAYFA
@login_required
def quiz_anasayfa(request):
    """Quiz ana sayfa - Oyun modları seçimi"""
    try:
        # ✅ select_related ile profil'i önceden çek
        profil = request.user.profil
        
        # ✅ Cache'den al (60 saniye)
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
        # Seçilen bölümü session'a kaydet
        request.session['tabu_bolum'] = secilen_bolum
        return redirect('tabu_lobi')  # lobiye yönlendir
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
    # kelimeler ile oyunu başlat, template'e gönder, vs.
    """Tabu lobi ekranı - takım isimleri giriliyor"""
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
    """Tabu oyunu başlat - eski, lobi ile birleştiği için opsiyonel"""
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
    """Tabu oyun ekranı ve ara ekran kontrolü"""
    oyun = get_object_or_404(TabuOyun, id=oyun_id)
    aktif_takim = oyun.aktif_takim
    gorulen_idler = request.session.get('gorulen_kelime_idler', [])
    ara_ekran = request.session.get('tabu_ara_ekran', True)

    # Ara ekranı göster (her tur başında)
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

    # Oyun ekranı (kelime göster)
    kelime = TabuKelime.objects.exclude(id__in=gorulen_idler).order_by('?').first()
    # Tur bitimi: kelime yok veya 10 kelime bitti
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
    """AJAX ile yeni kelime getir & skoru güncelle"""
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
                oyun.takim_a_skor -= 1
        else:
            if action == 'dogru':
                oyun.takim_b_skor += 1
            elif action == 'tabu':
                oyun.takim_b_skor -= 1
        oyun.save()

        # Görülen kelimeye ekle
        if mevcut_kelime_id and mevcut_kelime_id not in gorulen_idler:
            gorulen_idler.append(mevcut_kelime_id)
        request.session['gorulen_kelime_idler'] = gorulen_idler

        # 10 kelime bitti mi?
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
    """Süre bittiğinde veya kelime bittiğinde çağrılır"""
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

# --- NİHAİ KARŞILAŞMA FONKSİYONLARI ("YARIŞ DURUMU" DÜZELTİLDİ) ---

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
    
    if request.method == 'POST':
        data = json.loads(request.body)
        cevap_id = data.get('cevap_id')
        cevap_obj = Cevap.objects.select_related('soru').get(id=cevap_id)
        
        if oda.aktif_soru and cevap_obj.soru == oda.aktif_soru:
            is_oyuncu1 = (oda.oyuncu1 == request.user)
            
            if (is_oyuncu1 and not oda.oyuncu1_cevapladi) or (not is_oyuncu1 and not oda.oyuncu2_cevapladi):
                # ✅ CEVAP ZAMANINI KAYDET
                cevap_zamani = timezone.now()
                if is_oyuncu1:
                    oda.oyuncu1_cevapladi = True
                    oda.oyuncu1_cevap_zamani = cevap_zamani
                else:
                    oda.oyuncu2_cevapladi = True
                    oda.oyuncu2_cevap_zamani = cevap_zamani

                # ✅ COMBO + HIZ BONUSU İLE İSTATİSTİK GÜNCELLE
                _update_stats_with_combo(request.user, oda, cevap_obj, is_oyuncu1)
            
            # ✅ Her iki oyuncu da cevapladıysa
            if oda.oyuncu1_cevapladi and oda.oyuncu2_cevapladi:
                oda.aktif_soru_no += 1
                
                # ✅ OYUN BİTİŞ KONTROLÜ
                if oda.aktif_soru_no > oda.toplam_soru:
                    oda.oyun_durumu = 'bitti'
                    oda.aktif_soru = None
                    print(f"🏁 Oyun bitti! Oda: {oda_id}")
                else:
                    # ✅ YENİ SORU (3 saniye sonra değişecek - frontend'de)
                    oda.aktif_soru = _get_random_soru()
                    oda.oyuncu1_cevapladi = False
                    oda.oyuncu2_cevapladi = False
                    oda.ilk_dogru_cevaplayan = None
                    oda.soru_baslangic_zamani = timezone.now()  # ✅ YENİ SORU ZAMANI
                
                # ✅ Rozet kontrolü
                try:
                    profil = request.user.profil
                    if profil.cozulen_soru_sayisi % 10 == 0:
                        yeni_rozetler = rozet_kontrol_yap(profil)
                        if yeni_rozetler:
                            print(f"✅ {profil.kullanici.username} {len(yeni_rozetler)} yeni rozet kazandı!")
                except Exception as e:
                    print(f"❌ Rozet kontrol hatası: {e}")
            
            oda.save()

    # ✅ Response
    soru_obj = oda.aktif_soru
    cevaplar = []
    if soru_obj:
        cevaplar_qs = Cevap.objects.filter(soru=soru_obj).only('id', 'metin')
        cevaplar = [{'id': c.id, 'metin': c.metin} for c in cevaplar_qs]

    response_data = {
        'oyuncu1_skor': oda.oyuncu1_skor,
        'oyuncu2_skor': oda.oyuncu2_skor,
        'oyuncu1_combo': oda.oyuncu1_combo,  # ✅ COMBO EKLE
        'oyuncu2_combo': oda.oyuncu2_combo,  # ✅ COMBO EKLE
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


# ✅ YENİ FONKSİYON: COMBO + HIZ BONUSU
def _update_stats_with_combo(user, oda, cevap_obj, is_oyuncu1):
    """Combo ve hız bonusu ile istatistik güncelle"""
    try:
        profil = user.profil
        base_puan = 10
        bonus_puan = 0
        
        # ✅ HIZ BONUSU HESAPLA (5 saniye içinde)
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
            # ✅ COMBO ARTTIR
            if is_oyuncu1:
                oda.oyuncu1_combo += 1
                combo = oda.oyuncu1_combo
                oda.oyuncu1_dogru += 1
            else:
                oda.oyuncu2_combo += 1
                combo = oda.oyuncu2_combo
                oda.oyuncu2_dogru += 1
            
            # ✅ COMBO BONUSU (Max 20 puan)
            combo_bonus = min(combo * 2, 20)
            bonus_puan += combo_bonus
            
            print(f"🔥 {user.username} COMBO x{combo}! Bonus: +{combo_bonus}")
            
            # ✅ İLK DOĞRU CEVAPLAYAN BONUSU
            if oda.ilk_dogru_cevaplayan is None:
                oda.ilk_dogru_cevaplayan = user
                bonus_puan += 3
                print(f"🥇 {user.username} ilk doğru cevaplayan! +3 puan")
            
            # ✅ TOPLAM PUAN
            toplam_puan = base_puan + bonus_puan
            
            # ✅ SKORA EKLE
            if is_oyuncu1:
                oda.oyuncu1_skor += toplam_puan
            else:
                oda.oyuncu2_skor += toplam_puan
            
            # ✅ PROFİL İSTATİSTİKLERİ
            profil.toplam_dogru += 1
            profil.haftalik_dogru += 1
            profil.cozulen_soru_sayisi += 1
            profil.haftalik_cozulen += 1
            profil.toplam_puan += toplam_puan
            profil.haftalik_puan += toplam_puan
            profil.save()
            
            # ✅ OYUN MODU İSTATİSTİKLERİ
            oyun_ist, created = OyunModuIstatistik.objects.get_or_create(
                profil=profil,
                oyun_modu='karsilasma'
            )
            oyun_ist.cozulen_soru += 1
            oyun_ist.dogru_sayisi += 1
            oyun_ist.toplam_puan += toplam_puan
            oyun_ist.save()
            
            print(f"✅ {user.username} +{toplam_puan} puan kazandı! (Base: {base_puan}, Bonus: {bonus_puan})")
            
        else:
            # ✅ YANLIŞ CEVAP - COMBO SIFIRLA
            if is_oyuncu1:
                oda.oyuncu1_combo = 0
                oda.oyuncu1_yanlis += 1
            else:
                oda.oyuncu2_combo = 0
                oda.oyuncu2_yanlis += 1
            
            print(f"❌ {user.username} yanlış cevap! Combo sıfırlandı.")
            
            # ✅ PROFİL İSTATİSTİKLERİ
            profil.toplam_yanlis += 1
            profil.haftalik_yanlis += 1
            profil.cozulen_soru_sayisi += 1
            profil.haftalik_cozulen += 1
            profil.save()
            
            # ✅ OYUN MODU İSTATİSTİKLERİ
            oyun_ist, created = OyunModuIstatistik.objects.get_or_create(
                profil=profil,
                oyun_modu='karsilasma'
            )
            oyun_ist.cozulen_soru += 1
            oyun_ist.yanlis_sayisi += 1
            oyun_ist.save()
        
        # ✅ Cache'i temizle
        cache_key = f'karsilasma_ist_{profil.id}'
        cache.delete(cache_key)
        
    except Exception as e:
        print(f"❌ İstatistik güncelleme hatası: {e}")


# ✅ KARŞILAŞMA SONUÇ SAYFASI (YENİ)
@login_required
def karsilasma_sonuc(request, oda_id):
    """Karşılaşma oyunu bittiğinde sonuç sayfası"""
    oda = get_object_or_404(KarsilasmaOdasi, oda_id=oda_id)
    
    # ✅ OYUN BİTTİ - GALİBİYET/MAĞLUBİYET İSTATİSTİKLERİ
    try:
        profil = request.user.profil
        
        oyun_ist, created = OyunModuIstatistik.objects.get_or_create(
            profil=profil,
            oyun_modu='karsilasma'
        )
        
        oyun_ist.oynanan_oyun_sayisi += 1
        oyun_ist.haftalik_oyun_sayisi += 1
        
        # Kazanan belirleme
        is_oyuncu1 = (oda.oyuncu1 == request.user)
        kazandim = (is_oyuncu1 and oda.oyuncu1_skor > oda.oyuncu2_skor) or \
                   (not is_oyuncu1 and oda.oyuncu2_skor > oda.oyuncu1_skor)
        
        if kazandim:
            oyun_ist.kazanilan_oyun += 1
            profil.toplam_puan += 50  # Galibiyet bonusu
            profil.haftalik_puan += 50
        else:
            oyun_ist.kaybedilen_oyun += 1
        
        oyun_ist.save()
        profil.save()
        
        # ✅ ROZET KONTROLÜ
        yeni_rozetler = rozet_kontrol_yap(profil)
        
        if yeni_rozetler:
            for rozet in yeni_rozetler:
                messages.success(request, f'🏆 YENİ ROZET! {rozet.icon} {rozet.get_kategori_display()}')
    
    except Exception as e:
        print(f"❌ Karşılaşma sonuç hatası: {e}")
    
    context = {
        'oda': oda,
        'kazandim': kazandim,
    }
    return render(request, 'quiz/karsilasma_sonuc.html', context)

    # ✅ BUL BAKALIM OYUNU

# ✅ KARŞILAŞMA RAKIP BUL (Optimized)
@login_required
def karsilasma_rakip_bul(request):
    """Rakip bulma ve eşleştirme"""
    
    # ✅ Aktif oda kontrolü
    aktif_oda = KarsilasmaOdasi.objects.select_related('oyuncu1', 'oyuncu2').filter(
        models.Q(oyuncu1=request.user) | models.Q(oyuncu2=request.user),
        oyun_durumu__in=['bekleniyor', 'oynaniyor']
    ).first()
    
    if aktif_oda:
        return redirect('karsilasma_oyun', oda_id=aktif_oda.oda_id)
    
    # ✅ Bekleyen oda ara
    bekleyen_oda = KarsilasmaOdasi.objects.select_related('oyuncu1').filter(
        oyun_durumu='bekleniyor',
        oyuncu2=None
    ).exclude(oyuncu1=request.user).first()
    
    if bekleyen_oda:
        # ✅ Oyuncu 2 katıldı
        bekleyen_oda.oyuncu2 = request.user
        bekleyen_oda.oyun_durumu = 'oynaniyor'
        
        # ✅ İLK SORUYU ATAR
        bekleyen_oda.aktif_soru = _get_random_soru()
        bekleyen_oda.aktif_soru_no = 1
        
        bekleyen_oda.save()
        
        print(f"✅ Oyuncu 2 katıldı! İlk soru: {bekleyen_oda.aktif_soru}")
        
        return redirect('karsilasma_oyun', oda_id=bekleyen_oda.oda_id)
    else:
        # ✅ Yeni oda oluştur (beklemede)
        yeni_oda = KarsilasmaOdasi.objects.create(
            oyuncu1=request.user,
            oyun_durumu='bekleniyor'
        )
        
        print(f"✅ Yeni oda oluşturuldu: {yeni_oda.oda_id}")
        
        return redirect('karsilasma_oyun', oda_id=yeni_oda.oda_id)


# ✅ OPTIMIZE EDİLMİŞ RANDOM SORU SEÇİMİ
def _get_random_soru():
    """Cache'li ve optimize edilmiş random soru seçimi"""
    cache_key = 'all_soru_ids'
    soru_ids = cache.get(cache_key)
    
    if soru_ids is None:
        soru_ids = list(Soru.objects.values_list('id', flat=True))
        cache.set(cache_key, soru_ids, 300)  # 5 dakika cache
    
    if soru_ids:
        random_id = random.choice(soru_ids)
        return Soru.objects.get(id=random_id)
    return None


# BUL BAKALIM OYUNU FONKSİYONLARINI EKLE

# ✅ BUL BAKALIM BAŞLA (Optimized)
@login_required
def bul_bakalim_basla(request):
    """Bul Bakalım oyununu başlat"""
    ders = request.GET.get('ders')
    sinav_tipi = request.session.get('bulbakalim_sinav_tipi', 'ayt')
    
    # ✅ Cache'li soru seçimi
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
        
        cache.set(cache_key, sorular, 300)  # 5 dakika cache
    
    if len(sorular) < 5:
        messages.error(request, 'Yeterli soru yok! En az 5 soru olmalı.')
        return redirect('quiz_anasayfa')
    
    # Random 5 soru seç
    secilen_sorular = random.sample(sorular, min(5, len(sorular)))
    
    # Yeni oyun oluştur
    yeni_oyun = BulBakalimOyun.objects.create(
        oyuncu=request.user,
        sorular=secilen_sorular
    )
    
    return redirect('bul_bakalim_oyun', oyun_id=yeni_oyun.oyun_id)


# ✅ BUL BAKALIM OYUN (Optimized)
@login_required
def bul_bakalim_oyun(request, oyun_id):
    """Bul Bakalım oyun sayfası"""
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
    
    # ✅ prefetch_related ile cevapları önceden çek
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


# ✅ BUL BAKALIM CEVAPLA (Optimized)
@login_required
def bul_bakalim_cevapla(request, oyun_id):
    """Soruya cevap ver"""
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
    
    # ✅ select_related ile soru'yu önceden çek
    cevap = Cevap.objects.select_related('soru').get(id=cevap_id)
    soru = cevap.soru
    
    # Cevabı kaydet
    oyun.cevaplar[str(soru.id)] = cevap_id
    
    # Doğru mu?
    if cevap.dogru_mu:
        oyun.dogru_sayisi += 1
    else:
        oyun.yanlis_sayisi += 1
    
    oyun.save()
    
    # ✅ PROFİL İSTATİSTİKLERİNİ GÜNCELLE (Optimize edildi)
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
        
        # Oyun modu istatistiği
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
        print(f"❌ İstatistik güncelleme hatası: {e}")
    
    # Kaç soru kaldı?
    kalan_soru = 5 - len(oyun.cevaplar)
    
    if kalan_soru == 0:
        # Son soru, oyunu bitir
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


# ✅ BUL BAKALIM SONUÇ (Optimized)
@login_required
def bul_bakalim_sonuc(request, oyun_id):
    """Bul Bakalım sonuç sayfası"""
    oyun = get_object_or_404(
        BulBakalimOyun.objects.select_related('oyuncu'), 
        oyun_id=oyun_id, 
        oyuncu=request.user
    )
    
    # Oyun bitmemişse bitir
    if oyun.oyun_durumu != 'bitti':
        oyun.oyun_bitir()
    
    # ✅ DETAYLI SONUÇLARI AL (Optimize edildi)
    sonuclar = []
    yanlislar = []
    
    # ✅ Tüm soruları ve cevapları tek sorguda çek
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
            print(f"❌ Sonuç alma hatası (Soru ID: {soru_id}): {e}")
            continue
    
    # ✅ PROFİL İSTATİSTİKLERİNİ GÜNCELLE
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
        
        # ✅ ROZET KONTROLÜ
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


# ✅ BUL BAKALIM DERS SEÇİMİ
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


# ✅ BUL BAKALIM SINAV TİPİ SEÇİMİ
@login_required
def bul_bakalim_sinav_tipi_secimi(request):
    if request.method == 'POST':
        sinav_tipi = request.POST.get('sinav_tipi')
        request.session['bulbakalim_sinav_tipi'] = sinav_tipi
        return redirect('bul_bakalim_ders_secimi')
    return render(request, 'quiz/bul_bakalim_sinav_tipi_secimi.html')