from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.cache import cache
from profile.models import OyunModuIstatistik
from profile.rozet_kontrol import rozet_kontrol_yap
import logging

logger = logging.getLogger(__name__)


@login_required
def quiz_anasayfa(request):
    """Ana sayfa - Oyun modları + Motivasyon widget'ları"""
    try:
        profil = request.user.profil

        # Oyun istatistikleri
        oyun_istatistikleri = OyunModuIstatistik.objects.filter(profil=profil)
        karsilasma_ist = oyun_istatistikleri.filter(oyun_modu='karsilasma').first()
        tabu_ist       = oyun_istatistikleri.filter(oyun_modu='tabu').first()
        bulbakalim_ist = oyun_istatistikleri.filter(oyun_modu='bul_bakalim').first()

        # Toplam oynanan oyun
        toplam_oyun = sum([
            (karsilasma_ist.oynanan_oyun_sayisi if karsilasma_ist else 0),
            (tabu_ist.oynanan_oyun_sayisi       if tabu_ist       else 0),
            (bulbakalim_ist.oynanan_oyun_sayisi  if bulbakalim_ist else 0),
        ])

        # Liderlik sırası
        try:
            liderlik_sira = OgrenciProfili.objects.filter(
                toplam_puan__gt=profil.toplam_puan
            ).count() + 1
        except Exception:
            liderlik_sira = 0

        # Günlük görevler
        bugun_tamamlanan = 0
        bugun_toplam = 3
        try:
            from profile.gorev_helper import bugunun_gorevlerini_getir
            gorevler = bugunun_gorevlerini_getir(profil)
            bugun_toplam     = gorevler.count() or 3
            bugun_tamamlanan = gorevler.filter(tamamlandi_mi=True).count()
        except Exception as e:
            logger.error(f"Anasayfa görev hatası: {e}")

        # Başarı oranı
        toplam_soru = profil.toplam_dogru + profil.toplam_yanlis
        basari_orani = round((profil.toplam_dogru / toplam_soru) * 100, 1) if toplam_soru > 0 else 0

        # Envanter (mağaza)
        try:
            from magaza.models import KullaniciEnvanter
            envanter, _ = KullaniciEnvanter.objects.get_or_create(kullanici=request.user)
        except Exception:
            envanter = None

        context = {
            'profil': profil,
            'karsilasma_ist': karsilasma_ist,
            'tabu_ist': tabu_ist,
            'bulbakalim_ist': bulbakalim_ist,
            'toplam_oyun': toplam_oyun,
            'liderlik_sira': liderlik_sira,
            'bugun_tamamlanan': bugun_tamamlanan,
            'bugun_toplam': bugun_toplam,
            'basari_orani': basari_orani,
            'envanter': envanter,
        }

    except AttributeError as e:
        logger.error(f"Anasayfa profil hatası: {e}", exc_info=True)
        from django.shortcuts import redirect
        return redirect('profil')
    except Exception as e:
        logger.error(f"Anasayfa beklenmeyen hata: {e}", exc_info=True)
        context = {}

    return render(request, 'quiz/anasayfa.html', context)