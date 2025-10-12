from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import TabuKelime, TabuOyun, Soru, KarsilasmaOdasi, Cevap
from django.http import JsonResponse
from django.db import models, transaction
import json

# --- TAM VE EKSİKSİZ TABU OYUNU FONKSİYONLARI ---

@login_required
def tabu_lobi(request):
    if request.method == 'POST':
        takim_a_adi = request.POST.get('takim_a', 'Takım A'); takim_b_adi = request.POST.get('takim_b', 'Takım B')
        yeni_oyun = TabuOyun.objects.create(takim_a_adi=takim_a_adi, takim_b_adi=takim_b_adi, tur_sayisi=1)
        request.session['gorulen_kelime_idler'] = []
        return redirect('tabu_oyna', oyun_id=yeni_oyun.id)
    return render(request, 'quiz/tabu_lobi.html')

@login_required
def tabu_oyna(request, oyun_id):
    oyun = get_object_or_404(TabuOyun, id=oyun_id)
    gorulen_idler = request.session.get('gorulen_kelime_idler', [])
    kelime = TabuKelime.objects.exclude(id__in=gorulen_idler).order_by('?').first()
    if not kelime:
        oyun.oyun_durumu = 'bitti'; oyun.save()
        return redirect('tabu_sonuc', oyun_id=oyun.id)
    yasaklilar = kelime.yasakli_kelimeler.all()
    context = {'oyun': oyun, 'kelime': kelime, 'yasaklilar': yasaklilar}
    return render(request, 'quiz/tabu.html', context)

@login_required
def tabu_tur_guncelle(request, oyun_id):
    if request.method == 'POST':
        oyun = get_object_or_404(TabuOyun, id=oyun_id); data = json.loads(request.body)
        action = data.get('action'); mevcut_kelime_id = data.get('mevcut_kelime_id')
        if oyun.aktif_takim == 'A':
            if action == 'dogru': oyun.takim_a_skor += 1
            elif action == 'tabu': oyun.takim_a_skor -= 1
        else:
            if action == 'dogru': oyun.takim_b_skor += 1
            elif action == 'tabu': oyun.takim_b_skor -= 1
        oyun.save()
        gorulen_idler = request.session.get('gorulen_kelime_idler', [])
        if mevcut_kelime_id and mevcut_kelime_id not in gorulen_idler: gorulen_idler.append(mevcut_kelime_id)
        yeni_kelime = TabuKelime.objects.exclude(id__in=gorulen_idler).order_by('?').first()
        if not yeni_kelime: return JsonResponse({'tur_bitti_kelime_yok': True})
        request.session['gorulen_kelime_idler'] = gorulen_idler
        yasaklilar = list(yeni_kelime.yasakli_kelimeler.values_list('yasakli_kelime', flat=True))
        response_data = {'kelime_id': yeni_kelime.id, 'kelime': yeni_kelime.kelime, 'yasaklilar': yasaklilar, 'takim_a_skor': oyun.takim_a_skor, 'takim_b_skor': oyun.takim_b_skor}
        return JsonResponse(response_data)
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def tabu_tur_degistir(request, oyun_id):
    if request.method == 'POST':
        oyun = get_object_or_404(TabuOyun, id=oyun_id)
        if oyun.oyun_modu == 'normal' and oyun.aktif_takim == 'B':
            if oyun.takim_a_skor == oyun.takim_b_skor and TabuKelime.objects.exclude(id__in=request.session.get('gorulen_kelime_idler', [])).exists():
                oyun.oyun_modu = 'uzatma'; oyun.aktif_takim = 'A'; oyun.save()
                return JsonResponse({'uzatma': True, 'yeni_aktif_takim_adi': oyun.takim_a_adi})
            else:
                oyun.oyun_durumu = 'bitti'; oyun.save()
                return JsonResponse({'oyun_bitti': True, 'redirect_url': f'/quiz/tabu/oyun/{oyun.id}/sonuc/'})
        elif oyun.oyun_modu == 'uzatma' and oyun.aktif_takim == 'B':
            oyun.oyun_durumu = 'bitti'; oyun.save()
            return JsonResponse({'oyun_bitti': True, 'redirect_url': f'/quiz/tabu/oyun/{oyun.id}/sonuc/'})
        else:
            oyun.aktif_takim = 'B'; oyun.save()
            request.session['gorulen_kelime_idler'] = []
            return JsonResponse({'oyun_bitti': False, 'yeni_aktif_takim_adi': oyun.takim_b_adi})
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def tabu_sonuc(request, oyun_id):
    oyun = get_object_or_404(TabuOyun, id=oyun_id)
    context = {'oyun': oyun, 'kazanan': oyun.get_kazanan()}
    return render(request, 'quiz/tabu_sonuc.html', context)


