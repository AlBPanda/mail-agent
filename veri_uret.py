import json
import os
import random

SYSTEM_PROMPT = (
    "Sen bir mail analiz uzmanısın. Sana verilen Türkçe iş maillerini analiz edip "
    "kesinlikle sadece JSON formatında çıktı veriyorsun. Hiçbir ek açıklama yapmıyorsun."
)


def make_entry(mail_text: str, output_dict: dict) -> dict:
    return {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Aşağıdaki maili analiz et:\n\n{mail_text}"},
            {"role": "assistant", "content": json.dumps(output_dict, ensure_ascii=False)}
        ]
    }


random.seed(101)
examples = []

isimler = [
    "Ahmet Yılmaz", "Selin Demir", "Mert Korkmaz", "Zeynep Aksoy", "Burak Şahin",
    "Emre Yıldırım", "Canan Özdemir", "Kaan Çelik", "Deniz Arslan", "Oğuzhan Kaya",
    "Tarık Ünal", "Melis Aydın", "Hakan Polat", "Sinem Kılıç", "Onur Çetin",
    "Derya Koç", "Tolga Erdem", "Kemal Soylu", "Büşra Yıldız", "Pınar Aktaş",
    "Cemil Vural", "Gizem Tunca", "Barış Karaca", "Nihan Sezer", "Uğur Koçak",
    "Levent Kırca", "Tuğba Er", "Alp Arslan", "Seda Yalçın", "Murat Özkan",
    "Elif Çetin", "Kerem Aktaş", "Yeliz Kaya", "Cihan Demir", "Aslıhan Gür",
    "Fırat Soydan", "Gökhan Türk", "Şule Aydın", "Kadir İnan", "Zehra Taş"
]

unvanlar = [
    "Finans Müdürü", "Altyapı Ekip Lideri", "Hukuk Müşavirliği", "Satın Alma Uzmanı",
    "Müşteri İlişkileri", "Kıdemli Yazılım Uzmanı", "Muhasebe Sorumlusu", "Üretim Planlama",
    "Pazarlama Direktörü", "Bilgi Güvenliği Uzmanı", "Veritabanı Yöneticisi", "Ürün Yöneticisi",
    "Genel Müdür Yardımcısı", "Ofis Yöneticisi", "Veri Analisti", "DevOps Mühendisi",
    "İK Uzmanı", "Satış Direktörü", "Lojistik Sorumlusu", "Kalite Güvence Lideri",
    "CTO", "Sistem Yöneticisi", "Fabrika Müdürü", "Kurumsal İletişim Uzmanı"
]

gunler = [
    "Bugün", "Yarın", "Bu akşam", "Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma",
    "12 Ekim Pazartesi", "14 Ekim Çarşamba", "15 Ekim Perşembe", "16 Ekim Cuma",
    "19 Ekim Pazartesi", "21 Ekim Çarşamba", "22 Ekim Perşembe", "23 Ekim Cuma",
    "26 Ekim Pazartesi", "27 Ekim Salı", "28 Ekim Çarşamba", "30 Ekim Cuma",
    "2 Kasım Pazartesi", "4 Kasım Çarşamba", "6 Kasım Cuma", "10 Kasım Salı"
]

saatler = [
    "09:00", "09:30", "10:00", "10:30", "11:00", "11:30", "12:00",
    "13:30", "14:00", "14:30", "15:00", "15:30", "16:00", "16:30",
    "17:00", "17:30", "18:00", "19:30", "21:00", "23:59"
]

hitaplar = [
    "Merhaba,", "Selamlar,", "Selam ekip,", "Değerli Arkadaşlar,",
    "Merhaba arkadaşlar,", "Sayın İlgili,", "Selam,"
]

kapanislar = [
    "İyi çalışmalar.", "Teşekkürler, kolay gelsin.", "Acil dönüşünüzü rica ederim.",
    "Bilgilerinize, iyi çalışmalar.", "Saygılarımla.", "Teşekkürler."
]

