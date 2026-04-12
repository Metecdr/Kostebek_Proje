"""
Yanlışlarıma Dön — Kullanıcının yanlış cevapladığı soruları toplar, konu konu gösterir.
"""
import random
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from quiz.models import Soru, Cevap, KullaniciCevap, BulBakalimOyun
from collections import defaultdict


@login_required
def yanlislarima_don(request):
    user = request.user

    # --- Karşılaşma yanlışları ---
    karsilasma_yanlis_soru_ids = set(
        KullaniciCevap.objects.filter(kullanici=user, dogru_mu=False)
        .values_list('soru_id', flat=True)
        .distinct()
    )

    # --- Bul Bakalım yanlışları ---
    bb_yanlis_soru_ids = set()
    son_oyunlar = (
        BulBakalimOyun.objects
        .filter(oyuncu=user, oyun_durumu='bitti')
        .order_by('-oyun_id')[:50]
    )
    for oyun in son_oyunlar:
        cevaplar = oyun.cevaplar  # {str(soru_id): cevap_id, ...}
        if not cevaplar:
            continue
        cevap_ids = [v for v in cevaplar.values() if v is not None]
        if not cevap_ids:
            continue
        dogru_ids = set(
            Cevap.objects.filter(id__in=cevap_ids, dogru_mu=True).values_list('id', flat=True)
        )
        for soru_id_str, cevap_id in cevaplar.items():
            if cevap_id is None or cevap_id not in dogru_ids:
                try:
                    bb_yanlis_soru_ids.add(int(soru_id_str))
                except (ValueError, TypeError):
                    pass

    # --- Sorular konu/ders grubuna göre ---
    def grupla(soru_ids):
        """soru_ids setini ders → konu → [soru] şeklinde gruplar"""
        if not soru_ids:
            return {}
        sorular = (
            Soru.objects.filter(id__in=soru_ids)
            .select_related('konu')
            .order_by('ders', 'konu__isim')
        )
        gruplar = defaultdict(lambda: defaultdict(list))
        for s in sorular:
            ders = s.ders or 'diger'
            konu_isim = s.konu.isim if s.konu else 'Genel'
            konu_id = s.konu_id if s.konu_id else 0
            gruplar[ders][(konu_id, konu_isim)].append(s)
        # defaultdict → normal dict
        return {
            ders: [
                {'konu_id': k[0], 'konu_isim': k[1], 'sorular': v, 'sayi': len(v)}
                for k, v in konular.items()
            ]
            for ders, konular in gruplar.items()
        }

    bb_gruplar = grupla(bb_yanlis_soru_ids)
    karsilasma_gruplar = grupla(karsilasma_yanlis_soru_ids)

    return render(request, 'quiz/yanlislarima_don.html', {
        'bb_gruplar': bb_gruplar,
        'karsilasma_gruplar': karsilasma_gruplar,
        'bb_toplam': len(bb_yanlis_soru_ids),
        'karsilasma_toplam': len(karsilasma_yanlis_soru_ids),
    })


@login_required
def yanlis_tekrar_calis(request):
    """Belirli ders/konu için yanlış soruları alıp yeni bir BB oyunu başlat."""
    user = request.user
    mod = request.GET.get('mod', 'bb')          # 'bb' veya 'karsilasma'
    ders = request.GET.get('ders', '')
    konu_id = request.GET.get('konu_id', '')

    # Hangi soru ID'leri yanlış?
    if mod == 'karsilasma':
        yanlis_ids = set(
            KullaniciCevap.objects.filter(kullanici=user, dogru_mu=False)
            .values_list('soru_id', flat=True)
            .distinct()
        )
    else:  # bb
        yanlis_ids = set()
        son_oyunlar = (
            BulBakalimOyun.objects
            .filter(oyuncu=user, oyun_durumu='bitti')
            .order_by('-oyun_id')[:50]
        )
        for oyun in son_oyunlar:
            cevaplar = oyun.cevaplar or {}
            cevap_ids = [v for v in cevaplar.values() if v is not None]
            dogru_ids = set(
                Cevap.objects.filter(id__in=cevap_ids, dogru_mu=True).values_list('id', flat=True)
            ) if cevap_ids else set()
            for soru_id_str, cevap_id in cevaplar.items():
                if cevap_id is None or cevap_id not in dogru_ids:
                    try:
                        yanlis_ids.add(int(soru_id_str))
                    except (ValueError, TypeError):
                        pass

    # Filtrele
    qs = Soru.objects.filter(id__in=yanlis_ids, bul_bakalimda_cikar=True)
    if ders:
        qs = qs.filter(ders__iexact=ders)
    if konu_id:
        qs = qs.filter(konu_id=konu_id)

    soru_ids = list(qs.values_list('id', flat=True))
    if len(soru_ids) < 1:
        from django.contrib import messages
        messages.error(request, 'Bu filtre için yeterli yanlış soru bulunamadı!')
        return redirect('yanlislarima_don')

    secilen = random.sample(soru_ids, min(10, len(soru_ids)))
    oyun = BulBakalimOyun.objects.create(
        oyuncu=user,
        sorular=secilen,
        selected_ders=ders or 'karisik',
        sinav_tipi='TYT',
    )
    return redirect('bul_bakalim_oyun', oyun_id=oyun.oyun_id)
