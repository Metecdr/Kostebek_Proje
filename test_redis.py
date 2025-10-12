# test_redis.py
import redis

try:
    # Windows'tan, Linux'un içindeki Redis'e bağlanmayı dene
    r = redis.Redis(host='localhost', port=6379, db=0)

    # Ping komutu gönder
    response = r.ping()

    if response:
        print("\n>>> BAŞARILI: Windows, Redis'e sorunsuz bir şekilde bağlandı! Sorun başka yerde.")
    else:
        print("\n>>> BAŞARISIZ: Bağlantı kuruldu ama cevap alınamadı.")

except redis.exceptions.ConnectionError as e:
    print(f"\n>>> BAŞARISIZ: Windows, Redis'e bağlanamadı! ANA SORUN BU! Hata: {e}")

except Exception as e:
    print(f"\n>>> BAŞARISIZ: Beklenmedik bir hata oluştu: {e}")