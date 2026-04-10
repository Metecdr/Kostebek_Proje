from django.core.management.base import BaseCommand
from quiz.models import Soru, Cevap


class Command(BaseCommand):
    help = 'TYT+AYT sorularını toplu ekler (matematik hariç)'

    def handle(self, *args, **options):
        sorular = []

        # ==================== TÜRKÇE (TYT) ====================
        sorular.extend([
            {
                'metin': 'Aşağıdaki cümlelerin hangisinde bir yazım yanlışı vardır?',
                'ders': 'turkce', 'sinav_tipi': 'TYT',
                'detayli_aciklama': '"Herhalde" kelimesi bitişik yazılır.',
                'cevaplar': [
                    ('A) Dün akşam çok güzel bir film izledik.', False),
                    ('B) Her halde bu iş böyle olmayacak.', True),
                    ('C) Sabahleyin erkenden kalktık.', False),
                    ('D) Öğretmenimiz bize ödev verdi.', False),
                ]
            },
            {
                'metin': '"Gözden düşmek" deyiminin anlamı aşağıdakilerden hangisidir?',
                'ders': 'turkce', 'sinav_tipi': 'TYT',
                'detayli_aciklama': 'Gözden düşmek: değerini, itibarını yitirmek anlamına gelir.',
                'cevaplar': [
                    ('A) Değerini, itibarını yitirmek', True),
                    ('B) Çok beğenilmek', False),
                    ('C) Görüşünü kaybetmek', False),
                    ('D) Yüksekten düşmek', False),
                ]
            },
            {
                'metin': 'Aşağıdaki cümlelerin hangisinde nesne kullanılmamıştır?',
                'ders': 'turkce', 'sinav_tipi': 'TYT',
                'detayli_aciklama': '"Çocuklar parkta oynuyor." cümlesinde nesne yoktur.',
                'cevaplar': [
                    ('A) Annem çiçekleri suladı.', False),
                    ('B) Kitabı masanın üzerine koydum.', False),
                    ('C) Çocuklar parkta oynuyor.', True),
                    ('D) Öğretmen soruları dağıttı.', False),
                ]
            },
            {
                'metin': 'Aşağıdaki sözcüklerden hangisi yapım eki almamıştır?',
                'ders': 'turkce', 'sinav_tipi': 'TYT',
                'detayli_aciklama': '"Kalem" sözcüğü yapım eki almamış, kök halindedir.',
                'cevaplar': [
                    ('A) Güzellik', False),
                    ('B) Kalem', True),
                    ('C) Çalışkan', False),
                    ('D) Okumuş', False),
                ]
            },
            {
                'metin': '"Küçük çocuk, büyük bir heyecanla sahneye çıktı." cümlesinde kaç sıfat vardır?',
                'ders': 'turkce', 'sinav_tipi': 'TYT',
                'detayli_aciklama': 'Küçük, büyük ve bir olmak üzere 3 sıfat vardır.',
                'cevaplar': [
                    ('A) 1', False),
                    ('B) 2', False),
                    ('C) 3', True),
                    ('D) 4', False),
                ]
            },
            {
                'metin': 'Aşağıdaki cümlelerin hangisinde zarf kullanılmıştır?',
                'ders': 'turkce', 'sinav_tipi': 'TYT',
                'detayli_aciklama': '"Hızla" sözcüğü durum zarfıdır.',
                'cevaplar': [
                    ('A) Güzel çiçekler aldım.', False),
                    ('B) Bu kitap çok kalın.', False),
                    ('C) Hızla eve koştu.', True),
                    ('D) Kırmızı araba geçti.', False),
                ]
            },
            {
                'metin': 'Aşağıdakilerin hangisinde ünsüz yumuşaması vardır?',
                'ders': 'turkce', 'sinav_tipi': 'TYT',
                'detayli_aciklama': 'Kitap → kitabı: p→b ünsüz yumuşaması olmuştur.',
                'cevaplar': [
                    ('A) Evler', False),
                    ('B) Kitabı', True),
                    ('C) Okulda', False),
                    ('D) Masaya', False),
                ]
            },
            {
                'metin': 'Aşağıdaki cümlelerin hangisi birleşik cümledir?',
                'ders': 'turkce', 'sinav_tipi': 'TYT',
                'detayli_aciklama': '"Hava soğuyunca evde kaldık" cümlesinde zarf-fiil eki ile birleşik cümle oluşmuştur.',
                'cevaplar': [
                    ('A) Bugün hava güzel.', False),
                    ('B) Hava soğuyunca evde kaldık.', True),
                    ('C) Ali okula gitti.', False),
                    ('D) Bahçede çiçekler açtı.', False),
                ]
            },
            {
                'metin': '"İnsanlar, zor zamanlarda birbirlerine destek olmalıdır." cümlesinin yüklemi hangisidir?',
                'ders': 'turkce', 'sinav_tipi': 'TYT',
                'detayli_aciklama': 'Yüklem cümlenin sonundaki "olmalıdır" sözcüğüdür.',
                'cevaplar': [
                    ('A) İnsanlar', False),
                    ('B) Destek', False),
                    ('C) Olmalıdır', True),
                    ('D) Birbirlerine', False),
                ]
            },
            {
                'metin': 'Aşağıdaki cümlelerin hangisinde "de/da" bağlacı kullanılmıştır?',
                'ders': 'turkce', 'sinav_tipi': 'TYT',
                'detayli_aciklama': '"Sen de gel" cümlesindeki "de" bağlaçtır ve ayrı yazılır.',
                'cevaplar': [
                    ('A) Evde kimse yok.', False),
                    ('B) Sen de gel bizimle.', True),
                    ('C) Okulda ders işledik.', False),
                    ('D) Bahçede top oynadık.', False),
                ]
            },
        ])

        # ==================== FİZİK (TYT + AYT) ====================
        sorular.extend([
            {
                'metin': 'Bir cismin hızı sabit ise aşağıdakilerden hangisi kesinlikle doğrudur?',
                'ders': 'fizik', 'sinav_tipi': 'TYT',
                'detayli_aciklama': 'Hızı sabit olan cisme etki eden net kuvvet sıfırdır (Newton 1. yasası).',
                'cevaplar': [
                    ('A) Cisme etki eden net kuvvet sıfırdır.', True),
                    ('B) Cisim hareket etmiyordur.', False),
                    ('C) Cisme hiç kuvvet etki etmiyordur.', False),
                    ('D) Cismin ivmesi artmaktadır.', False),
                ]
            },
            {
                'metin': 'Serbest düşme yapan cismin 3. saniye sonundaki hızı kaç m/s? (g=10 m/s²)',
                'ders': 'fizik', 'sinav_tipi': 'TYT',
                'detayli_aciklama': 'v = g × t = 10 × 3 = 30 m/s',
                'cevaplar': [
                    ('A) 10', False),
                    ('B) 20', False),
                    ('C) 30', True),
                    ('D) 45', False),
                ]
            },
            {
                'metin': 'Hızı 2 katına çıkan cismin kinetik enerjisi kaç katına çıkar?',
                'ders': 'fizik', 'sinav_tipi': 'TYT',
                'detayli_aciklama': 'Ek = ½mv². Hız 2 katına çıkınca Ek 4 katına çıkar.',
                'cevaplar': [
                    ('A) 2', False),
                    ('B) 4', True),
                    ('C) 8', False),
                    ('D) 16', False),
                ]
            },
            {
                'metin': 'Işığın vakumda yayılma hızı yaklaşık kaç m/s\'dir?',
                'ders': 'fizik', 'sinav_tipi': 'TYT',
                'detayli_aciklama': 'Işık hızı c ≈ 3 × 10⁸ m/s.',
                'cevaplar': [
                    ('A) 3 × 10⁶ m/s', False),
                    ('B) 3 × 10⁸ m/s', True),
                    ('C) 3 × 10¹⁰ m/s', False),
                    ('D) 3 × 10⁴ m/s', False),
                ]
            },
            {
                'metin': 'Yerden 20 m yükseklikten serbest bırakılan cisim yere kaç saniyede ulaşır? (g=10)',
                'ders': 'fizik', 'sinav_tipi': 'TYT',
                'detayli_aciklama': 'h = ½gt² → 20 = ½×10×t² → t = 2 s',
                'cevaplar': [
                    ('A) 1 s', False),
                    ('B) 2 s', True),
                    ('C) 3 s', False),
                    ('D) 4 s', False),
                ]
            },
            {
                'metin': 'Coulomb yasasında iki yük arası uzaklık 3 katına çıkarılırsa kuvvet nasıl değişir?',
                'ders': 'fizik', 'sinav_tipi': 'AYT',
                'detayli_aciklama': 'F = kq₁q₂/r². Uzaklık 3 kat → F\' = F/9.',
                'cevaplar': [
                    ('A) 3 katına çıkar', False),
                    ('B) 9 katına çıkar', False),
                    ('C) 1/3 katına düşer', False),
                    ('D) 1/9 katına düşer', True),
                ]
            },
            {
                'metin': 'Dalga boyu 0,5 m ve frekansı 600 Hz olan dalganın hızı kaç m/s?',
                'ders': 'fizik', 'sinav_tipi': 'AYT',
                'detayli_aciklama': 'v = λ × f = 0,5 × 600 = 300 m/s',
                'cevaplar': [
                    ('A) 120', False),
                    ('B) 300', True),
                    ('C) 1200', False),
                    ('D) 600', False),
                ]
            },
            {
                'metin': 'İdeal transformatörde primer 200, sekonder 50 sarım ise gerilim kaç kat düşer?',
                'ders': 'fizik', 'sinav_tipi': 'AYT',
                'detayli_aciklama': 'V₁/V₂ = N₁/N₂ → 200/50 = 4 kat düşer.',
                'cevaplar': [
                    ('A) 2', False),
                    ('B) 4', True),
                    ('C) 8', False),
                    ('D) 50', False),
                ]
            },
            {
                'metin': 'İletkenin boyu 2 katına çıkıp kesit alanı yarıya düşürülürse direnci nasıl değişir?',
                'ders': 'fizik', 'sinav_tipi': 'AYT',
                'detayli_aciklama': 'R = ρL/A → R\' = ρ(2L)/(A/2) = 4R.',
                'cevaplar': [
                    ('A) 2 katına çıkar', False),
                    ('B) 4 katına çıkar', True),
                    ('C) Yarıya düşer', False),
                    ('D) Değişmez', False),
                ]
            },
            {
                'metin': 'Eşit kollu terazide bir kefede 200 g, diğerinde 150 g varsa ne olur?',
                'ders': 'fizik', 'sinav_tipi': 'TYT',
                'detayli_aciklama': '200 g olan kefe daha ağır olduğu için aşağı iner.',
                'cevaplar': [
                    ('A) Terazi dengede kalır.', False),
                    ('B) 200 g olan kefe aşağı iner.', True),
                    ('C) 150 g olan kefe aşağı iner.', False),
                    ('D) Her iki kefe de aşağı iner.', False),
                ]
            },
        ])

        # ==================== KİMYA (TYT + AYT) ====================
        sorular.extend([
            {
                'metin': 'Periyodik tabloda aynı grupta aşağıya doğru inildikçe aşağıdakilerden hangisi artar?',
                'ders': 'kimya', 'sinav_tipi': 'TYT',
                'detayli_aciklama': 'Aynı grupta aşağıya inildikçe atom çapı artar.',
                'cevaplar': [
                    ('A) İyonlaşma enerjisi', False),
                    ('B) Elektronegatiflik', False),
                    ('C) Atom çapı', True),
                    ('D) Elektron ilgisi', False),
                ]
            },
            {
                'metin': 'pH değeri 3 olan çözeltinin H⁺ derişimi kaçtır?',
                'ders': 'kimya', 'sinav_tipi': 'TYT',
                'detayli_aciklama': 'pH = -log[H⁺] → [H⁺] = 10⁻³ M',
                'cevaplar': [
                    ('A) 10⁻¹ M', False),
                    ('B) 10⁻³ M', True),
                    ('C) 10⁻⁷ M', False),
                    ('D) 10⁻¹⁴ M', False),
                ]
            },
            {
                'metin': 'Aşağıdakilerden hangisi kovalent bağ içerir?',
                'ders': 'kimya', 'sinav_tipi': 'TYT',
                'detayli_aciklama': 'H₂O kovalent bağ içerir. NaCl ve KBr iyonik bağlıdır.',
                'cevaplar': [
                    ('A) NaCl', False),
                    ('B) KBr', False),
                    ('C) H₂O', True),
                    ('D) CaO', False),
                ]
            },
            {
                'metin': 'Avogadro sayısı aşağıdakilerden hangisidir?',
                'ders': 'kimya', 'sinav_tipi': 'TYT',
                'detayli_aciklama': 'Avogadro sayısı 6,02 × 10²³ tür.',
                'cevaplar': [
                    ('A) 6,02 × 10²³', True),
                    ('B) 3,14 × 10²³', False),
                    ('C) 6,02 × 10²⁰', False),
                    ('D) 1,60 × 10⁻¹⁹', False),
                ]
            },
            {
                'metin': '2 mol H₂ ile 1 mol O₂ tepkimesinden kaç mol H₂O oluşur?',
                'ders': 'kimya', 'sinav_tipi': 'TYT',
                'detayli_aciklama': '2H₂ + O₂ → 2H₂O → 2 mol H₂O oluşur.',
                'cevaplar': [
                    ('A) 1 mol', False),
                    ('B) 2 mol', True),
                    ('C) 3 mol', False),
                    ('D) 4 mol', False),
                ]
            },
            {
                'metin': 'Bir atomun kütle numarası 23, proton sayısı 11 ise nötron sayısı kaçtır?',
                'ders': 'kimya', 'sinav_tipi': 'TYT',
                'detayli_aciklama': '23 - 11 = 12 nötron.',
                'cevaplar': [
                    ('A) 11', False),
                    ('B) 12', True),
                    ('C) 23', False),
                    ('D) 34', False),
                ]
            },
            {
                'metin': 'Aşağıdakilerden hangisi organik bir bileşiktir?',
                'ders': 'kimya', 'sinav_tipi': 'AYT',
                'detayli_aciklama': 'Metan (CH₄) karbon içeren organik bir bileşiktir.',
                'cevaplar': [
                    ('A) NaCl', False),
                    ('B) H₂SO₄', False),
                    ('C) CH₄', True),
                    ('D) CaCO₃', False),
                ]
            },
            {
                'metin': 'Le Chatelier ilkesinde basınç artırılırsa denge hangi yöne kayar?',
                'ders': 'kimya', 'sinav_tipi': 'AYT',
                'detayli_aciklama': 'Basınç artırılırsa denge mol sayısı az olan tarafa kayar.',
                'cevaplar': [
                    ('A) Her zaman ileri yöne', False),
                    ('B) Her zaman geri yöne', False),
                    ('C) Mol sayısı az olan tarafa', True),
                    ('D) Denge değişmez', False),
                ]
            },
            {
                'metin': 'Aşağıdakilerden hangisi bir elektrolit değildir?',
                'ders': 'kimya', 'sinav_tipi': 'AYT',
                'detayli_aciklama': 'Şeker suda iyon oluşturmaz, elektrolit değildir.',
                'cevaplar': [
                    ('A) NaOH', False),
                    ('B) HCl', False),
                    ('C) Şeker (C₁₂H₂₂O₁₁)', True),
                    ('D) H₂SO₄', False),
                ]
            },
            {
                'metin': 'Aşağıdaki tepkimelerden hangisi nötrleşme tepkimesidir?',
                'ders': 'kimya', 'sinav_tipi': 'AYT',
                'detayli_aciklama': 'Asit + Baz → Tuz + Su nötrleşme tepkimesidir.',
                'cevaplar': [
                    ('A) 2H₂ + O₂ → 2H₂O', False),
                    ('B) HCl + NaOH → NaCl + H₂O', True),
                    ('C) CaCO₃ → CaO + CO₂', False),
                    ('D) 2Na + Cl₂ → 2NaCl', False),
                ]
            },
        ])

        # ==================== BİYOLOJİ (TYT + AYT) ====================
        sorular.extend([
            {
                'metin': 'Hücrenin enerji santrali olarak bilinen organel hangisidir?',
                'ders': 'biyoloji', 'sinav_tipi': 'TYT',
                'detayli_aciklama': 'Mitokondri hücresel solunum yaparak ATP üretir.',
                'cevaplar': [
                    ('A) Ribozom', False),
                    ('B) Mitokondri', True),
                    ('C) Golgi cisimciği', False),
                    ('D) Lizozom', False),
                ]
            },
            {
                'metin': 'DNA\'nın yapısında aşağıdaki bazlardan hangisi bulunmaz?',
                'ders': 'biyoloji', 'sinav_tipi': 'TYT',
                'detayli_aciklama': 'Urasil RNA\'ya özgüdür, DNA\'da Timin bulunur.',
                'cevaplar': [
                    ('A) Adenin', False),
                    ('B) Guanin', False),
                    ('C) Timin', False),
                    ('D) Urasil', True),
                ]
            },
            {
                'metin': 'Aşağıdakilerden hangisi prokaryot hücredir?',
                'ders': 'biyoloji', 'sinav_tipi': 'TYT',
                'detayli_aciklama': 'Bakteriler prokaryot hücrelerdir.',
                'cevaplar': [
                    ('A) Bitki hücresi', False),
                    ('B) Hayvan hücresi', False),
                    ('C) Bakteri', True),
                    ('D) Mantar hücresi', False),
                ]
            },
            {
                'metin': 'Ekosistemlerde enerji akışının doğru sıralaması hangisidir?',
                'ders': 'biyoloji', 'sinav_tipi': 'TYT',
                'detayli_aciklama': 'Üreticiler → Tüketiciler → Ayrıştırıcılar.',
                'cevaplar': [
                    ('A) Tüketiciler → Üreticiler → Ayrıştırıcılar', False),
                    ('B) Üreticiler → Tüketiciler → Ayrıştırıcılar', True),
                    ('C) Ayrıştırıcılar → Tüketiciler → Üreticiler', False),
                    ('D) Tüketiciler → Ayrıştırıcılar → Üreticiler', False),
                ]
            },
            {
                'metin': 'Aşağıdakilerden hangisi hayvan hücresinde bulunmaz?',
                'ders': 'biyoloji', 'sinav_tipi': 'TYT',
                'detayli_aciklama': 'Hücre duvarı bitki hücrelerine özgüdür.',
                'cevaplar': [
                    ('A) Mitokondri', False),
                    ('B) Hücre duvarı', True),
                    ('C) Ribozom', False),
                    ('D) Golgi cisimciği', False),
                ]
            },
            {
                'metin': 'Karaciğerin temel görevlerinden biri aşağıdakilerden hangisidir?',
                'ders': 'biyoloji', 'sinav_tipi': 'TYT',
                'detayli_aciklama': 'Karaciğer safra üretir ve zehirli maddeleri etkisizleştirir.',
                'cevaplar': [
                    ('A) Oksijen taşımak', False),
                    ('B) Kan hücresi üretmek', False),
                    ('C) Safra üretmek ve zehirli maddeleri etkisizleştirmek', True),
                    ('D) İdrar üretmek', False),
                ]
            },
            {
                'metin': 'Fotosentezin ışık reaksiyonları kloroplastın hangi bölümünde gerçekleşir?',
                'ders': 'biyoloji', 'sinav_tipi': 'AYT',
                'detayli_aciklama': 'Işık reaksiyonları tilakoit zarlarında gerçekleşir.',
                'cevaplar': [
                    ('A) Stroma', False),
                    ('B) Tilakoit zarları', True),
                    ('C) Çift zar', False),
                    ('D) Sitoplazma', False),
                ]
            },
            {
                'metin': 'AaBb genotipli bireyin oluşturabileceği gamet çeşidi sayısı kaçtır?',
                'ders': 'biyoloji', 'sinav_tipi': 'AYT',
                'detayli_aciklama': '2ⁿ → n=2 → 4 gamet: AB, Ab, aB, ab.',
                'cevaplar': [
                    ('A) 2', False),
                    ('B) 4', True),
                    ('C) 8', False),
                    ('D) 16', False),
                ]
            },
            {
                'metin': 'Protein sentezinin gerçekleştiği organel hangisidir?',
                'ders': 'biyoloji', 'sinav_tipi': 'AYT',
                'detayli_aciklama': 'Ribozomlar mRNA üzerinden protein sentezler.',
                'cevaplar': [
                    ('A) Mitokondri', False),
                    ('B) Lizozom', False),
                    ('C) Ribozom', True),
                    ('D) Peroksizom', False),
                ]
            },
            {
                'metin': 'Homolog kromozomların ayrılması mayozun hangi evresinde gerçekleşir?',
                'ders': 'biyoloji', 'sinav_tipi': 'AYT',
                'detayli_aciklama': 'Homolog kromozomlar Anafaz I\'de ayrılır.',
                'cevaplar': [
                    ('A) Profaz I', False),
                    ('B) Anafaz I', True),
                    ('C) Metafaz II', False),
                    ('D) Telofaz II', False),
                ]
            },
        ])

        # ==================== TARİH (TYT + AYT) ====================
        sorular.extend([
            {
                'metin': 'Tanzimat Fermanı hangi yılda ilan edilmiştir?',
                'ders': 'tarih', 'sinav_tipi': 'TYT',
                'detayli_aciklama': 'Tanzimat Fermanı 1839\'da ilan edilmiştir.',
                'cevaplar': [
                    ('A) 1808', False),
                    ('B) 1839', True),
                    ('C) 1876', False),
                    ('D) 1856', False),
                ]
            },
            {
                'metin': 'TBMM ilk kez hangi tarihte açılmıştır?',
                'ders': 'tarih', 'sinav_tipi': 'TYT',
                'detayli_aciklama': 'TBMM 23 Nisan 1920\'de açılmıştır.',
                'cevaplar': [
                    ('A) 19 Mayıs 1919', False),
                    ('B) 23 Nisan 1920', True),
                    ('C) 29 Ekim 1923', False),
                    ('D) 30 Ağustos 1922', False),
                ]
            },
            {
                'metin': 'Aşağıdakilerden hangisi Atatürk İnkılaplarından biri değildir?',
                'ders': 'tarih', 'sinav_tipi': 'TYT',
                'detayli_aciklama': 'Mecelle Osmanlı döneminde hazırlanmış medeni kanundur.',
                'cevaplar': [
                    ('A) Harf İnkılabı', False),
                    ('B) Soyadı Kanunu', False),
                    ('C) Mecelle\'nin kabulü', True),
                    ('D) Medeni Kanun\'un kabulü', False),
                ]
            },
            {
                'metin': 'İstanbul\'un fethi hangi padişah döneminde gerçekleşmiştir?',
                'ders': 'tarih', 'sinav_tipi': 'TYT',
                'detayli_aciklama': 'İstanbul 1453\'te Fatih Sultan Mehmet tarafından fethedildi.',
                'cevaplar': [
                    ('A) Yıldırım Bayezid', False),
                    ('B) II. Murad', False),
                    ('C) Fatih Sultan Mehmet', True),
                    ('D) Kanuni Sultan Süleyman', False),
                ]
            },
            {
                'metin': 'Birinci Dünya Savaşı hangi yıllar arasında gerçekleşmiştir?',
                'ders': 'tarih', 'sinav_tipi': 'TYT',
                'detayli_aciklama': 'I. Dünya Savaşı 1914-1918 arasında yaşanmıştır.',
                'cevaplar': [
                    ('A) 1905-1910', False),
                    ('B) 1914-1918', True),
                    ('C) 1939-1945', False),
                    ('D) 1912-1916', False),
                ]
            },
            {
                'metin': 'Osmanlı Devleti\'nin kuruluş yılı hangisidir?',
                'ders': 'tarih', 'sinav_tipi': 'TYT',
                'detayli_aciklama': 'Osmanlı 1299\'da Osman Bey tarafından kurulmuştur.',
                'cevaplar': [
                    ('A) 1071', False),
                    ('B) 1299', True),
                    ('C) 1453', False),
                    ('D) 1326', False),
                ]
            },
            {
                'metin': 'Kurtuluş Savaşı\'nın son muharebesi hangisidir?',
                'ders': 'tarih', 'sinav_tipi': 'AYT',
                'detayli_aciklama': 'Başkomutanlık Meydan Muharebesi (30 Ağustos 1922).',
                'cevaplar': [
                    ('A) Sakarya Meydan Muharebesi', False),
                    ('B) İnönü Muharebeleri', False),
                    ('C) Başkomutanlık Meydan Muharebesi', True),
                    ('D) Çanakkale Savaşı', False),
                ]
            },
            {
                'metin': 'Fransız İhtilali hangi yılda gerçekleşmiştir?',
                'ders': 'tarih', 'sinav_tipi': 'AYT',
                'detayli_aciklama': 'Fransız İhtilali 1789\'da başlamıştır.',
                'cevaplar': [
                    ('A) 1776', False),
                    ('B) 1789', True),
                    ('C) 1815', False),
                    ('D) 1848', False),
                ]
            },
            {
                'metin': 'Lozan Barış Antlaşması hangi yılda imzalanmıştır?',
                'ders': 'tarih', 'sinav_tipi': 'AYT',
                'detayli_aciklama': 'Lozan 24 Temmuz 1923\'te imzalanmıştır.',
                'cevaplar': [
                    ('A) 1920', False),
                    ('B) 1921', False),
                    ('C) 1923', True),
                    ('D) 1924', False),
                ]
            },
            {
                'metin': 'Aşağıdakilerden hangisi Sivas Kongresi kararlarından biridir?',
                'ders': 'tarih', 'sinav_tipi': 'AYT',
                'detayli_aciklama': 'Sivas Kongresi\'nde tüm cemiyetler birleştirilmiştir.',
                'cevaplar': [
                    ('A) İstanbul Hükümeti\'nin tanınması', False),
                    ('B) Manda ve himaye kabul edilmiştir', False),
                    ('C) Tüm cemiyetler birleştirilmiştir', True),
                    ('D) Saltanat kaldırılmıştır', False),
                ]
            },
        ])

        # ==================== COĞRAFYA (TYT + AYT) ====================
        sorular.extend([
            {
                'metin': 'Türkiye\'de en fazla yağış alan bölge hangisidir?',
                'ders': 'cografya', 'sinav_tipi': 'TYT',
                'detayli_aciklama': 'Doğu Karadeniz en fazla yağış alan bölgedir.',
                'cevaplar': [
                    ('A) Ege', False),
                    ('B) Marmara', False),
                    ('C) Doğu Karadeniz', True),
                    ('D) Akdeniz', False),
                ]
            },
            {
                'metin': 'Aşağıdakilerden hangisi iç kuvvetler tarafından oluşturulmuş yer şeklidir?',
                'ders': 'cografya', 'sinav_tipi': 'TYT',
                'detayli_aciklama': 'Volkanik dağlar iç kuvvetler tarafından oluşturulur.',
                'cevaplar': [
                    ('A) Vadi', False),
                    ('B) Delta', False),
                    ('C) Volkanik dağ', True),
                    ('D) Kumul', False),
                ]
            },
            {
                'metin': 'Dünyanın en kalabalık kıtası hangisidir?',
                'ders': 'cografya', 'sinav_tipi': 'TYT',
                'detayli_aciklama': 'Asya en kalabalık kıtadır.',
                'cevaplar': [
                    ('A) Afrika', False),
                    ('B) Avrupa', False),
                    ('C) Asya', True),
                    ('D) Kuzey Amerika', False),
                ]
            },
            {
                'metin': 'Akdeniz ikliminin en belirgin özelliği hangisidir?',
                'ders': 'cografya', 'sinav_tipi': 'TYT',
                'detayli_aciklama': 'Yazlar sıcak-kurak, kışlar ılık-yağışlı.',
                'cevaplar': [
                    ('A) Yazlar serin ve yağışlı, kışlar soğuk', False),
                    ('B) Yazlar sıcak ve kurak, kışlar ılık ve yağışlı', True),
                    ('C) Dört mevsim bol yağışlı', False),
                    ('D) Yıl boyunca kurak', False),
                ]
            },
            {
                'metin': 'Türkiye\'nin en uzun nehri hangisidir?',
                'ders': 'cografya', 'sinav_tipi': 'TYT',
                'detayli_aciklama': 'Kızılırmak 1355 km ile Türkiye\'nin en uzun nehridir.',
                'cevaplar': [
                    ('A) Fırat', False),
                    ('B) Kızılırmak', True),
                    ('C) Sakarya', False),
                    ('D) Dicle', False),
                ]
            },
            {
                'metin': 'Rüzgâr aşındırmasının en etkili olduğu iklim tipi hangisidir?',
                'ders': 'cografya', 'sinav_tipi': 'AYT',
                'detayli_aciklama': 'Çöl ikliminde bitki örtüsü az, rüzgâr aşındırması en etkilidir.',
                'cevaplar': [
                    ('A) Ekvatoral iklim', False),
                    ('B) Çöl iklimi', True),
                    ('C) Karasal iklim', False),
                    ('D) Okyanusal iklim', False),
                ]
            },
            {
                'metin': 'Aşağıdakilerden hangisi yenilenebilir enerji kaynağıdır?',
                'ders': 'cografya', 'sinav_tipi': 'AYT',
                'detayli_aciklama': 'Güneş enerjisi yenilenebilirdir.',
                'cevaplar': [
                    ('A) Kömür', False),
                    ('B) Doğalgaz', False),
                    ('C) Güneş enerjisi', True),
                    ('D) Petrol', False),
                ]
            },
            {
                'metin': 'Türkiye\'de nüfusu en fazla olan şehir hangisidir?',
                'ders': 'cografya', 'sinav_tipi': 'TYT',
                'detayli_aciklama': 'İstanbul Türkiye\'nin en kalabalık şehridir.',
                'cevaplar': [
                    ('A) Ankara', False),
                    ('B) İstanbul', True),
                    ('C) İzmir', False),
                    ('D) Bursa', False),
                ]
            },
            {
                'metin': 'Haritada eğim hesaplanırken aşağıdakilerden hangisi kullanılır?',
                'ders': 'cografya', 'sinav_tipi': 'TYT',
                'detayli_aciklama': 'Eğim = Yükseklik farkı / Yatay mesafe.',
                'cevaplar': [
                    ('A) Yükseklik farkı / Yatay mesafe', True),
                    ('B) Yatay mesafe / Yükseklik farkı', False),
                    ('C) Yükseklik farkı × Yatay mesafe', False),
                    ('D) Yatay mesafe × Ölçek', False),
                ]
            },
            {
                'metin': 'Aşağıdakilerden hangisi bir ova oluşum şeklidir?',
                'ders': 'cografya', 'sinav_tipi': 'AYT',
                'detayli_aciklama': 'Delta ovası akarsu alüvyonlarıyla oluşur.',
                'cevaplar': [
                    ('A) Tektonik göl', False),
                    ('B) Karstik mağara', False),
                    ('C) Delta ovası', True),
                    ('D) Volkanik krater', False),
                ]
            },
        ])

        # ==================== FELSEFE (TYT) ====================
        sorular.extend([
            {
                'metin': '"Düşünüyorum, öyleyse varım." sözü hangi filozofa aittir?',
                'ders': 'felsefe', 'sinav_tipi': 'TYT',
                'detayli_aciklama': 'Bu söz Descartes\'a aittir.',
                'cevaplar': [
                    ('A) Platon', False),
                    ('B) Aristoteles', False),
                    ('C) Descartes', True),
                    ('D) Kant', False),
                ]
            },
            {
                'metin': '"Varlık nedir?" sorusuyla ilgilenen felsefe alanı hangisidir?',
                'ders': 'felsefe', 'sinav_tipi': 'TYT',
                'detayli_aciklama': 'Ontoloji varlığın doğasını inceler.',
                'cevaplar': [
                    ('A) Epistemoloji', False),
                    ('B) Ontoloji', True),
                    ('C) Etik', False),
                    ('D) Estetik', False),
                ]
            },
            {
                'metin': 'Bilginin kaynağının akıl olduğunu savunan akım hangisidir?',
                'ders': 'felsefe', 'sinav_tipi': 'TYT',
                'detayli_aciklama': 'Rasyonalizm bilginin kaynağının akıl olduğunu savunur.',
                'cevaplar': [
                    ('A) Empirizm', False),
                    ('B) Rasyonalizm', True),
                    ('C) Pragmatizm', False),
                    ('D) Nihilizm', False),
                ]
            },
            {
                'metin': 'Sokrates\'in felsefe yöntemi aşağıdakilerden hangisidir?',
                'ders': 'felsefe', 'sinav_tipi': 'TYT',
                'detayli_aciklama': 'Sokrates diyalektik (doğurtma) yöntemini kullanmıştır.',
                'cevaplar': [
                    ('A) Tümdengelim', False),
                    ('B) Tümevarım', False),
                    ('C) Diyalektik (doğurtma)', True),
                    ('D) Fenomenoloji', False),
                ]
            },
            {
                'metin': 'Eylemlerin sonuçlarına göre ahlaki değerlendirme yapan yaklaşım hangisidir?',
                'ders': 'felsefe', 'sinav_tipi': 'TYT',
                'detayli_aciklama': 'Faydacılık eylemleri sonuçlarına göre değerlendirir.',
                'cevaplar': [
                    ('A) Deontoloji', False),
                    ('B) Faydacılık', True),
                    ('C) Erdem etiği', False),
                    ('D) Nihilizm', False),
                ]
            },
            {
                'metin': '"İdealar dünyası" kavramını ortaya atan düşünür kimdir?',
                'ders': 'felsefe', 'sinav_tipi': 'TYT',
                'detayli_aciklama': 'Platon idealar dünyası kavramını ortaya atmıştır.',
                'cevaplar': [
                    ('A) Aristoteles', False),
                    ('B) Platon', True),
                    ('C) Herakleitos', False),
                    ('D) Epikuros', False),
                ]
            },
            {
                'metin': 'Epistemoloji hangi konuyu inceler?',
                'ders': 'felsefe', 'sinav_tipi': 'TYT',
                'detayli_aciklama': 'Epistemoloji bilginin doğasını ve kaynağını inceler.',
                'cevaplar': [
                    ('A) Güzellik ve sanat', False),
                    ('B) Ahlaki değerler', False),
                    ('C) Bilginin doğası ve kaynağı', True),
                    ('D) Devlet yönetimi', False),
                ]
            },
            {
                'metin': 'Varoluşçuluk akımının öncülerinden biri kimdir?',
                'ders': 'felsefe', 'sinav_tipi': 'TYT',
                'detayli_aciklama': 'Sartre varoluşçuluğun en önemli temsilcilerindendir.',
                'cevaplar': [
                    ('A) Karl Marx', False),
                    ('B) Auguste Comte', False),
                    ('C) Jean-Paul Sartre', True),
                    ('D) John Locke', False),
                ]
            },
            {
                'metin': 'Bilginin kaynağının deney ve gözlem olduğunu savunan akım hangisidir?',
                'ders': 'felsefe', 'sinav_tipi': 'TYT',
                'detayli_aciklama': 'Empirizm tüm bilginin deneyimden geldiğini savunur.',
                'cevaplar': [
                    ('A) Rasyonalizm', False),
                    ('B) Empirizm', True),
                    ('C) Kritisizm', False),
                    ('D) Pozitivizm', False),
                ]
            },
            {
                'metin': 'Aşağıdakilerden hangisi estetik felsefesinin temel sorusudur?',
                'ders': 'felsefe', 'sinav_tipi': 'TYT',
                'detayli_aciklama': 'Estetik, güzelliğin doğasını sorgular.',
                'cevaplar': [
                    ('A) Bilgi nedir?', False),
                    ('B) Doğru eylem nedir?', False),
                    ('C) Güzel nedir?', True),
                    ('D) Varlık nedir?', False),
                ]
            },
        ])

        # ==================== VERİTABANINA EKLE ====================
        eklenen = 0
        for soru_data in sorular:
            soru = Soru.objects.create(
                metin=soru_data['metin'],
                ders=soru_data['ders'],
                sinav_tipi=soru_data['sinav_tipi'],
                detayli_aciklama=soru_data.get('detayli_aciklama', ''),
                bul_bakalimda_cikar=True,
                karsilasmada_cikar=True,
            )
            for cevap_metin, dogru_mu in soru_data['cevaplar']:
                Cevap.objects.create(
                    soru=soru,
                    metin=cevap_metin,
                    dogru_mu=dogru_mu,
                )
            eklenen += 1

        self.stdout.write(self.style.SUCCESS(
            f'\n✅ Toplam {eklenen} soru başarıyla eklendi!'
        ))

        from collections import Counter
        ders_sayilari = Counter(s['ders'] for s in sorular)
        for ders, sayi in sorted(ders_sayilari.items()):
            self.stdout.write(f'  📚 {ders}: {sayi} soru')
