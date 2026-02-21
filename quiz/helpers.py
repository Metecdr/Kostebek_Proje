import random
import logging
import math
from django.core.cache import cache
from django.db import IntegrityError, models
from django.core.exceptions import ValidationError
from django.utils import timezone
from quiz.models import Soru
from profile.models import OyunModuIstatistik

logger = logging.getLogger(__name__)


def get_random_soru_by_ders(ders='karisik'):
    """Seçilen derse göre rastgele soru getir"""
    logger.debug(f"Soru aranıyor: Ders={ders}")
    cache_key = f'karsilasma_soru_ids_{ders}'
    soru_ids = cache.get(cache_key)
    
    if soru_ids is None:
        if ders == 'karisik':
            soru_ids = list(Soru.objects.filter(karsilasmada_cikar=True).values_list('id', flat=True))
        else:
            soru_ids = list(Soru.objects.filter(ders=ders, karsilasmada_cikar=True).values_list('id', flat=True))
        cache.set(cache_key, soru_ids, 300)
        logger.debug(f"Soru ID'leri cache'lendi: Ders={ders}, Sayı={len(soru_ids)}")
    
    if soru_ids:
        random_id = random.choice(soru_ids)
        soru = Soru.objects.get(id=random_id)
        logger.debug(f"Soru seçildi: ID={random_id}, Ders={ders}")
        return soru
    
    logger.warning(f"Hiç soru bulunamadı: Ders={ders}")
    return None


def update_stats_with_combo(user, oda, cevap_obj, is_oyuncu1):
    """Combo ve hız bonusu ile istatistik güncelle"""
    try:
        profil = user.profil
        base_puan = 10
        bonus_puan = 0
        
        if is_oyuncu1 and oda.oyuncu1_cevap_zamani and oda.soru_baslangic_zamani:
            sure = (oda.oyuncu1_cevap_zamani - oda.soru_baslangic_zamani).total_seconds()
            if sure < 5:
                bonus_puan += 5
                logger.debug(f"Hız bonusu: Kullanıcı={user.username}, Süre={sure:.1f}s")
        elif not is_oyuncu1 and oda.oyuncu2_cevap_zamani and oda.soru_baslangic_zamani:
            sure = (oda.oyuncu2_cevap_zamani - oda.soru_baslangic_zamani).total_seconds()
            if sure < 5:
                bonus_puan += 5
                logger.debug(f"Hız bonusu: Kullanıcı={user.username}, Süre={sure:.1f}s")
        
        if cevap_obj.dogru_mu:
            if is_oyuncu1:
                oda.oyuncu1_combo += 1
                combo = oda.oyuncu1_combo
                oda.oyuncu1_dogru += 1
            else:
                oda.oyuncu2_combo += 1
                combo = oda.oyuncu2_combo
                oda.oyuncu2_dogru += 1
            
            combo_bonus = min(combo * 2, 20)
            bonus_puan += combo_bonus
            logger.debug(f"Combo bonusu: Kullanıcı={user.username}, Combo={combo}, Bonus={combo_bonus}")
            
            if oda.ilk_dogru_cevaplayan is None:
                oda.ilk_dogru_cevaplayan = user
                bonus_puan += 3
                logger.debug(f"İlk doğru bonusu: Kullanıcı={user.username}")
            
            toplam_puan = base_puan + bonus_puan
            
            if is_oyuncu1:
                oda.oyuncu1_skor += toplam_puan
            else:
                oda.oyuncu2_skor += toplam_puan
            
            profil.toplam_dogru += 1
            profil.haftalik_dogru += 1
            profil.cozulen_soru_sayisi += 1
            profil.haftalik_cozulen += 1
            profil.toplam_puan += toplam_puan
            profil.haftalik_puan += toplam_puan
            profil.save()
            
            oyun_ist, created = OyunModuIstatistik.objects.get_or_create(profil=profil, oyun_modu='karsilasma')
            oyun_ist.cozulen_soru += 1
            oyun_ist.dogru_sayisi += 1
            oyun_ist.toplam_puan += toplam_puan
            oyun_ist.save()
            
            logger.info(f"İstatistik güncellendi: Kullanıcı={user.username}, Puan={toplam_puan}, Doğru=True")
        else:
            if is_oyuncu1:
                oda.oyuncu1_combo = 0
                oda.oyuncu1_yanlis += 1
            else:
                oda.oyuncu2_combo = 0
                oda.oyuncu2_yanlis += 1
            
            logger.debug(f"Yanlış cevap: Kullanıcı={user.username}, Combo sıfırlandı")
            
            profil.toplam_yanlis += 1
            profil.haftalik_yanlis += 1
            profil.cozulen_soru_sayisi += 1
            profil.haftalik_cozulen += 1
            profil.save()
            
            oyun_ist, created = OyunModuIstatistik.objects.get_or_create(profil=profil, oyun_modu='karsilasma')
            oyun_ist.cozulen_soru += 1
            oyun_ist.yanlis_sayisi += 1
            oyun_ist.save()
        
        cache_key = f'karsilasma_ist_{profil.id}'
        cache.delete(cache_key)
    
    except AttributeError as e:
        logger.error(f"Profil erişim hatası: Kullanıcı={user.username}, Hata={e}", exc_info=True)
    except IntegrityError as e:
        logger.error(f"Veritabanı bütünlük hatası: Kullanıcı={user.username}, Hata={e}", exc_info=True)
    except ValidationError as e:
        logger.error(f"Validasyon hatası: Kullanıcı={user.username}, Hata={e}", exc_info=True)
    except Exception as e:
        logger.error(f"İstatistik güncelleme beklenmeyen hata: Kullanıcı={user.username}, Hata={e}", exc_info=True)


