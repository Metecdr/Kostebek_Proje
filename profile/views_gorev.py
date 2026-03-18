from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.contrib import messages
from profile.models import KullaniciGunlukGorev, CalismaKaydi, OgrenciProfili
import logging

logger = logging.getLogger(__name__)


def _bugunun_gorevlerini_getir(profil):
    """Bugünün görevlerini getir, yoksa ata"""
    bugun = timezone.now().date()
    gorevler = KullaniciGunlukGorev.objects.filter(
        profil=profil,
        tarih=bugun
    ).select_related('sablon')

    if not gorevler.exists():
        try:
            from profile.gorev_helper import bugunun_gorevlerini_getir
            gorevler = bugunun_gorevlerini_getir(profil)
        except Exception as e:
            logger.error(f"Görev atama hatası: {e}", exc_info=True)

    return gorevler


@login_required
def gunluk_gorevler_view(request):
    """Günlük görevler sayfası"""
    try:
        profil = request.user.profil
    except AttributeError:
        messages.error(request, 'Profil bulunamadı!')
        return redirect('profil')

    bugun = timezone.now().date()

    # Bugünkü görevleri getir
    try:
        gorevler = _bugunun_gorevlerini_getir(profil)
        tamamlanan_sayi = gorevler.filter(tamamlandi_mi=True).count()
        toplam_sayi = gorevler.count()
        toplam_xp = sum(g.sablon.odul_xp for g in gorevler if g.tamamlandi_mi)
    except Exception as e:
        logger.error(f"Günlük görev view hatası: {e}", exc_info=True)
        gorevler = []
        tamamlanan_sayi = 0
        toplam_sayi = 0
        toplam_xp = 0

    # Son 7 günün görev tamamlama oranı
    son_7_gun_gorev = []
    GUN_MAP = ['Pzt', 'Sal', 'Çar', 'Per', 'Cum', 'Cmt', 'Paz']
    for i in range(6, -1, -1):
        tarih = bugun - timezone.timedelta(days=i)
        try:
            gun_gorevler = KullaniciGunlukGorev.objects.filter(
                profil=profil,
                tarih=tarih
            )
            toplam = gun_gorevler.count()
            tamamlanan = gun_gorevler.filter(tamamlandi_mi=True).count()
        except Exception:
            toplam = 0
            tamamlanan = 0

        son_7_gun_gorev.append({
            'tarih': tarih.strftime('%d.%m'),
            'gun': GUN_MAP[tarih.weekday()],
            'toplam': toplam,
            'tamamlanan': tamamlanan,
            'oran': int((tamamlanan / toplam * 100)) if toplam > 0 else 0,
            'bugun': tarih == bugun,
        })

    context = {
        'gorevler': gorevler,
        'tamamlanan_sayi': tamamlanan_sayi,
        'toplam_sayi': toplam_sayi,
        'toplam_xp': toplam_xp,
        'son_7_gun_gorev': son_7_gun_gorev,
        'bugun': bugun,
        'profil': profil,
    }

    return render(request, 'gunluk_gorevler.html', context)


@login_required
def calisma_takvimi_view(request):
    """Çalışma takvimi sayfası"""
    try:
        profil = request.user.profil
    except AttributeError:
        messages.error(request, 'Profil bulunamadı!')
        return redirect('profil')

    bugun = timezone.now().date()

    # Son 84 gün verisi
    try:
        from profile.gorev_helper import son_n_gun_calisma
        calisma_verileri = son_n_gun_calisma(profil, gun_sayisi=84)
    except Exception as e:
        logger.error(f"Çalışma verisi hatası: {e}", exc_info=True)
        calisma_verileri = []

    # Bu haftanın istatistikleri
    bu_hafta_baslangic = bugun - timezone.timedelta(days=bugun.weekday())
    bu_ay_baslangic = bugun.replace(day=1)

    try:
        haftalik_veriler = CalismaKaydi.objects.filter(
            profil=profil,
            tarih__gte=bu_hafta_baslangic,
            tarih__lte=bugun
        )
        haftalik_soru = sum(v.cozulen_soru for v in haftalik_veriler)
        haftalik_xp   = sum(v.kazanilan_xp  for v in haftalik_veriler)
    except Exception as e:
        logger.error(f"Haftalık veri hatası: {e}", exc_info=True)
        haftalik_soru = 0
        haftalik_xp   = 0

    # Bu ayın istatistikleri
    try:
        aylik_veriler = CalismaKaydi.objects.filter(
            profil=profil,
            tarih__gte=bu_ay_baslangic,
            tarih__lte=bugun
        )
        aylik_soru = sum(v.cozulen_soru for v in aylik_veriler)
        aylik_xp   = sum(v.kazanilan_xp  for v in aylik_veriler)
    except Exception as e:
        logger.error(f"Aylık veri hatası: {e}", exc_info=True)
        aylik_soru = 0
        aylik_xp   = 0

    # Haftalara böl (takvim grid için)
    haftalar = []
    hafta = []
    for gun in calisma_verileri:
        hafta.append(gun)
        if len(hafta) == 7:
            haftalar.append(hafta)
            hafta = []
    if hafta:
        haftalar.append(hafta)

    context = {
        'profil': profil,
        'calisma_verileri': calisma_verileri,
        'haftalar': haftalar,
        'haftalik_soru': haftalik_soru,
        'haftalik_xp': haftalik_xp,
        'aylik_soru': aylik_soru,
        'aylik_xp': aylik_xp,
        'streak': profil.ardasik_gun_sayisi,
        'en_uzun_streak': profil.en_uzun_streak,
        'toplam_aktif_gun': len([g for g in calisma_verileri if g.get('seviye', 0) > 0]),
    }

    return render(request, 'calisma_takvimi.html', context)


@login_required
def gorev_odul_al(request, gorev_id):
    """Tamamlanan görevin ödülünü al (AJAX)"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST gerekli'}, status=400)

    try:
        profil = request.user.profil
        gorev = KullaniciGunlukGorev.objects.get(
            id=gorev_id,
            profil=profil,
            tamamlandi_mi=True,
            odul_alindi_mi=False
        )

        basarili = gorev.odulu_ver()

        if basarili:
            return JsonResponse({
                'success': True,
                'xp': gorev.sablon.odul_xp,
                'puan': gorev.sablon.odul_puan,
                'mesaj': f'🎉 +{gorev.sablon.odul_xp} XP kazandın!'
            })
        else:
            return JsonResponse({'success': False, 'error': 'Ödül alınamadı'})

    except KullaniciGunlukGorev.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Görev bulunamadı'}, status=404)
    except Exception as e:
        logger.error(f"Ödül alma hatası: {e}", exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)}, status=500)