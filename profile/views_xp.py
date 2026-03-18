from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from profile.models import XPGecmisi
import logging

logger = logging.getLogger(__name__)


@login_required
def xp_gecmisi_view(request):
    """XP Geçmişi Sayfası"""
    try:
        profil = request.user.profil
        
        # Son 50 XP kaydı
        xp_kayitlari = XPGecmisi.objects.filter(
            profil=profil
        ).order_by('-tarih')[:50]
        
        # Toplam istatistikler
        from django.db.models import Sum, Count
        istatistik = XPGecmisi.objects.filter(profil=profil).aggregate(
            toplam_xp=Sum('miktar'),
            toplam_kayit=Count('id')
        )
        
        # Sebep bazlı gruplandırma (en çok XP nereden geliyor)
        from django.db.models import Sum
        sebep_dagilimi = XPGecmisi.objects.filter(
            profil=profil
        ).values('sebep').annotate(
            toplam=Sum('miktar')
        ).order_by('-toplam')[:5]
        
        # Bugün kazanılan XP
        from django.utils import timezone
        bugun = timezone.now().date()
        bugun_xp = XPGecmisi.objects.filter(
            profil=profil,
            tarih__date=bugun
        ).aggregate(toplam=Sum('miktar'))['toplam'] or 0
        
        # Bu hafta kazanılan XP
        from datetime import timedelta
        hafta_basi = bugun - timedelta(days=bugun.weekday())
        hafta_xp = XPGecmisi.objects.filter(
            profil=profil,
            tarih__date__gte=hafta_basi
        ).aggregate(toplam=Sum('miktar'))['toplam'] or 0

        context = {
            'profil': profil,
            'xp_kayitlari': xp_kayitlari,
            'toplam_xp': istatistik['toplam_xp'] or 0,
            'toplam_kayit': istatistik['toplam_kayit'] or 0,
            'sebep_dagilimi': sebep_dagilimi,
            'bugun_xp': bugun_xp,
            'hafta_xp': hafta_xp,
        }
        
        return render(request, 'xp_gecmisi.html', context)
    
    except Exception as e:
        logger.error(f"XP geçmişi hatası: {e}", exc_info=True)
        context = {
            'profil': request.user.profil,
            'xp_kayitlari': [],
            'toplam_xp': 0,
            'toplam_kayit': 0,
            'sebep_dagilimi': [],
            'bugun_xp': 0,
            'hafta_xp': 0,
        }
        return render(request, 'xp_gecmisi.html', context)


@login_required
def haftalik_rapor_view(request):
    """Haftalık Rapor Sayfası"""
    try:
        from django.utils import timezone
        from datetime import timedelta
        from django.db.models import Sum, Count, Max
        from profile.models import CalismaKaydi, DersIstatistik

        profil = request.user.profil
        bugun = timezone.now().date()
        hafta_basi = bugun - timedelta(days=bugun.weekday())
        hafta_sonu = hafta_basi + timedelta(days=6)

        # Bu haftanın günlük kayıtları
        haftalik_kayitlar = CalismaKaydi.objects.filter(
            profil=profil,
            tarih__range=[hafta_basi, hafta_sonu]
        ).order_by('tarih')

        # Günlere göre veri (Pazartesi-Pazar)
        gunler = []
        gun_isimleri = ['Pzt', 'Sal', 'Çar', 'Per', 'Cum', 'Cmt', 'Paz']
        for i in range(7):
            gun = hafta_basi + timedelta(days=i)
            kayit = haftalik_kayitlar.filter(tarih=gun).first()
            gunler.append({
                'isim': gun_isimleri[i],
                'tarih': gun,
                'soru': kayit.cozulen_soru if kayit else 0,
                'dogru': kayit.dogru_sayisi if kayit else 0,
                'yanlis': kayit.yanlis_sayisi if kayit else 0,
                'xp': kayit.kazanilan_xp if kayit else 0,
                'bugun': gun == bugun,
            })

        # Haftalık toplamlar
        hafta_toplam = haftalik_kayitlar.aggregate(
            toplam_soru=Sum('cozulen_soru'),
            toplam_dogru=Sum('dogru_sayisi'),
            toplam_yanlis=Sum('yanlis_sayisi'),
            toplam_xp=Sum('kazanilan_xp'),
            toplam_oyun=Sum('oynanan_oyun'),
        )

        toplam_soru  = hafta_toplam['toplam_soru']  or 0
        toplam_dogru = hafta_toplam['toplam_dogru'] or 0
        toplam_yanlis= hafta_toplam['toplam_yanlis']or 0
        toplam_xp    = hafta_toplam['toplam_xp']    or 0
        toplam_oyun  = hafta_toplam['toplam_oyun']  or 0

        basari_orani = round((toplam_dogru / toplam_soru * 100), 1) if toplam_soru > 0 else 0

        # En çok çalışılan ders (bu hafta)
        en_cok_ders = DersIstatistik.objects.filter(
            profil=profil
        ).order_by('-haftalik_cozulen').first()

        # Geçen hafta ile karşılaştırma
        gecen_hafta_basi = hafta_basi - timedelta(days=7)
        gecen_hafta_sonu = hafta_basi - timedelta(days=1)
        gecen_hafta = CalismaKaydi.objects.filter(
            profil=profil,
            tarih__range=[gecen_hafta_basi, gecen_hafta_sonu]
        ).aggregate(
            toplam_soru=Sum('cozulen_soru'),
            toplam_xp=Sum('kazanilan_xp'),
        )
        gecen_hafta_soru = gecen_hafta['toplam_soru'] or 0
        gecen_hafta_xp   = gecen_hafta['toplam_xp']   or 0

        # Karşılaştırma yüzdeleri
        soru_degisim = round(((toplam_soru - gecen_hafta_soru) / gecen_hafta_soru * 100), 1) if gecen_hafta_soru > 0 else 0
        xp_degisim   = round(((toplam_xp   - gecen_hafta_xp)   / gecen_hafta_xp   * 100), 1) if gecen_hafta_xp   > 0 else 0

        # Aktif gün sayısı
        aktif_gun = haftalik_kayitlar.filter(cozulen_soru__gt=0).count()

        context = {
            'profil': profil,
            'gunler': gunler,
            'hafta_basi': hafta_basi,
            'hafta_sonu': hafta_sonu,
            'toplam_soru': toplam_soru,
            'toplam_dogru': toplam_dogru,
            'toplam_yanlis': toplam_yanlis,
            'toplam_xp': toplam_xp,
            'toplam_oyun': toplam_oyun,
            'basari_orani': basari_orani,
            'en_cok_ders': en_cok_ders,
            'gecen_hafta_soru': gecen_hafta_soru,
            'gecen_hafta_xp': gecen_hafta_xp,
            'soru_degisim': soru_degisim,
            'xp_degisim': xp_degisim,
            'aktif_gun': aktif_gun,
        }

        return render(request, 'haftalik_rapor.html', context)

    except Exception as e:
        logger.error(f"Haftalık rapor hatası: {e}", exc_info=True)
        return render(request, 'haftalik_rapor.html', {'profil': request.user.profil})