# ==================== 🏆 TURNUVA FONKSİYONLARI ====================

def sonraki_round_olustur(turnuva, onceki_round):
    """
    Önceki round'dan kazananları alarak sonraki round'u oluştur
    """
    from .models import TurnuvaMaci
    
    # Önceki round'un kazananlarını al
    onceki_maclar = TurnuvaMaci.objects.filter(
        turnuva=turnuva,
        round=onceki_round,
        tamamlandi=True
    ).order_by('olusturma_tarihi')
    
    kazananlar = [mac.kazanan for mac in onceki_maclar if mac.kazanan]
    
    if len(kazananlar) < 2:
        logger.warning(f"Yetersiz kazanan: {len(kazananlar)}")
        return False
    
    # Yeni round numarası
    yeni_round = onceki_round + 1
    
    # Maçları oluştur
    for i in range(0, len(kazananlar), 2):
        if i + 1 < len(kazananlar):
            oyuncu1 = kazananlar[i]
            oyuncu2 = kazananlar[i + 1]
            
            TurnuvaMaci.objects.create(
                turnuva=turnuva,
                round=yeni_round,
                oyuncu1=oyuncu1,
                oyuncu2=oyuncu2,
                tamamlandi=False
            )
            logger.info(f"Yeni maç: {oyuncu1.username} vs {oyuncu2.username} (Round {yeni_round})")
        else:
            # Tek kalan oyuncu (BYE)
            TurnuvaMaci.objects.create(
                turnuva=turnuva,
                round=yeni_round,
                oyuncu1=kazananlar[i],
                oyuncu2=None,
                kazanan=kazananlar[i],
                tamamlandi=True
            )
            logger.info(f"BYE: {kazananlar[i].username} (Round {yeni_round})")
    
    return True


