# utils/rewards.py

from profile.models import OgrenciProfili 

def unvan_kontrol(profil, kazanilan_puan):
    """
    Kullanıcının skoruna göre unvan (rozet) kazanıp kazanmadığını kontrol eder.
    """
    guncel_unvanlar = profil.unvanlar.split(',')
    yeni_unvan = None
    
    # Rozet Koşulları
    if profil.toplam_puan + kazanilan_puan >= 500 and "Uzman Köstebek" not in guncel_unvanlar:
        yeni_unvan = "Uzman Köstebek"
    elif profil.toplam_puan + kazanilan_puan >= 200 and "Deneyimli Köstebek" not in guncel_unvanlar:
        yeni_unvan = "Deneyimli Köstebek"
    elif profil.toplam_puan + kazanilan_puan >= 50 and "Acemi Köstebek" not in guncel_unvanlar:
        yeni_unvan = "Acemi Köstebek"
        
    if yeni_unvan:
        if profil.unvanlar == "Yeni Köstebek":
            profil.unvanlar = yeni_unvan
        else:
            profil.unvanlar += f",{yeni_unvan}"