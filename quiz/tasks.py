from background_task import background
from django.core.management import call_command

# schedule=604800 saniyede bir (7 gün) çalışacak şekilde ayarla
@background(schedule=604800)
def haftalik_sifirlama_gorevi():
    print("Haftalık puan sıfırlama görevi başlatılıyor...")
    try:
        call_command('sifirla_haftalik_puan')
        print("Haftalık puanlar başarıyla sıfırlandı.")
    except Exception as e:
        print(f"Hata oluştu: {e}")