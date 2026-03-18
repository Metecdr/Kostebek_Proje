from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db import transaction
from django.contrib import messages
from magaza.models import MagazaUrun, SatinAlma, KullaniciEnvanter
import logging

logger = logging.getLogger(__name__)


def envanter_getir_veya_olustur(kullanici):
    """Kullanıcının envanterini getir, yoksa oluştur"""
    envanter, _ = KullaniciEnvanter.objects.get_or_create(kullanici=kullanici)
    return envanter


@login_required
def magaza(request):
    """Mağaza ana sayfası"""
    profil = request.user.profil
    envanter = envanter_getir_veya_olustur(request.user)

    # Sahip olunan ürün id'leri
    sahip_olunan_ids = set(
        SatinAlma.objects.filter(kullanici=request.user).values_list('urun_id', flat=True)
    )

    unvanlar = MagazaUrun.objects.filter(kategori='unvan', aktif=True)
    cerceveler = MagazaUrun.objects.filter(kategori='cerceve', aktif=True)
    temalar = MagazaUrun.objects.filter(kategori='tema', aktif=True)

    context = {
        'profil': profil,
        'envanter': envanter,
        'unvanlar': unvanlar,
        'cerceveler': cerceveler,
        'temalar': temalar,
        'sahip_olunan_ids': sahip_olunan_ids,
        'toplam_puan': profil.toplam_puan,
    }
    return render(request, 'magaza/magaza.html', context)


@login_required
@transaction.atomic
def satin_al(request, urun_id):
    """Ürün satın alma"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'POST gerekli'}, status=400)

    urun = get_object_or_404(MagazaUrun, id=urun_id, aktif=True)
    profil = request.user.profil

    # Zaten sahip mi?
    if SatinAlma.objects.filter(kullanici=request.user, urun=urun).exists():
        return JsonResponse({'success': False, 'message': 'Bu ürüne zaten sahipsiniz!'})

    # Yeterli puan var mı?
    if profil.toplam_puan < urun.fiyat:
        return JsonResponse({
            'success': False,
            'message': f'Yetersiz puan! {urun.fiyat - profil.toplam_puan} puan daha kazanman gerekiyor.'
        })

    # Satın al
    profil.toplam_puan -= urun.fiyat
    profil.save()

    SatinAlma.objects.create(
        kullanici=request.user,
        urun=urun,
        odenen_puan=urun.fiyat
    )

    # Bildirim gönder
    try:
        from profile.bildirim_helper import bildirim_gonder
        bildirim_gonder(
            kullanici=request.user,
            tip='basari',
            baslik=f'🛒 {urun.isim} Satın Alındı!',
            mesaj=f'{urun.icon} {urun.isim} envanterine eklendi! Profil düzenleme sayfasından aktif edebilirsin.',
            icon='🛒'
        )
    except Exception as e:
        logger.error(f"Satın alma bildirimi hatası: {e}")

    logger.info(f"Satın alma: {request.user.username} - {urun.isim} ({urun.fiyat} puan)")

    return JsonResponse({
        'success': True,
        'message': f'✅ {urun.isim} satın alındı!',
        'kalan_puan': profil.toplam_puan,
    })


@login_required
def envanter(request):
    """Kullanıcının envanteri"""
    envanter = envanter_getir_veya_olustur(request.user)

    satin_almalar = SatinAlma.objects.filter(
        kullanici=request.user
    ).select_related('urun').order_by('-tarih')

    context = {
        'envanter': envanter,
        'satin_almalar': satin_almalar,
        'profil': request.user.profil,
    }
    return render(request, 'magaza/envanter.html', context)


@login_required
@transaction.atomic
def urun_aktif_et(request, urun_id):
    """Satın alınan ürünü aktif et"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'POST gerekli'}, status=400)

    urun = get_object_or_404(MagazaUrun, id=urun_id)
    envanter = envanter_getir_veya_olustur(request.user)

    # Sahip mi kontrol et
    if not SatinAlma.objects.filter(kullanici=request.user, urun=urun).exists():
        return JsonResponse({'success': False, 'message': 'Bu ürüne sahip değilsiniz!'})

    # Kategoriye göre aktif et
    if urun.kategori == 'unvan':
        envanter.aktif_unvan = urun
    elif urun.kategori == 'cerceve':
        envanter.aktif_cerceve = urun
    elif urun.kategori == 'tema':
        envanter.aktif_tema = urun

    envanter.save()

    logger.info(f"Ürün aktif edildi: {request.user.username} - {urun.isim}")

    return JsonResponse({
        'success': True,
        'message': f'✅ {urun.isim} aktif edildi!',
    })


@login_required
@transaction.atomic
def urun_kaldir(request, urun_id):
    """Aktif ürünü kaldır"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'POST gerekli'}, status=400)

    urun = get_object_or_404(MagazaUrun, id=urun_id)
    envanter = envanter_getir_veya_olustur(request.user)

    if urun.kategori == 'unvan' and envanter.aktif_unvan == urun:
        envanter.aktif_unvan = None
    elif urun.kategori == 'cerceve' and envanter.aktif_cerceve == urun:
        envanter.aktif_cerceve = None
    elif urun.kategori == 'tema' and envanter.aktif_tema == urun:
        envanter.aktif_tema = None

    envanter.save()

    return JsonResponse({'success': True, 'message': f'✅ {urun.isim} kaldırıldı!'})