def turnuva_mac_bitir(mac, kazanan):
    """
    Turnuva maçını bitir ve gerekirse sonraki round'u oluştur
    """
    from django.utils import timezone
    from quiz.models import TurnuvaMaci
    import logging
    
    logger = logging.getLogger(__name__)
    
    # Maçı güncelle
    mac.kazanan = kazanan
    mac.tamamlandi = True
    mac.save()
    
    logger.info(f"✅ Maç bitti: {mac.oyuncu1.username} vs {mac.oyuncu2.username} → Kazanan: {kazanan.username}")
    
    # Bu round'daki tüm maçlar bitti mi?
    turnuva = mac.turnuva
    round_no = mac.round
    
    round_maclari = TurnuvaMaci.objects.filter(turnuva=turnuva, round=round_no)
    tamamlanan_maclar = round_maclari.filter(tamamlandi=True).count()
    toplam_maclar = round_maclari.count()
    
    logger.info(f"📊 Round {round_no}: {tamamlanan_maclar}/{toplam_maclar} maç tamamlandı")
    
    # Tüm maçlar bitti mi?
    if tamamlanan_maclar == toplam_maclar:
        logger.info(f"✅ Round {round_no} tamamlandı!")
        
        # Kazananları al
        kazananlar = list(round_maclari.filter(kazanan__isnull=False).values_list('kazanan', flat=True))
        
        logger.info(f"👑 Kazananlar ({len(kazananlar)}): {kazananlar}")
        
        # Tek kişi kaldıysa turnuva bitti
        if len(kazananlar) <= 1:
            turnuva.durum = 'bitti'
            
            if len(kazananlar) == 1:
                from django.contrib.auth.models import User
                birinci = User.objects.get(id=kazananlar[0])
                turnuva.birinci = birinci
                
                # ✅ 2. ve 3.lüğü bul
                final_mac = round_maclari.first()
                
                # 2.lik (finalin kaybedeni)
                ikinci = final_mac.oyuncu1 if final_mac.oyuncu2 == birinci else final_mac.oyuncu2
                turnuva.ikinci = ikinci
                
                # ✅ 3.lük (yarı finalin kaybedenlerinden biri - skorlarına göre)
                if round_no > 1:
                    yarimfinal_round = round_no - 1
                    yarimfinal_maclari = TurnuvaMaci.objects.filter(
                        turnuva=turnuva,
                        round=yarimfinal_round,
                        tamamlandi=True
                    )
                    
                    # Yarı final kaybedenleri
                    kaybedenler = []
                    for yarimfinal_mac in yarimfinal_maclari:
                        kaybeden = yarimfinal_mac.oyuncu1 if yarimfinal_mac.kazanan == yarimfinal_mac.oyuncu2 else yarimfinal_mac.oyuncu2
                        
                        # ikinci değilse ekle
                        if kaybeden != ikinci:
                            kaybeden_skor = yarimfinal_mac.oyuncu1_skor if kaybeden == yarimfinal_mac.oyuncu1 else yarimfinal_mac.oyuncu2_skor
                            kaybedenler.append((kaybeden, kaybeden_skor))
                    
                    # En yüksek skora sahip kaybeden 3. olur
                    if kaybedenler:
                        kaybedenler.sort(key=lambda x: x[1], reverse=True)
                        ucuncu = kaybedenler[0][0]
                        turnuva.ucuncu = ucuncu
                        logger.info(f"🥉 3.lük: {ucuncu.username}")
                
                logger.info(f"🏆 TURNUVA BİTTİ!")
                logger.info(f"🥇 1.lik: {birinci.username}")
                logger.info(f"🥈 2.lik: {ikinci.username if ikinci else 'Yok'}")
                logger.info(f"🥉 3.lük: {turnuva.ucuncu.username if turnuva.ucuncu else 'Yok'}")
            
            turnuva.bitis = timezone.now()
            turnuva.save()
            
            # ✅ ÖDÜL XP'LERİNİ VER
            if turnuva.birinci:
                profile = turnuva.birinci.kullanici_profili
                profile.xp += turnuva.odul_xp_1
                profile.save()
                logger.info(f"💰 {turnuva.birinci.username} +{turnuva.odul_xp_1} XP kazandı!")
            
            if turnuva.ikinci:
                profile = turnuva.ikinci.kullanici_profili
                profile.xp += turnuva.odul_xp_2
                profile.save()
                logger.info(f"💰 {turnuva.ikinci.username} +{turnuva.odul_xp_2} XP kazandı!")
            
            if turnuva.ucuncu:
                profile = turnuva.ucuncu.kullanici_profili
                profile.xp += turnuva.odul_xp_3
                profile.save()
                logger.info(f"💰 {turnuva.ucuncu.username} +{turnuva.odul_xp_3} XP kazandı!")
            
            return True  # Turnuva bitti
        
        else:
            # Sonraki round'u oluştur
            yeni_round = round_no + 1
            logger.info(f"🎮 Round {yeni_round} oluşturuluyor...")
            
            # Kazananları eşleştir
            from django.contrib.auth.models import User
            kazanan_kullanicilar = User.objects.filter(id__in=kazananlar)
            
            for i in range(0, len(kazanan_kullanicilar), 2):
                if i + 1 < len(kazanan_kullanicilar):
                    oyuncu1 = kazanan_kullanicilar[i]
                    oyuncu2 = kazanan_kullanicilar[i + 1]
                    
                    yeni_mac = TurnuvaMaci.objects.create(
                        turnuva=turnuva,
                        round=yeni_round,
                        oyuncu1=oyuncu1,
                        oyuncu2=oyuncu2,
                        tamamlandi=False
                    )
                    
                    logger.info(f"  ✅ Round {yeni_round} maç: {oyuncu1.username} vs {oyuncu2.username}")
                else:
                    # Tek kalan (BYE)
                    oyuncu1 = kazanan_kullanicilar[i]
                    yeni_mac = TurnuvaMaci.objects.create(
                        turnuva=turnuva,
                        round=yeni_round,
                        oyuncu1=oyuncu1,
                        oyuncu2=None,
                        kazanan=oyuncu1,
                        tamamlandi=True
                    )
                    logger.info(f"  ✅ Round {yeni_round} BYE: {oyuncu1.username}")
            
            # Turnuva durumunu güncelle
            turnuva.durum = 'devam_ediyor'
            turnuva.save()
            
            logger.info(f"✅ Round {yeni_round} oluşturuldu!")
            
            # ✅ YENİ ROUND MAÇLARINI OTOMATİK HAZIRLA
            from quiz.helpers import get_random_soru_by_ders
            from quiz.models import KarsilasmaOdasi
            from datetime import timedelta
            
            # Yeni round'un başlangıç zamanı: 5 dakika sonra
            yeni_baslangic = timezone.now() + timedelta(minutes=5)
            
            yeni_maclar = TurnuvaMaci.objects.filter(turnuva=turnuva, round=yeni_round, tamamlandi=False)
            
            for yeni_mac in yeni_maclar:
                # İlk soruyu al
                ilk_soru = get_random_soru_by_ders(turnuva.ders)
                
                # Karşılaşma odası oluştur
                oda = KarsilasmaOdasi.objects.create(
                    oyuncu1=yeni_mac.oyuncu1,
                    oyuncu2=yeni_mac.oyuncu2,
                    secilen_ders=turnuva.ders,
                    sinav_tipi=turnuva.sinav_tipi.lower(),
                    oyun_durumu='bekleniyor',
                    aktif_soru=ilk_soru,
                    aktif_soru_no=1,
                    toplam_soru=turnuva.toplam_soru,
                )
                
                yeni_mac.karsilasma_oda = oda
                yeni_mac.mac_baslangic_zamani = yeni_baslangic
                yeni_mac.oyuncu1_hazir = False
                yeni_mac.oyuncu2_hazir = False
                yeni_mac.save()
                
                logger.info(f"  🎮 Oda hazırlandı: {yeni_mac.oyuncu1.username} vs {yeni_mac.oyuncu2.username}")
            
            logger.info(f"⏰ Round {yeni_round} maçları {yeni_baslangic.strftime('%H:%M')} saatinde başlayacak!")
    
    return False  # Turnuva devam ediyor