# =====================================================================
# 1. BÖLÜM: 500 TAMAMEN BENZERSİZ AKSİYON GEREKLİ MAİL
# Modelin ezber yapmaması için her mailde farklı nesneler, sistemler,
# sayılar ve doğrudan metinden çıkarılan görevler kullanılır.
# =====================================================================

sistemler = [
    "PostgreSQL kümesi", "MongoDB veritabanı", "Redis önbellek sunucusu", "Kafka mesaj kuyruğu",
    "Elasticsearch arama motoru", "RabbitMQ servisi", "Docker kayıt sunucusu", "Kubernetes prod kümesi",
    "Nginx yük dengeleyici", "OAuth2 kimlik doğrulama servisi", "Ödeme geçidi API'si", "Fatura kesim mikroservisi",
    "Stok takip modülü", "Müşteri bildirim servisi", "Mobil iOS uygulaması", "Android saha uygulaması",
    "B2B bayi portalı", "İK bordro sistemi", "CRM müşteri paneli", "ERP muhasebe entegrasyonu",
    "Raporlama veri ambarı", "Yedekleme (Backup) sunucusu", " Kurumsal VPN ağ geçidi", "GitLab CI/CD hattı",
    "Grafana izleme paneli"
]

teknik_eylemler = [
    ("bağlantı adreslerini yeni IP'ye yönlendirme", "servis bağlantı adreslerini (connection string) yeni IP'ye yönlendir", "test ortamında bağlantıyı doğrula", "eski sunucunun kapatılması", "yuksek"),
    ("SSL sertifikası yenileme", "yeni SSL sertifikasını sunucuya yükle", "HTTPS erişimini test edip sonucu bildir", "eski sertifikanın süresinin dolması", "yuksek"),
    ("bellek sızıntısı (memory leak) yaması", "güncel hotfix paketini canlı ortama yükle", "RAM kullanım grafiğini 2 saat boyunca izle", "sistem performans değerlendirmesi", "yuksek"),
    ("veritabanı indeks optimizasyonu", "yavaş çalışan SQL sorguları için yeni indeksleri oluştur", "sorgu yanıt sürelerini raporla", "haftalık veritabanı bakımı", "orta"),
    ("kullanıcı yetki tablosu temizliği", "işten ayrılan personelin erişim anahtarlarını iptal et", "güncel yetki listesini güvenlik ekibine gönder", "ISO 27001 güvenlik denetimi", "yuksek"),
    ("API hız sınırı (rate limit) güncellemesi", "kurumsal müşteriler için dakika başı istek limitini 500'e çıkar", "yapılandırma dosyasını yeniden başlat", "müşteri yük testi", "orta"),
    ("disk alanı temizliği ve log arşivleme", "30 günden eski uygulama loglarını soğuk depoya taşı", "boşalan disk alanını kontrol edip bilgi ver", "sunucu kapasite kontrolü", "yuksek"),
    ("güvenlik duvarı (firewall) kural tanımlama", "yeni servis için 8443 portuna erişim izni tanımla", "telnet ile port erişimini test et", "canlı ortam geçişi", "orta"),
    ("sürüm (release) öncesi kod incelemesi", "açılan Pull Request içindeki birim testlerini çalıştır", "hata yoksa kodu ana dala (main) birleştir", "yeni sürüm yayını", "yuksek"),
    ("felaket kurtarma yedekleme testi", "son alınan veritabanı yedeğini test sunucusuna geri yükle", "veri bütünlüğünü kontrol edip tutanak tut", "aylık denetim kapanışı", "orta")
]

