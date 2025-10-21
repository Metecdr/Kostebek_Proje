from quiz.models import Rozet, KullaniciRozet  # ✅ İkisi de import

def unvan_kontrol(profil, kazanilan_puan):
    """Kullanıcının puanına göre ünvan kontrolü yapar"""
    guncel_unvanlar = profil.unvanlar.split(',') if profil.unvanlar else []
    yeni_unvan = None
    
    toplam = profil.toplam_puan + kazanilan_puan
    
    if toplam >= 500 and "Uzman Köstebek" not in guncel_unvanlar:
        yeni_unvan = "Uzman Köstebek"
    elif toplam >= 200 and "Deneyimli Köstebek" not in guncel_unvanlar:
        yeni_unvan = "Deneyimli Köstebek"
    elif toplam >= 50 and "Acemi Köstebek" not in guncel_unvanlar:
        yeni_unvan = "Acemi Köstebek"
    
    if yeni_unvan:
        if profil.unvanlar == "Yeni Köstebek" or not profil.unvanlar:
            profil.unvanlar = yeni_unvan
        else:
            profil.unvanlar += f",{yeni_unvan}"
        profil.save()
        return yeni_unvan
    
    return None


def rozet_kontrol(kullanici):
    """
    Kullanıcının rozet kazanıp kazanmadığını kontrol eder
    Rozet tablosundaki kurallara göre dinamik kontrol
    """
    profil = kullanici.profil
    yeni_rozetler = []
    
    # Tüm rozetleri getir
    tum_rozetler = Rozet.objects.all()
    
    for rozet in tum_rozetler:
        # Daha önce kazanılmış mı?
        kazanilmis_mi = KullaniciRozet.objects.filter(
            kullanici=kullanici,
            rozet=rozet
        ).exists()
        
        if kazanilmis_mi:
            continue
        
        # Koşul kontrolü
        kosul_saglandi = False
        
        if rozet.kosul_turu == 'soru_sayisi':
            kosul_saglandi = profil.cozulen_soru_sayisi >= rozet.kosul_degeri
        
        elif rozet.kosul_turu == 'toplam_puan':
            kosul_saglandi = profil.toplam_puan >= rozet.kosul_degeri
        
        elif rozet.kosul_turu == 'dogru_sayisi':
            kosul_saglandi = profil.toplam_dogru >= rozet.kosul_degeri
        
        elif rozet.kosul_turu == 'basari_orani':
            if profil.cozulen_soru_sayisi >= 20:  # En az 20 soru çözülmüş olmalı
                kosul_saglandi = profil.basari_orani() >= rozet.kosul_degeri
        
        # Koşul sağlandıysa rozeti ver
        if kosul_saglandi:
            KullaniciRozet.objects.create(
                kullanici=kullanici,
                rozet=rozet
            )
            yeni_rozetler.append(rozet)
    
    return yeni_rozetler