def turnuva_siralama_guncelle(turnuva):
    """
    Turnuva bittiğinde sıralama tablosunu oluştur/güncelle
    """
    from .models import TurnuvaMaci, TurnuvaSiralama
    from django.db.models import Q, Sum, Avg, Max, Count
    
    if turnuva.durum != 'bitti':
        logger.warning(f"Turnuva henüz bitmedi: {turnuva.isim}")
        return
    
    logger.info(f"📊 Sıralama tablosu oluşturuluyor: {turnuva.isim}")
    
    # Tüm katılımcılar için istatistik topla
    for katilimci in turnuva.katilimcilar.all():
        
        # Kullanıcının tüm maçları
        oyuncu1_maclari = TurnuvaMaci.objects.filter(
            turnuva=turnuva,
            oyuncu1=katilimci,
            tamamlandi=True
        )
        
        oyuncu2_maclari = TurnuvaMaci.objects.filter(
            turnuva=turnuva,
            oyuncu2=katilimci,
            tamamlandi=True
        )
        
        # Maç sayıları
        oynanan_mac = oyuncu1_maclari.count() + oyuncu2_maclari.count()
        kazanilan_mac = TurnuvaMaci.objects.filter(
            Q(turnuva=turnuva) & Q(kazanan=katilimci) & Q(tamamlandi=True)
        ).count()
        kaybedilen_mac = oynanan_mac - kazanilan_mac
        
        # Skor istatistikleri
        toplam_skor = 0
        skorlar = []
        
        for mac in oyuncu1_maclari:
            toplam_skor += mac.oyuncu1_skor
            skorlar.append(mac.oyuncu1_skor)
        
        for mac in oyuncu2_maclari:
            toplam_skor += mac.oyuncu2_skor
            skorlar.append(mac.oyuncu2_skor)
        
        ortalama_skor = toplam_skor / oynanan_mac if oynanan_mac > 0 else 0
        en_yuksek_skor = max(skorlar) if skorlar else 0
        
        # Soru istatistikleri (Karşılaşma odalarından)
        from .models import KarsilasmaOdasi
        
        toplam_dogru = 0
        toplam_yanlis = 0
        
        odalar = KarsilasmaOdasi.objects.filter(
            Q(oyuncu1=katilimci) | Q(oyuncu2=katilimci),
            oyun_durumu='bitti'
        )
        
        for oda in odalar:
            if oda.oyuncu1 == katilimci:
                toplam_dogru += oda.oyuncu1_dogru
                toplam_yanlis += oda.oyuncu1_yanlis
            else:
                toplam_dogru += oda.oyuncu2_dogru
                toplam_yanlis += oda.oyuncu2_yanlis
        
        toplam_soru = toplam_dogru + toplam_yanlis
        dogru_yuzdesi = (toplam_dogru / toplam_soru * 100) if toplam_soru > 0 else 0
        
        # Hangi round'da elendi?
        son_mac = TurnuvaMaci.objects.filter(
            Q(turnuva=turnuva) & 
            (Q(oyuncu1=katilimci) | Q(oyuncu2=katilimci)) &
            Q(tamamlandi=True)
        ).order_by('-round').first()
        
        elesme_round = son_mac.round if son_mac else 0
        
        # Sıra belirleme
        if turnuva.birinci == katilimci:
            sira = 1
            kazanilan_xp = turnuva.odul_xp_1
        elif turnuva.ikinci == katilimci:
            sira = 2
            kazanilan_xp = turnuva.odul_xp_2
        elif turnuva.ucuncu == katilimci:
            sira = 3
            kazanilan_xp = turnuva.odul_xp_3
        else:
            # Diğerleri için round'a göre sıralama
            # Aynı round'da elenenleri skorlarına göre sırala
            ayni_roundda_elenenler = []
            
            for diger_katilimci in turnuva.katilimcilar.all():
                if diger_katilimci == katilimci:
                    continue
                
                if diger_katilimci in [turnuva.birinci, turnuva.ikinci, turnuva.ucuncu]:
                    continue
                
                diger_son_mac = TurnuvaMaci.objects.filter(
                    Q(turnuva=turnuva) & 
                    (Q(oyuncu1=diger_katilimci) | Q(oyuncu2=diger_katilimci)) &
                    Q(tamamlandi=True)
                ).order_by('-round').first()
                
                if diger_son_mac and diger_son_mac.round == elesme_round:
                    # Skorunu hesapla
                    diger_toplam_skor = 0
                    diger_oyuncu1 = TurnuvaMaci.objects.filter(turnuva=turnuva, oyuncu1=diger_katilimci, tamamlandi=True)
                    diger_oyuncu2 = TurnuvaMaci.objects.filter(turnuva=turnuva, oyuncu2=diger_katilimci, tamamlandi=True)
                    
                    for m in diger_oyuncu1:
                        diger_toplam_skor += m.oyuncu1_skor
                    for m in diger_oyuncu2:
                        diger_toplam_skor += m.oyuncu2_skor
                    
                    ayni_roundda_elenenler.append({
                        'kullanici': diger_katilimci,
                        'skor': diger_toplam_skor
                    })
            
            # Kendini de ekle
            ayni_roundda_elenenler.append({
                'kullanici': katilimci,
                'skor': toplam_skor
            })
            
            # Skorlara göre sırala
            ayni_roundda_elenenler.sort(key=lambda x: x['skor'], reverse=True)
            
            # Kendi sırasını bul
            for idx, item in enumerate(ayni_roundda_elenenler):
                if item['kullanici'] == katilimci:
                    # 1., 2., 3. zaten var, diğerleri 4'ten başlar
                    sira = 4 + idx
                    break
            else:
                sira = 999  # Fallback
            
            kazanilan_xp = 0
        
        # Sıralama kaydını oluştur/güncelle
        siralama, created = TurnuvaSiralama.objects.update_or_create(
            turnuva=turnuva,
            kullanici=katilimci,
            defaults={
                'sira': sira,
                'elesme_round': elesme_round,
                'oynanan_mac': oynanan_mac,
                'kazanilan_mac': kazanilan_mac,
                'kaybedilen_mac': kaybedilen_mac,
                'toplam_skor': toplam_skor,
                'ortalama_skor': round(ortalama_skor, 2),
                'en_yuksek_skor': en_yuksek_skor,
                'toplam_dogru': toplam_dogru,
                'toplam_yanlis': toplam_yanlis,
                'dogru_yuzdesi': round(dogru_yuzdesi, 2),
                'kazanilan_xp': kazanilan_xp,
            }
        )
        
        logger.info(f"   {sira}. {katilimci.username} - Skor: {toplam_skor}, Doğruluk: {dogru_yuzdesi:.1f}%")
    
    logger.info(f"✅ Sıralama tablosu tamamlandı!")