kurumsal_konular = [
    ("Anadolu Lojistik", "kargo taşıma sözleşmesi", "sözleşmedeki cezai şart maddesini revize et", "imzalı nüshayı hukuk birimine ilet", "tedarikçi sözleşme imzası", "yuksek"),
    ("Demirbank", "canlı ürün demosu hazırlığı", "demo ortamındaki örnek müşteri verilerini güncelle", "sunum akışını baştan sona test et", "müşteri demo toplantısı", "yuksek"),
    ("Kuzey Enerji", "yıllık bakım teklifi", "ekipman maliyet tablosunu güncel döviz kuruyla yeniden hesapla", "revize fiyat teklifini satış müdürüne gönder", "ihale son teklif saati", "yuksek"),
    ("Yıldız Holding", "KVKK veri işleme protokolü", "ekteki gizlilik sözleşmesinin 5. maddesini incele", "hukuki görüş notunu e-posta ile paylaş", "yönetim onay toplantısı", "orta"),
    ("Büyükşehir Belediyesi", "ihale teknik şartname dosyası", "ürünlerimizin şartnameye uygunluk tablosunu doldur", "kaşeli belgeyi ihale klasörüne yükle", "ihale komisyonu oturumu", "yuksek"),
    ("Marmara Tekstil", "arızalı barkod okuyucu değişimi", "depodaki yedek cihaz stok miktarını kontrol et", "müşteriye yeni sevkiyat tarihini bildir", "iade süresi dolumu", "yuksek"),
    ("Ege Gıda", "Ekim ayı e-fatura mutabakatı", "sistemdeki açık faturaları müşteri ekstresiyle karşılaştır", "mutabakat mektubunu onaylayıp muhasebeye gönder", "ay sonu vergi kapanışı", "orta"),
    ("Akdeniz Turizm", "mobil uygulama tasarım onayı", "Figma üzerindeki yeni rezervasyon ekranlarını incele", "tasarım revizyon notlarını ekip liderine ilet", "sprint planlama toplantısı", "dusuk"),
    ("Avrasya Telekom", "sunucu lisans yenileme faturası", "%15 kurumsal indirimli proforma faturayı onayla", "ödeme talimatı için belgeyi finansa teslim et", "indirim kampanyası bitişi", "yuksek"),
    ("Boğaziçi Yazılım", "stajyer ve yeni mezun mülakatları", "dün görüşülen 4 adayın teknik değerlendirme puanlarını gir", "seçilen aday listesini İK departmanına gönder", "iş teklifi açıklaması", "orta")
]

departman_gorevleri = [
    ("Bütçe ve Finans", "Q{q} departman harcama raporu", "{miktar} TL tutarındaki gider kalemlerini faturalarla eşleştir", "bütçe özet tablosunu finans müdürüne gönder", "yönetim kurulu bütçe sunumu", "yuksek"),
    ("İnsan Kaynakları", "{ay} ayı fazla mesai çizelgesi", "ekibindeki personelin toplam mesai saatlerini doğrula", "imzalı çizelgeyi İK portalına yükle", "maaş bordro kesim tarihi", "orta"),
    ("Üretim Planlama", "{hat}. Hat CNC tezgahı periyodik bakımı", "bekleyen siparişleri diğer üretim hattına kaydır", "güncel vardiya listesini ustabaşına ilet", "planlı bakım duruşu", "yuksek"),
    ("Satın Alma", "{departman} departmanı donanım talebi", "talep edilen {adet} adet monitör için 3 ayrı tedarikçiden teklif al", "karşılaştırma tablosunu satın alma komitesine sun", "bütçe onay komitesi", "orta"),
    ("Bilgi Güvenliği", "Zorunlu siber güvenlik ve oltalama eğitimi", "eğitim portalındaki {modul}. modül videolarını tamamla", "modül sonundaki çevrimiçi sınavdan en az 80 puan al", "ISO denetim başlangıcı", "dusuk"),
    ("Lojistik ve Depo", "{sehir} deposu aylık stok sayımı", "fiziksel sayım sonuçlarını ERP stok kayıtlarıyla karşılaştır", "eksik çıkan kalemler için tutanak hazırla", "çeyrek dönem envanter kapanışı", "yuksek"),
    ("Kurumsal İletişim", "Yeni ürün lansmanı basın bülteni", "metindeki teknik terimleri ve performans verilerini kontrol et", "son okuma onayını ajansa gönderilmeden önce paylaş", "basın bülteni dağıtımı", "orta"),
    ("İdari İşler", "Şirket araçları kış lastiği değişimi", "zimmetindeki {plaka} plakalı aracı yetkili servise götür", "servis işlem fişini idari işlere teslim et", "kış lastiği zorunluluğu başlangıcı", "dusuk"),
    ("Kalite Güvence", "Üretim parti #{parti} laboratuvar testleri", "numune dayanıklılık test sonuçlarını standartlarla kıyasla", "sevkiyat uygunluk belgesini imzala", "müşteri tır yüklemesi", "yuksek"),
    ("Ar-Ge Merkezi", "TÜBİTAK proje ilerleme raporu", "son 3 ayda yapılan model eğitim deneylerini dökümante et", "rapor taslağını proje yürütücüsüne gönder", "TÜBİTAK sistem yükleme son günü", "yuksek")
]

