from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta, date
from profile.models import OyunModuIstatistik, OgrenciProfili
from profile.rozet_kontrol import rozet_kontrol_yap
import logging
import hashlib

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

        # Günün sözü - her gün değişir
        gunun_sozleri = [
            {"soz": "Başarı, her gün tekrarlanan küçük çabaların toplamıdır.", "yazar": "Robert Collier"},
            {"soz": "Gelecek, bugünden başlar.", "yazar": "Malcolm X"},
            {"soz": "Eğitim en güçlü silahtır; dünyayı değiştirmek için kullanabilirsiniz.", "yazar": "Nelson Mandela"},
            {"soz": "Hayal gücü bilgiden daha önemlidir.", "yazar": "Albert Einstein"},
            {"soz": "Bir şeyi öğrenmenin en iyi yolu, onu yapmaktır.", "yazar": "Richard Branson"},
            {"soz": "Zor olan doğru olanı yapmak değil, doğru olanın ne olduğunu bilmektir.", "yazar": "Lyndon B. Johnson"},
            {"soz": "Bugün yapabileceğin şeyi yarına bırakma.", "yazar": "Benjamin Franklin"},
            {"soz": "Deha, yüzde bir ilham ve yüzde doksan dokuz terdir.", "yazar": "Thomas Edison"},
            {"soz": "Bilmediğini bilmek, bilginin başlangıcıdır.", "yazar": "Sokrates"},
            {"soz": "İnsanın kendini yenmesi, zaferlerin en büyüğüdür.", "yazar": "Platon"},
            {"soz": "Her büyük yolculuk tek bir adımla başlar.", "yazar": "Lao Tzu"},
            {"soz": "Başarısızlık, başarıya giden yolda sadece bir duraktır.", "yazar": "Denis Waitley"},
            {"soz": "Hayat bisiklete binmek gibidir, dengenizi korumak için hareket etmeye devam etmelisiniz.", "yazar": "Albert Einstein"},
            {"soz": "Okumak, zihni her yöne açan bir anahtardır.", "yazar": "Mustafa Kemal Atatürk"},
            {"soz": "Bir kitap, bin öğretmenin yerine geçer.", "yazar": "Türk Atasözü"},
            {"soz": "Emek olmadan başarı olmaz.", "yazar": "Ralph Waldo Emerson"},
            {"soz": "Azim ve sebat, yeteneğin yerini alabilir.", "yazar": "Calvin Coolidge"},
            {"soz": "En karanlık gece bile güneşin doğuşunu engelleyemez.", "yazar": "Victor Hugo"},
            {"soz": "Kendine inan, yarının seni bugün hayal edemeyeceğin yerlere götürecek.", "yazar": "Anonim"},
            {"soz": "Bugün ek, yarın biç.", "yazar": "Türk Atasözü"},
            {"soz": "Öğrenmek, keşfetmenin başlangıcıdır.", "yazar": "Carl Sagan"},
            {"soz": "İlim ilim bilmektir, ilim kendin bilmektir.", "yazar": "Yunus Emre"},
            {"soz": "Sabır acıdır, meyvesi ise tatlı.", "yazar": "Jean-Jacques Rousseau"},
            {"soz": "Bilgi güçtür.", "yazar": "Francis Bacon"},
            {"soz": "Yapabilirsiniz diye düşünüyorsanız haklısınız; yapamam diye düşünüyorsanız yine haklısınız.", "yazar": "Henry Ford"},
            {"soz": "Hayatta en hakiki mürşit ilimdir.", "yazar": "Mustafa Kemal Atatürk"},
            {"soz": "Düşmekten korkma, kalkmamaktan kork.", "yazar": "Türk Atasözü"},
            {"soz": "Başarı, cesaretle başlar.", "yazar": "Goethe"},
            {"soz": "Güçlü olan haklı değildir, haklı olan güçlüdür.", "yazar": "Mustafa Kemal Atatürk"},
            {"soz": "Dün geçti, yarın henüz gelmedi. Sadece bugün var, hadi başlayalım.", "yazar": "Mother Teresa"},
        ]
        # Her gün aynı sözü göster (güne göre deterministik seçim)
        bugun_str = timezone.now().strftime('%Y-%m-%d')
        soz_index = int(hashlib.md5(bugun_str.encode()).hexdigest(), 16) % len(gunun_sozleri)
        gunun_sozu = gunun_sozleri[soz_index]

        # Duyurular — Duyuru modelinden çek
        duyurular = []
        try:
            from profile.models import Duyuru
            duyurular = [d for d in Duyuru.objects.filter(aktif=True).order_by('-olusturma_tarihi')[:4] if d.aktif_mi]
        except Exception:
            pass
        # Varsayılan duyurular (model yoksa veya boşsa)
        if not duyurular:
            duyurular = [
                {'baslik': '🎉 Köstebek YKS\'ye Hoş Geldin!', 'mesaj': 'Eğlenerek öğrenmeye hazır mısın? Hadi başlayalım!', 'renk_css': 'linear-gradient(135deg,rgba(102,126,234,0.18),rgba(118,75,162,0.1))', 'sinir_rengi': '#667eea', 'icon': '🎉'},
                {'baslik': '💡 Bul Bakalım Modu', 'mesaj': '5 soru, 90 saniye! Yeni oyun modunu dene ve puan kazan.', 'renk_css': 'linear-gradient(135deg,rgba(16,185,129,0.18),rgba(5,150,105,0.1))', 'sinir_rengi': '#10b981', 'icon': '💡'},
                {'baslik': '🏆 Turnuva Sistemi', 'mesaj': 'Resmi turnuvalara katılarak ödül kazan ve şampiyonluk için yarış!', 'renk_css': 'linear-gradient(135deg,rgba(245,158,11,0.18),rgba(217,119,6,0.1))', 'sinir_rengi': '#f59e0b', 'icon': '🏆'},
            ]

        # ── Widget A: Bu Hafta Performans ──
        haftalik_basari = round(
            profil.haftalik_dogru / max(profil.haftalik_cozulen, 1) * 100
        )
        son_7_gun = []
        try:
            from quiz.models import KullaniciCevap
            bugun = timezone.now().date()
            gun_kisa_tr = ['Pzt', 'Sal', 'Çar', 'Per', 'Cum', 'Cmt', 'Paz']
            max_sayi = 0
            for i in range(6, -1, -1):
                gun = bugun - timedelta(days=i)
                sayi = KullaniciCevap.objects.filter(
                    kullanici=request.user, tarih__date=gun
                ).count()
                if sayi > max_sayi:
                    max_sayi = sayi
                son_7_gun.append({
                    'gun': gun_kisa_tr[gun.weekday()],
                    'sayi': sayi,
                    'bugun': (i == 0),
                })
            # Yüzde hesapla (bar chart için)
            for g in son_7_gun:
                g['yuzde'] = round(g['sayi'] / max(max_sayi, 1) * 100)
        except Exception as e:
            logger.error(f"Son 7 gün hesaplama hatası: {e}")
            son_7_gun = []

        # ── Widget B: Motivasyon + Günlük Hedef ──
        streak = profil.ardasik_gun_sayisi or 0
        GUNLUK_HEDEF_SORU = 10  # sabit hedef
        gunluk_ilerleme = min(profil.gunluk_cozulen, GUNLUK_HEDEF_SORU)
        gunluk_hedef_yuzde = round(gunluk_ilerleme / GUNLUK_HEDEF_SORU * 100)
        gunluk_hedef_tamamlandi = gunluk_ilerleme >= GUNLUK_HEDEF_SORU

        if streak == 0:
            motivasyon_mesaji = "Bugün ilk soruyu çözerek seriye başla! 🌱"
        elif streak == 1:
            motivasyon_mesaji = "Harika başlangıç! Yarın devam et 🔥"
        elif streak < 5:
            motivasyon_mesaji = f"{streak} günlük seri! Momentum kazanıyorsun 💪"
        elif streak < 10:
            motivasyon_mesaji = f"{streak} günlük seri! Alışkanlık oluşuyor 🔥"
        elif streak < 30:
            motivasyon_mesaji = f"{streak} günlük seri! Harika bir istikrar 🏆"
        else:
            motivasyon_mesaji = f"{streak} gün üst üste! Efsanesin 👑"

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
            'gunun_sozu': gunun_sozu,
            'duyurular': duyurular,
            # Widget A
            'son_7_gun': son_7_gun,
            'haftalik_basari': haftalik_basari,
            # Widget B
            'streak': streak,
            'motivasyon_mesaji': motivasyon_mesaji,
            'gunluk_ilerleme': gunluk_ilerleme,
            'gunluk_hedef_yuzde': gunluk_hedef_yuzde,
            'gunluk_hedef_tamamlandi': gunluk_hedef_tamamlandi,
            'GUNLUK_HEDEF_SORU': GUNLUK_HEDEF_SORU,
        }

    except AttributeError as e:
        logger.error(f"Anasayfa profil hatası: {e}", exc_info=True)
        from django.shortcuts import redirect
        return redirect('profil')
    except Exception as e:
        logger.error(f"Anasayfa beklenmeyen hata: {e}", exc_info=True)
        context = {}

    return render(request, 'quiz/anasayfa.html', context)