# --- NİHAİ KARŞILAŞMA FONKSİYONLARI ("YARIŞ DURUMU" DÜZELTİLDİ) ---

@login_required
def karsilasma_rakip_bul(request):
    aktif_oda = KarsilasmaOdasi.objects.filter(models.Q(oyuncu1=request.user) | models.Q(oyuncu2=request.user), oyun_durumu__in=['bekleniyor', 'oynaniyor']).first()
    if aktif_oda: return redirect('karsilasma_oyun', oda_id=aktif_oda.oda_id)
    bekleyen_oda = KarsilasmaOdasi.objects.filter(oyun_durumu='bekleniyor', oyuncu2=None).exclude(oyuncu1=request.user).first()
    if bekleyen_oda:
        bekleyen_oda.oyuncu2 = request.user
        bekleyen_oda.oyun_durumu = 'oynaniyor'
        bekleyen_oda.aktif_soru = Soru.objects.order_by('?').first()
        bekleyen_oda.save()
        return redirect('karsilasma_oyun', oda_id=bekleyen_oda.oda_id)
    else:
        yeni_oda = KarsilasmaOdasi.objects.create(oyuncu1=request.user)
        return redirect('karsilasma_oyun', oda_id=yeni_oda.oda_id)

@login_required
def karsilasma_oyun(request, oda_id):
    oda = get_object_or_404(KarsilasmaOdasi, oda_id=oda_id)
    context = {'oda': oda}
    return render(request, 'quiz/karsilasma_oyun.html', context)

@login_required
@transaction.atomic
def karsilasma_durum_guncelle(request, oda_id):
    # DÜZELTME: 'select_for_update()' ile bu oyun odasının satırını kilitliyoruz.
    oda = get_object_or_404(KarsilasmaOdasi.objects.select_for_update(), oda_id=oda_id)
    
    if request.method == 'POST':
        data = json.loads(request.body)
        cevap_id = data.get('cevap_id')
        cevap_obj = Cevap.objects.get(id=cevap_id)
        
        # Sadece odanın aktif sorusuna cevap verilebilir
        if oda.aktif_soru and cevap_obj.soru == oda.aktif_soru:
            is_oyuncu1 = (oda.oyuncu1 == request.user)
            
            # Oyuncunun daha önce cevap verip vermediğini KİLİT ALTINDA kontrol et
            if (is_oyuncu1 and not oda.oyuncu1_cevapladi) or (not is_oyuncu1 and not oda.oyuncu2_cevapladi):
                if is_oyuncu1:
                    oda.oyuncu1_cevapladi = True
                else:
                    oda.oyuncu2_cevapladi = True

                if cevap_obj.dogru_mu:
                    puan = 10
                    bonus = 2
                    if oda.ilk_dogru_cevaplayan is None:
                        oda.ilk_dogru_cevaplayan = request.user
                        if is_oyuncu1: oda.oyuncu1_skor += puan + bonus
                        else: oda.oyuncu2_skor += puan + bonus
                    else:
                        if is_oyuncu1: oda.oyuncu1_skor += puan
                        else: oda.oyuncu2_skor += puan
            
            # Her iki oyuncu da cevapladıysa, yeni soruya geç
            if oda.oyuncu1_cevapladi and oda.oyuncu2_cevapladi:
                oda.aktif_soru = Soru.objects.order_by('?').first()
                oda.oyuncu1_cevapladi = False
                oda.oyuncu2_cevapladi = False
                oda.ilk_dogru_cevaplayan = None
            
            oda.save() # Kilit burada açılır.

    # Her durumda odanın en güncel durumunu döndür
    soru_obj = oda.aktif_soru
    cevaplar = []
    if soru_obj:
        cevaplar_qs = Cevap.objects.filter(soru=soru_obj)
        cevaplar = [{'id': c.id, 'metin': c.metin} for c in cevaplar_qs]

    response_data = {
        'oyuncu1_skor': oda.oyuncu1_skor, 'oyuncu2_skor': oda.oyuncu2_skor,
        'oyuncu2_adi': oda.oyuncu2.username if oda.oyuncu2 else None,
        'oyun_durumu': oda.oyun_durumu,
        'soru': soru_obj.metin if soru_obj else "Oyun Bitti! Sonuçlar bekleniyor...",
        'cevaplar': cevaplar,
        'oyuncu1_cevapladi': oda.oyuncu1_cevapladi,
        'oyuncu2_cevapladi': oda.oyuncu2_cevapladi,
    }
    return JsonResponse(response_data)