for i in range(500):
    gonderen = f"{random.choice(isimler)} ({random.choice(unvanlar)})"
    t1 = f"{random.choice(gunler)} {random.choice(saatler)}"
    t2 = f"{random.choice(gunler)} {random.choice(saatler)}"
    while t2 == t1:
        t2 = f"{random.choice(gunler)} {random.choice(saatler)}"

    hitap = random.choice(hitaplar)
    kapanis = random.choice(kapanislar)

    grup = i % 3
    if grup == 0:
        sistem = sistemler[i % len(sistemler)]
        eylem_adi, g1, g2, olay2_adi, oncelik = teknik_eylemler[(i // len(sistemler)) % len(teknik_eylemler)]
        versiyon = f"v{random.randint(1,5)}.{random.randint(0,9)}"
        konu = f"{sistem} ({versiyon}) - {eylem_adi.capitalize()}"
        olay1 = f"{sistem} {eylem_adi}"
        gorev1 = f"{sistem} üzerinde {g1}"
        gorev2 = g2.capitalize()
        olay2 = f"{sistem} {olay2_adi}"
    elif grup == 1:
        firma, konu_eki, g1, g2, olay2_adi, oncelik = kurumsal_konular[i % len(kurumsal_konular)]
        proje_kodu = f"PRJ-{100 + i}"
        konu = f"{firma} ({proje_kodu}) {konu_eki.title()}"
        olay1 = f"{firma} {konu_eki} tamamlanması"
        gorev1 = f"{firma} için {g1}"
        gorev2 = g2.capitalize()
        olay2 = f"{firma} {olay2_adi}"
    else:
        dep, konu_sablon, g1_sablon, g2, olay2_adi, oncelik = departman_gorevleri[i % len(departman_gorevleri)]
        q = random.randint(1, 4)
        miktar = random.randint(15, 250) * 1000
        ay = random.choice(["Eylül", "Ekim", "Kasım"])
        hat = random.randint(1, 6)
        adet = random.randint(5, 40)
        modul = random.randint(1, 8)
        sehir = random.choice(["İzmir", "Ankara", "Bursa", "Kocaeli", "Adana", "Antalya"])
        plaka = f"34 {random.choice(['ABC', 'KLM', 'TKP', 'YZM', 'DEF'])} {random.randint(10, 99)}"
        parti = random.randint(1000, 9999)

        konu = konu_sablon.format(q=q, ay=ay, hat=hat, departman=dep, sehir=sehir, parti=parti)
        g1_tam = g1_sablon.format(miktar=miktar, adet=adet, modul=modul, plaka=plaka)
        olay1 = f"{konu} işlemleri"
        gorev1 = g1_tam.capitalize()
        gorev2 = g2.capitalize()
        olay2 = olay2_adi.capitalize()

    # Tek tarihli mi yoksa çift tarihli mi?
    cift_tarihli = (i % 2 == 0)
    if cift_tarihli:
        tarih_listesi = [
            {"olay": olay1, "tarih": t1},
            {"olay": olay2, "tarih": t2}
        ]
        kalip = i % 3
        if kalip == 0:
            govde = (
                f"{hitap}\n"
                f"{konu} kapsamında yürüttüğümüz çalışmalarda kritik aşamaya geldik. "
                f"En geç {t1} tarihine kadar '{gorev1}' ve '{gorev2}' adımlarını tamamlamanız gerekmektedir. "
                f"Ardından {t2} tarihinde {olay2.lower()} gerçekleştirilecektir.\n\n"
                f"{kapanis}"
            )
        elif kalip == 1:
            govde = (
                f"{hitap}\n"
                f"Bildiğiniz üzere {t2} itibarıyla {olay2.lower()} planlanmaktadır. "
                f"Bu süreçten önce {t1} saatine kadar:\n"
                f"- {gorev1}\n"
                f"- {gorev2}\n"
                f"işlemlerinin eksiksiz bitirilmesini rica ederim.\n\n"
                f"{kapanis}"
            )
        else:
            govde = (
                f"{hitap}\n"
                f"{konu} için takvimimiz netleşmiştir. İlk olarak {t1} tarihine kadar {gorev1.lower()} ve {gorev2.lower()} görevlerini tamamlayalım. "
                f"{t2} tarihinde ise {olay2.lower()} yapılacaktır.\n\n"
                f"{kapanis}"
            )
        ozet = f"{t2} tarihindeki {olay2.lower()} öncesinde, {t1} saatine kadar {olay1.lower()} kapsamındaki görevlerin tamamlanması gerekiyor."
    else:
        tarih_listesi = [
            {"olay": olay1, "tarih": t1}
        ]
        kalip = i % 3
        if kalip == 0:
            govde = (
                f"{hitap}\n"
                f"{konu} ile ilgili süreci zamanında kapatabilmemiz için en geç {t1} tarihine kadar şu iki adımı tamamlamanızı rica ederim:\n"
                f"1. {gorev1}\n"
                f"2. {gorev2}\n\n"
                f"{kapanis}"
            )
        elif kalip == 1:
            govde = (
                f"{hitap}\n"
                f"{olay1} konusunda son tarihe yaklaşıyoruz. Lütfen {t1} saatine kadar {gorev1.lower()} ve ardından {gorev2.lower()}.\n\n"
                f"{kapanis}"
            )
        else:
            govde = (
                f"{hitap}\n"
                f"{konu} kapsamında aksama yaşanmaması adına {t1} terminine dikkat edelim. "
                f"Yapılacak işler: {gorev1}. Ayrıca {gorev2}.\n\n"
                f"{kapanis}"
            )
        ozet = f"{konu} kapsamında belirtilen görevlerin en geç {t1} tarihine kadar tamamlanması isteniyor."

    tam_mail = f"Gönderen: {gonderen}\nKonu: {konu}\n\n{govde}"
    cikti = {
        "mail_turu": "aksiyon_gerekli",
        "gonderen": gonderen,
        "oncelik": oncelik,
        "tarihler_ve_terminler": tarih_listesi,
        "yapilacak_isler": [gorev1, gorev2],
        "ozet": ozet
    }
    examples.append(make_entry(tam_mail, cikti))


# =====================================================================
# 2. BÖLÜM: 250 BENZERSİZ BİLGİLENDİRME MAİLİ
# =====================================================================

bilgi_konulari = [
    ("İdari İşler", "{kat}. Kat Kart Okuyucu Turnike Yenilemesi", "Binamızın {kat}. katındaki giriş turnikeleri yenilenmiştir; mevcut personel kartlarınızla herhangi bir işlem yapmadan geçiş yapabilirsiniz."),
    ("IT Destek", "{sistem} Planlı Bakım Çalışması Tamamlandı", "Gece gerçekleştirilen {sistem} altyapı güncellemesi başarıyla tamamlanmış olup tüm servisler sorunsuz çalışmaktadır."),
    ("İnsan Kaynakları", "{isim} - Aramıza Yeni Katılan Çalışma Arkadaşımız", "{departman} ekibimize {isim} katılmıştır; kendisine aramıza hoş geldin diyor ve başarılar diliyoruz."),
    ("Proje Yönetim Ofisi", "Sprint {sprint} Kapanış Özeti", "Sprint {sprint} kapsamında planlanan işlerin %{oran}'i başarıyla tamamlanmıştır; emeği geçen tüm ekibe teşekkür ederiz."),
    ("Resepsiyon", "Danışmaya Gelen {kargo} Kargo Teslimatı", "Adınıza gelen #{takip} takip numaralı {kargo} gönderisi danışma bankosuna bırakılmıştır, müsait olduğunuzda alabilirsiniz."),
    ("Müşteri İlişkileri", "{ay} Ayı Müşteri Memnuniyet (NPS) Skoru", "{ay} ayı yapılan anketler sonucunda şirketimizin NPS müşteri memnuniyet skoru {puan} puana yükselmiştir."),
    ("Bilgi Güvenliği", "Aylık Yedekleme ve Kurtarma Testi Sonucu", "Veri merkezimizde yapılan periyodik felaket kurtarma testi %{oran} başarı ve sıfır veri kaybıyla tamamlanmıştır."),
    ("Ofis Yönetimi", "{oda} Toplantı Odası Ekipman Yenilemesi", "{oda} toplantı odasındaki projeksiyon ve ses sistemi yenilenmiş olup kullanıma açılmıştır."),
    ("Finans Departmanı", "{ay} Ayı Sabit Kur Tablosu Yayınlandı", "{ay} ayı iç bütçe raporlamalarında kullanılacak referans döviz kuru tablosu intranet sistemine yüklenmiştir."),
    ("Sosyal Komite", "Şirket İçi {etkinlik} Turnuvası Sonuçları", "Bu dönem düzenlenen {etkinlik} turnuvasında birinciliği {isim} kazanmıştır, kendisini tebrik ederiz.")
]

kargo_firmalari = ["Yurtiçi", "Aras", "MNG", "DHL", "UPS", "PTT"]
toplantı_odalari = ["Boğaziçi", "Marmara", "Ege", "Toros", "Anadolu", "3. Kat Büyük", "A Blok"]
etkinlikler = ["Satranç", "Masa Tenisi", "Bilardo", "Bowling", "E-Spor", "Dart"]

for i in range(250):
    gonderen, konu_sablon, ozet_sablon = bilgi_konulari[i % len(bilgi_konulari)]
    kat = (i % 8) + 1
    sistem = sistemler[i % len(sistemler)]
    isim = isimler[i % len(isimler)]
    departman = unvanlar[i % len(unvanlar)].split()[0]
    sprint = 10 + (i % 40)
    oran = 92 + (i % 8)
    kargo = kargo_firmalari[i % len(kargo_firmalari)]
    takip = 100000 + i * 37
    ay = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"][i % 12]
    puan = 72 + (i % 20)
    oda = toplantı_odalari[i % len(toplantı_odalari)]
    etkinlik = etkinlikler[i % len(etkinlikler)]

    konu = konu_sablon.format(kat=kat, sistem=sistem, isim=isim, sprint=sprint, kargo=kargo, ay=ay, oda=oda, etkinlik=etkinlik)
    ozet_metni = ozet_sablon.format(kat=kat, sistem=sistem, isim=isim, departman=departman, sprint=sprint, oran=oran, kargo=kargo, takip=takip, ay=ay, puan=puan, oda=oda, etkinlik=etkinlik)

    hitap = random.choice(hitaplar)
    ek = random.choice([
        "Herhangi bir işlem yapmanıza gerek yoktur.",
        "Sadece bilgilendirme amaçlıdır, aksiyon gerekmemektedir.",
        "Tarafınızca yapılacak bir işlem bulunmamaktadır."
    ])
    govde = f"{hitap}\n{ozet_metni} {ek}\n\nİyi çalışmalar dileriz."
    tam_mail = f"Gönderen: {gonderen}\nKonu: {konu}\n\n{govde}"

    cikti = {
        "mail_turu": "bilgilendirme",
        "gonderen": gonderen,
        "oncelik": "dusuk",
        "tarihler_ve_terminler": [],
        "yapilacak_isler": [],
        "ozet": ozet_metni
    }
    examples.append(make_entry(tam_mail, cikti))


# =====================================================================
# 3. BÖLÜM: 250 BENZERSİZ REKLAM / SPAM / TUZAK BÜLTEN MAİLİ
# =====================================================================

markalar = [
    ("firsat@teknomarketim.com", "TeknoMarket"), ("kampanya@supermoda.com", "SüperModa"),
    ("bulten@kriptoakademi.io", "KriptoAkademi"), ("info@tatilcenneti.net", "TatilCenneti"),
    ("no-reply@lezzetkapida.com", "LezzetKapıda"), ("satis@zirveseo.com", "Zirve SEO Ajansı"),
    ("vip@sanslicasino777.com", "ŞanslıCasino"), ("duyuru@ucuzucakbileti.com", "UcuzBilet"),
    ("promo@hizliarackirala.com", "HızlıAraç"), ("reklam@bulutmuhasebe.io", "BulutMuhasebe"),
    ("bildirim@profesyonelağ.com", "ProAğ"), ("kampanya@evdekorasyon.com", "EvDekor")
]

urunler = [
    "oyuncu laptoplarında", "kışlık mont ve botlarda", "akıllı saat ve kulaklıklarda",
    "yurt dışı uçak biletlerinde", "Antalya erken rezervasyon otellerinde", "yıllık bulut depolama paketlerinde",
    "online İngilizce eğitim setlerinde", "borsa ve kripto VIP sinyallerinde", "organik cilt bakım ürünlerinde",
    "kurumsal SEO ve reklam paketlerinde", "tüm restoran siparişlerinde", "4K televizyon ve ses sistemlerinde"
]

for i in range(250):
    eposta, marka = markalar[i % len(markalar)]
    urun = urunler[(i // len(markalar)) % len(urunler)]
    indirim = random.choice([25, 30, 40, 50, 60, 70, 75, 80])
    kupon = f"FIRSAT{indirim}{i}"
    saat1 = random.choice(["18:00", "20:00", "21:00", "22:00"])
    saat2 = "23:59"
    gun = random.choice(gunler)
    fiyat = random.choice([199, 299, 499, 999, 1499, 2500, 5000])

    kalip = i % 4
    if kalip == 0:
        konu = f"{marka} Dev Gece İndirimi {gun} Saat {saat1}'de Başlıyor!"
        govde = f"Merhaba,\nSadece {gun} {saat1} ile {saat2} saatleri arasında geçerli {urun} %{indirim} indirim fırsatını kaçırmayın! Kupon kodunuz: {kupon}"
    elif kalip == 1:
        konu = f"Son Çağrı: {urun.title()} %{indirim} İndirim İçin Son Saatler!"
        govde = f"Değerli müşterimiz,\nSepetinizdeki ürünlerde sadece bugün {saat2}'a kadar geçerli {fiyat} TL hediye çeki tanımlandı! Hemen alışverişe başlayın."
    elif kalip == 2:
        konu = f"Tebrikler! {marka} Hesabınıza {fiyat} TL Bonus Tanımlandı"
        govde = f"Selam,\nŞanslı kullanıcımız seçildiniz! {gun} saat {saat1}'e kadar linke tıklayarak {fiyat} TL değerindeki promosyon ödülünüzü hemen kullanabilirsiniz."
    else:
        konu = f"{marka} Hafta Sonu Fırsatı: {urun.title()} Dev Kampanya"
        govde = f"Merhaba,\n{urun.capitalize()} peşin fiyatına 6 taksit ve %{indirim} indirim avantajı başladı! Kampanya {gun} gece {saat2}'da sona erecektir."

    tam_mail = f"Gönderen: {eposta}\nKonu: {konu}\n\n{govde}"
    cikti = {
        "mail_turu": "reklam_spam",
        "islem": "yoksay"
    }
    examples.append(make_entry(tam_mail, cikti))

random.shuffle(examples)

os.makedirs("data", exist_ok=True)
output_path = os.path.join("data", "mail_egitim.jsonl")

with open(output_path, "w", encoding="utf-8") as f:
    for entry in examples:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

boyut_kb = os.path.getsize(output_path) / 1024
print(f"Toplam {len(examples)} adet TAMAMEN BENZERSİZ eğitim örneği '{output_path}' dosyasına yazıldı!")
print(f"Dosya boyutu: {boyut_kb:.1f} KB ({boyut_kb/1024:.2f} MB)")
