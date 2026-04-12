"""Günün Sorusu - kullanıcı facing view"""
from datetime import date
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Count

from quiz.models import GununSorusu, GununSorusuCevap, Cevap


def gunun_sorusu_view(request):
    bugun = GununSorusu.objects.filter(tarih=date.today()).select_related('soru').first()

    kullanici_cevabi = None
    cevaplar = []
    toplam_cevaplayan = 0
    dogru_oran = 0

    if bugun:
        cevaplar = list(bugun.soru.cevaplar.all())
        toplam_cevaplayan = GununSorusuCevap.objects.filter(gunun_sorusu=bugun).count()

        if toplam_cevaplayan > 0:
            dogru_sayisi = GununSorusuCevap.objects.filter(gunun_sorusu=bugun, dogru_mu=True).count()
            dogru_oran = round(100 * dogru_sayisi / toplam_cevaplayan)

        if request.user.is_authenticated:
            kullanici_cevabi = GununSorusuCevap.objects.filter(
                kullanici=request.user, gunun_sorusu=bugun
            ).first()

    return render(request, 'quiz/gunun_sorusu.html', {
        'gunun_sorusu': bugun,
        'cevaplar': cevaplar,
        'kullanici_cevabi': kullanici_cevabi,
        'toplam_cevaplayan': toplam_cevaplayan,
        'dogru_oran': dogru_oran,
    })


@login_required
def gunun_sorusu_cevapla(request):
    if request.method != 'POST':
        return JsonResponse({'ok': False}, status=405)

    cevap_id = request.POST.get('cevap_id')
    gs_id = request.POST.get('gunun_sorusu_id')

    try:
        gunun_sorusu = GununSorusu.objects.get(id=gs_id, tarih=date.today())
        secilen_cevap = Cevap.objects.get(id=cevap_id, soru=gunun_sorusu.soru)
    except (GununSorusu.DoesNotExist, Cevap.DoesNotExist):
        return JsonResponse({'ok': False, 'hata': 'Geçersiz soru veya cevap.'})

    # Zaten cevapladı mı?
    if GununSorusuCevap.objects.filter(kullanici=request.user, gunun_sorusu=gunun_sorusu).exists():
        return JsonResponse({'ok': False, 'hata': 'Zaten cevapladınız.'})

    dogru_mu = secilen_cevap.dogru_mu
    GununSorusuCevap.objects.create(
        kullanici=request.user,
        gunun_sorusu=gunun_sorusu,
        secilen_cevap=secilen_cevap,
        dogru_mu=dogru_mu,
    )

    # XP ver
    if dogru_mu:
        try:
            profil = request.user.profil
            profil.xp_ekle(gunun_sorusu.bonus_xp)
        except Exception:
            pass

    dogru_cevap = gunun_sorusu.soru.cevaplar.filter(dogru_mu=True).first()
    return JsonResponse({
        'ok': True,
        'dogru_mu': dogru_mu,
        'bonus_xp': gunun_sorusu.bonus_xp if dogru_mu else 0,
        'dogru_cevap_id': dogru_cevap.id if dogru_cevap else None,
    })
