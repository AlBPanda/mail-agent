import json
import os
import random

random.seed(42)

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


# ── Ortak Havuzlar ────────────────────────────────────────────────────────────
isimler = [
    "Ahmet Yılmaz", "Zeynep Kaya", "Mehmet Demir", "Elif Çelik", "Caner Şahin",
    "Selin Yıldız", "Burak Özkan", "Ayşe Arslan", "Murat Aydın", "Deniz Polat",
    "Serkan Koç", "Gamze Doğan", "Tolga Kılıç", "Pınar Aslan", "Onur Çetin",
    "Esra Kurt", "Sinan Koçak", "Büşra Yalçın", "Emre Taş", "Derya Aksoy",
    "Kaan Korkmaz", "Merve Çakır", "Oğuzhan Erdoğan", "Tuğba Şen", "Alperen Yavuz",
    "Hande Yıldırım", "Fikret Başaran", "Cansu Öztürk", "Berkay Çiçek", "Nazlı Doğru",
    "Volkan Acar", "Yasemin Güler", "İbrahim Şahin", "Tuba Kara", "Selim Erdoğan",
]

unvanlar = [
    "Finans Müdürü", "Bütçe Uzmanı", "Muhasebe Sorumlusu", "DevOps Lideri",
    "Sistem Yöneticisi", "Güvenlik Uzmanı", "Altyapı Mühendisi", "Hukuk Müşaviri",
    "İK Uzmanı", "Proje Yöneticisi", "Ürün Yöneticisi", "Satın Alma Uzmanı",
    "Kalite Lideri", "Veritabanı Yöneticisi", "Operasyon Direktörü",
    "CTO", "CEO", "Baş Mühendis", "Teknik Lider", "Scrum Master",
    "Veri Bilimcisi", "Bulut Mimarı", "Uyum Sorumlusu", "Risk Analisti",
]

hitaplar = [
    "Merhaba,", "Selamlar,", "İyi günler,", "Arkadaşlar merhaba,", "Ekip selam,",
    "Sayın ilgili,", "Herkese merhaba,", "Merhaba ekip,",
]
kapanislar = [
    "İyi çalışmalar.", "Teşekkürler.", "Acil dönüşünüzü rica ederim.",
    "Bilgilerinize sunarım.", "Saygılarımla.", "Lütfen bu konuyu öncelikle ele alın.",
    "Koordinasyonunuz için teşekkür ederim.",
]

gunler = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Yarın", "Bugün"]
aylar = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
         "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
saatler = ["09:00", "10:00", "10:30", "11:00", "11:30", "13:00",
           "13:30", "14:00", "15:00", "15:30", "16:00", "17:00", "17:30"]
gece_saatleri = ["18:00", "19:00", "20:00", "21:00", "22:00", "23:00", "23:30", "23:59"]

sistemler = [
    "Redis önbellek sunucusu", "PostgreSQL veritabanı", "Kafka mesaj kuyruğu",
    "Kubernetes kümesi", "Elasticsearch sunucusu", "API Gateway servisi",
    "RabbitMQ kuyruğu", "Docker Registry sunucusu", "Nginx yük dengeleyici",
    "SSO kimlik servisi", "ERP canlı veritabanı", "3D Secure ödeme servisi",
    "MongoDB kümeleri", "Vault gizli yönetim servisi", "Grafana izleme sistemi",
    "CI/CD pipeline altyapısı", "LDAP kimlik doğrulama sunucusu",
    "S3 uyumlu nesne depolama", "Prometheus metrik sunucusu",
]

projeler = [
    "Mobil Uygulama v4.2", "B2B Bayi Portalı", "Kurumsal CRM Geçişi",
    "E-Fatura Entegrasyonu", "Hızlı Ödeme Geçidi", "Canlı Destek Modülü",
    "Veri Ambarı Geçişi", "Tedarikçi Paneli", "İK Portalı v3",
    "Analitik Dashboard", "API Ağ Geçidi v2", "Müşteri Self-Servis Portalı",
    "Depo Yönetim Sistemi", "Dijital İmza Platformu", "IoT Veri Kolektörü",
]

departmanlar = [
    "Pazarlama", "Ar-Ge", "Bilgi Teknolojileri", "Lojistik", "Satın Alma",
    "Finans", "Hukuk", "Operasyon", "İnsan Kaynakları", "Strateji",
]

examples = []


def rastgele_tarih(idx: int) -> tuple[str, str]:
    tip = idx % 6
    gun = random.choice(gunler)
    saat = random.choice(saatler)
    gece = random.choice(gece_saatleri)
    gun_no = random.randint(2, 28)
    ay = random.choice(aylar)
    if tip == 0:
        t1 = f"{gun} saat {saat}" if gun in ("Yarın", "Bugün") else f"{gun} günü saat {saat}"
        t2 = f"Cuma sabahı {random.choice(['06:00','08:00','09:00'])}"
    elif tip == 1:
        t1 = f"Yarın {saat}"
        t2 = f"{gun} {saat}"
    elif tip == 2:
        t1 = f"{gun_no} {ay} saat {saat}"
        t2 = f"{gun_no + 3} {ay} saat {saat}"
    elif tip == 3:
        t1 = f"Bu akşam {gece}"
        t2 = f"Yarın sabah 09:00"
    elif tip == 4:
        t1 = f"{gun} {saat}"
        t2 = f"Bu hafta Cuma {gece}"
    else:
        t1 = f"Bu hafta {gun} {saat}"
        t2 = f"Gelecek {gun} {saat}"
    return t1, t2


# =====================================================================
# 1. BÖLÜM: 800 AKSİYON GEREKTİREN İŞ MAİLİ (%40)
# 10 farklı senaryo × 80 örnek
# =====================================================================

SENARYO_SAYISI = 10

for i in range(800):
    gonderen = f"{random.choice(isimler)} ({random.choice(unvanlar)})"
    hitap = random.choice(hitaplar)
    kapanis = random.choice(kapanislar)
    t1, t2 = rastgele_tarih(i)
    senaryo = i % SENARYO_SAYISI
    numara = 100 + i

    if senaryo == 0:
        # Sunucu/altyapı taşıma
        sistem = sistemler[i % len(sistemler)]
        dep = departmanlar[i % len(departmanlar)]
        konu = f"[ACİL] {sistem.title()} Bakım ve Taşıma Planı"
        gorev1 = f"bağlı servislerin bağlantı adreslerini yeni IP'ye yönlendir"
        gorev2 = "test ortamında bağlantı ve yük testlerini tamamla"
        olay1 = f"{sistem} taşıma penceresi"
        olay2 = "Canlı ortamın devreye alınması"
        oncelik = "yuksek"
        govde = (
            f"{hitap}\n"
            f"{sistem.title()} taşıma penceresi {t1} olarak planlanmıştır. "
            f"Taşıma öncesinde {gorev1} ve {gorev2} adımlarını tamamlamanız kritik önem taşımaktadır. "
            f"Canlı ortamın devreye alınması ise {t2} olarak öngörülmektedir.\n\n{kapanis}"
        )
        ozet = f"{t1} tarihindeki {sistem} taşıması için {gorev1} ve {gorev2} tamamlanmalı."

    elif senaryo == 1:
        # Fatura ve bütçe onayı
        dep = departmanlar[i % len(departmanlar)]
        konu = f"{dep} Bölümü Proforma Fatura Onayı (FAT-{numara})"
        gorev1 = f"indirimli proforma faturayı kaşele ve imzala"
        gorev2 = "onaylı faturayı finans sistemine yükle ve bütçe kodunu gir"
        olay1 = f"FAT-{numara} fatura son onay tarihi"
        olay2 = "Yönetim kurulu bütçe sunumu"
        oncelik = "yuksek"
        govde = (
            f"{hitap}\n"
            f"{dep} bölümüne ait FAT-{numara} numaralı proforma faturanın {t1} tarihine kadar "
            f"onaylanması gerekmektedir. Lütfen {gorev1} ve {gorev2} işlemlerini tamamlayın. "
            f"Yönetim kurulu sunumu {t2} tarihinde gerçekleşecektir.\n\n{kapanis}"
        )
        ozet = f"FAT-{numara} faturası {t1} tarihine kadar imzalanıp finans sistemine yüklenmeli."

    elif senaryo == 2:
        # Sertifika yenilemesi
        proje = projeler[i % len(projeler)]
        konu = f"{proje} SSL/TLS Sertifika Yenilemesi"
        gorev1 = f"yeni kök sertifikayı canlı servise tanımla"
        gorev2 = "test ortamında HTTPS el sıkışmasını doğrula"
        olay1 = f"{proje} sertifika son geçerlilik tarihi"
        olay2 = "Eski sertifika geçersiz hale geliyor"
        oncelik = "yuksek"
        govde = (
            f"{hitap}\n"
            f"{proje} üzerindeki SSL sertifikası {t1} tarihinde sona erecektir. "
            f"Hizmet kesintisi yaşanmaması için en geç {t1} saatine kadar "
            f"{gorev1} ve {gorev2} adımlarını tamamlayın.\n\n{kapanis}"
        )
        ozet = f"{proje} SSL sertifikası {t1} itibarıyla geçersiz; yenileme adımları tamamlanmalı."

    elif senaryo == 3:
        # KVKK / hukuki denetim
        proje = projeler[(i + 5) % len(projeler)]
        konu = f"KVKK Uyum Denetimi — {proje} Erişim Logları Talebi"
        gorev1 = "son 6 aylık veritabanı erişim loglarını dışa aktar"
        gorev2 = "imzalı tutanakla birlikte hukuk müşavirliğine teslim et"
        olay1 = "Denetim için log teslim tarihi"
        olay2 = "Denetim kapanış toplantısı"
        oncelik = "yuksek"
        govde = (
            f"{hitap}\n"
            f"KVKK denetimi kapsamında {proje} sistemine ait erişim loglarının {t1} tarihine kadar "
            f"hazırlanması gerekmektedir. Lütfen {gorev1} ve ardından {gorev2} işlemlerini yapın. "
            f"Kapanış toplantısı {t2} olarak planlanmıştır.\n\n{kapanis}"
        )
        ozet = f"KVKK denetimi için {proje} erişim logları {t1} tarihine kadar hukuk müşavirliğine teslim edilmeli."

    elif senaryo == 4:
        # Yatırımcı/yönetim sunumu revizesi
        dep = departmanlar[(i + 2) % len(departmanlar)]
        konu = f"ACİL — {dep} Nakit Akış Tablosu Revizesi"
        gorev1 = "nakit akış tablosunu son kur verileriyle güncelle"
        gorev2 = "yönetim kurulu paylaşım grubuna PDF olarak gönder"
        olay1 = f"Güncel nakit akış tablosu teslim tarihi"
        olay2 = "Yatırımcı toplantısı"
        oncelik = "yuksek"
        govde = (
            f"{hitap}\n"
            f"Yatırımcı toplantısı için {dep} nakit akış tablosunun {t1} tarihine kadar revize edilmesi kritik. "
            f"Lütfen {gorev1} ve {gorev2} işlemlerini en kısa sürede tamamlayın. "
            f"Toplantı {t2} tarihinde başlayacaktır.\n\n{kapanis}"
        )
        ozet = f"Yatırımcı toplantısı ({t2}) öncesinde {dep} nakit akış tablosu {t1} itibarıyla güncellenip gönderilmeli."

    elif senaryo == 5:
        # Güvenlik açığı/penetrasyon testi
        sistem = sistemler[(i + 3) % len(sistemler)]
        konu = f"Güvenlik Açığı Bildirimi — {sistem.title()} (CVE-2026-{numara})"
        gorev1 = f"{sistem} üzerinde acil güvenlik yamasını uygula"
        gorev2 = "yama sonrası penetrasyon testi raporunu paylaş"
        olay1 = "Yama uygulama son tarihi"
        olay2 = "Güvenlik denetim kapanışı"
        oncelik = "yuksek"
        govde = (
            f"{hitap}\n"
            f"{sistem.title()} sisteminde kritik bir güvenlik açığı (CVE-2026-{numara}) tespit edilmiştir. "
            f"En geç {t1} tarihine kadar {gorev1} ve {gorev2} adımlarını tamamlamanız gerekmektedir. "
            f"Denetim kapanış toplantısı {t2} olarak planlanmıştır.\n\n{kapanis}"
        )
        ozet = f"CVE-2026-{numara} açığı için {sistem} {t1} tarihine kadar yamalanıp test raporu paylaşılmalı."

    elif senaryo == 6:
        # Sprint kapanışı / sürüm onayı
        proje = projeler[(i + 2) % len(projeler)]
        konu = f"{proje} Sprint-{numara % 30 + 1} Kapanış ve Sürüm Onayı"
        gorev1 = "açık hataları Jira'da kapatarak sürüm notlarını hazırla"
        gorev2 = "onaylı sürümü App Store ve Play Store'a gönder"
        olay1 = "Sürüm not teslim tarihi"
        olay2 = "Mağaza gönderim son tarihi"
        oncelik = "yuksek"
        govde = (
            f"{hitap}\n"
            f"{proje} Sprint-{numara % 30 + 1} kapanışı {t1} olarak planlanmıştır. "
            f"Bu tarihe kadar {gorev1} ve {gorev2} tamamlanmalıdır. "
            f"Mağaza incelemeleri genellikle 3 iş günü sürmektedir.\n\n{kapanis}"
        )
        ozet = f"{proje} Sprint kapanışı için {t1} itibarıyla sürüm notları hazırlanıp mağazaya gönderilmeli."

    elif senaryo == 7:
        # Lisans yenileme / tedarikçi sözleşmesi
        dep = departmanlar[(i + 4) % len(departmanlar)]
        konu = f"Yazılım Lisansı Yenilemesi — {dep} Departmanı"
        gorev1 = "mevcut lisans envanterini ve kullanım raporunu hazırla"
        gorev2 = "tedarikçi teklifini onaylayıp satın alma talebini sisteme gir"
        olay1 = "Mevcut lisans bitiş tarihi"
        olay2 = "Tedarikçi teklif geçerlilik sonu"
        oncelik = "yuksek"
        govde = (
            f"{hitap}\n"
            f"{dep} departmanı için kullanılan yazılım lisansları {t1} tarihinde sona erecektir. "
            f"Hizmet kesintisi yaşanmaması için en geç {t1} tarihine kadar "
            f"{gorev1} ve {gorev2} işlemlerini tamamlayın. "
            f"Tedarikçi teklifinin geçerliliği {t2} tarihine kadar devam etmektedir.\n\n{kapanis}"
        )
        ozet = f"{dep} yazılım lisansları {t1} tarihinde bitiyor; envanter ve satın alma talebi tamamlanmalı."

    elif senaryo == 8:
        # Acil toplantı / karar gerektiren durum
        dep = departmanlar[(i + 1) % len(departmanlar)]
        konu = f"Acil Toplantı Daveti — {dep} Kriz Yönetimi"
        gorev1 = f"{dep} bölümünün son durum raporunu hazırla"
        gorev2 = "toplantı gündemini tüm katılımcılara gönder"
        olay1 = "Kriz toplantısı başlangıcı"
        olay2 = "Aksiyon planı teslim tarihi"
        oncelik = "yuksek"
        govde = (
            f"{hitap}\n"
            f"{dep} bölümünde acil bir gelişme yaşandı. "
            f"{t1} saatinde kriz toplantısı düzenliyoruz. "
            f"Toplantı öncesinde lütfen {gorev1} ve {gorev2} işlemlerini tamamlayın. "
            f"Aksiyon planının {t2} tarihine kadar hazır olması beklenmektedir.\n\n{kapanis}"
        )
        ozet = f"{dep} kriz toplantısı {t1}; öncesinde durum raporu hazırlanıp gündem gönderilmeli."

    else:
        # Yedek sistem (DR) tatbikatı / iş sürekliliği
        sistem = sistemler[(i + 7) % len(sistemler)]
        konu = f"Felaket Kurtarma Tatbikatı — {sistem.title()}"
        gorev1 = f"{sistem} yedek ortamını devreye al ve bağlantı testini tamamla"
        gorev2 = "tatbikat sonuç raporunu BT yöneticisine ilet"
        olay1 = "DR tatbikat başlangıcı"
        olay2 = "Tatbikat rapor teslim tarihi"
        oncelik = "orta"
        govde = (
            f"{hitap}\n"
            f"Yıllık felaket kurtarma tatbikatımız kapsamında {sistem.title()} için test {t1} tarihinde başlayacaktır. "
            f"Tatbikat sırasında {gorev1} ve {gorev2} adımlarını tamamlamanız beklenmektedir. "
            f"Raporların {t2} tarihine kadar iletilmesi gerekmektedir.\n\n{kapanis}"
        )
        ozet = f"{sistem} DR tatbikatı {t1}; yedek ortam devreye alınıp sonuç raporu {t2} tarihinde iletilmeli."

    cift_tarihli = (i % 2 == 0)
    if cift_tarihli:
        tarih_listesi = [{"olay": olay1, "tarih": t1}, {"olay": olay2, "tarih": t2}]
    else:
        tarih_listesi = [{"olay": olay1, "tarih": t1}]

    tam_mail = f"Gönderen: {gonderen}\nKonu: {konu}\n\n{govde}"
    cikti = {
        "mail_turu": "aksiyon_gerekli",
        "gonderen": gonderen,
        "oncelik": oncelik,
        "tarihler_ve_terminler": tarih_listesi,
        "yapilacak_isler": [gorev1.capitalize(), gorev2.capitalize()],
        "ozet": ozet,
    }
    examples.append(make_entry(tam_mail, cikti))


# =====================================================================
# 2. BÖLÜM: 600 BİLGİLENDİRME MAİLİ (%30)
# 6 farklı alt-tip × 100 örnek
# =====================================================================

# --- 2a. OAuth / üçüncü taraf uygulama erişimi (İngilizce noreply) ---
servis_adlari = [
    "GitHub", "Google", "GitLab", "Atlassian", "Microsoft", "Figma",
    "Notion", "Slack", "Linear", "Vercel", "Netlify", "Render",
]
uygulama_adlari = [
    "Git Credential Manager", "VS Code Sync", "CI/CD Runner", "OAuth CLI",
    "API Explorer", "Desktop App", "Webhook Manager", "Deploy Bot",
    "Code Review Bot", "Issue Tracker", "Analytics Plugin", "SSO Connector",
]

for i in range(100):
    servis = servis_adlari[i % len(servis_adlari)]
    uygulama = uygulama_adlari[i % len(uygulama_adlari)]
    domain = servis.lower().replace(" ", "")
    gonderen = f"{servis} <noreply@{domain}.com>"
    konu = f"[{servis}] A third-party OAuth application has been added to your account"
    url1 = f"https://{domain}.com/settings/connections/applications/{1000 + i}"
    url2 = f"https://{domain}.com/settings/security-log"
    govde = (
        f"Hey there,\n"
        f"A third-party OAuth application ({uygulama}) was recently authorized to access your account.\n"
        f"Visit {url1} for more information.\n"
        f"To review security events for your account, visit {url2}\n"
        f"If you didn't authorize this application, please revoke access immediately."
    )
    ozet = f"{servis} hesabınıza '{uygulama}' uygulaması için OAuth erişim izni eklendiğine dair otomatik güvenlik bildirimi."
    tam_mail = f"Gönderen: {gonderen}\nKonu: {konu}\n\n{govde}"
    cikti = {"mail_turu": "bilgilendirme", "gonderen": gonderen, "oncelik": "dusuk",
              "tarihler_ve_terminler": [], "yapilacak_isler": [], "ozet": ozet}
    examples.append(make_entry(tam_mail, cikti))

# --- 2b. Yeni cihaz / IP'den giriş güvenlik uyarısı ---
cihaz_turleri = [
    "Windows cihaz", "MacBook Pro", "iPhone", "Android cihaz", "Linux sunucu",
    "Chrome tarayıcı", "Safari tarayıcı", "Firefox", "bilinmeyen cihaz",
]
sehirler = [
    "İstanbul", "Ankara", "İzmir", "Bursa", "Londra", "Berlin", "Amsterdam",
    "Dublin", "Singapur", "Dubai", "New York", "Tokyo",
]

for i in range(100):
    servis = servis_adlari[i % len(servis_adlari)]
    cihaz = cihaz_turleri[i % len(cihaz_turleri)]
    sehir = sehirler[i % len(sehirler)]
    domain = servis.lower().replace(" ", "")
    gonderen = f"{servis} <no-reply@accounts.{domain}.com>"
    konu = f"Güvenlik uyarısı: {sehir} konumundan yeni bir {cihaz} oturumu"
    govde = (
        f"Merhaba,\n"
        f"{servis} hesabınızda {sehir} konumundan bir {cihaz} üzerinden oturum açıldı.\n"
        f"Bu işlemi siz gerçekleştirdiyseniz herhangi bir adım atmanıza gerek yoktur.\n"
        f"Eğer bu işlemi siz yapmadıysanız lütfen şifrenizi hemen değiştirin ve destek ekibiyle iletişime geçin."
    )
    ozet = f"{servis} hesabınıza {sehir} konumundaki {cihaz} üzerinden giriş yapıldığına dair otomatik bilgilendirme."
    tam_mail = f"Gönderen: {gonderen}\nKonu: {konu}\n\n{govde}"
    cikti = {"mail_turu": "bilgilendirme", "gonderen": gonderen, "oncelik": "dusuk",
              "tarihler_ve_terminler": [], "yapilacak_isler": [], "ozet": ozet}
    examples.append(make_entry(tam_mail, cikti))

# --- 2c. Kurumsal duyuru (turnike, yemekhane, NPS, sprint kapanışı) ---
kat_konular = [
    ("Turnike Yenilemesi", "turnike sistemi yenilendi; mevcut kartlarınızla işlem yapmadan geçiş yapabilirsiniz"),
    ("Yemekhane Menüsü Güncellemesi", "yeni haftalık menü sisteme yüklendi, değişiklik gerekmemektedir"),
    ("Park Yeri Düzenlemesi", "B2 katı park yeri düzenlemesi tamamlandı, plakalarınız kayıtlıdır"),
    ("Ofis WiFi Şifre Değişikliği", "kurumsal WiFi şifresi güncellendi, BT ekibinden yeni şifreyi alabilirsiniz"),
    ("Sağlık Sigortası Bilgilendirmesi", "yıllık sağlık sigortası poliçeleriniz yenilendi, değişiklik gerekmemektedir"),
    ("Tatil Takvimi Duyurusu", "2026-2027 resmi tatil takvimi İK sisteminize yüklendi"),
    ("Maaş Bordrosu Hazır", "aylık bordronuz sisteme yüklendi, herhangi bir işlem gerekmemektedir"),
]

for i in range(100):
    kat = (i % 7) + 1
    konu_adi, ozet_metin = kat_konular[i % len(kat_konular)]
    gonderen = "İdari İşler ve Kurumsal İletişim <kurumsal@sirket.com>"
    konu = f"{kat}. Kat / {konu_adi}"
    govde = f"Merhaba,\nBinamızın {kat}. katında {ozet_metin}. Herhangi bir işlem yapmanıza gerek yoktur.\n\nİyi çalışmalar."
    ozet = f"{kat}. kat {konu_adi.lower()} hakkında bilgilendirme; herhangi bir aksiyon gerekmemektedir."
    tam_mail = f"Gönderen: {gonderen}\nKonu: {konu}\n\n{govde}"
    cikti = {"mail_turu": "bilgilendirme", "gonderen": gonderen, "oncelik": "dusuk",
              "tarihler_ve_terminler": [], "yapilacak_isler": [], "ozet": ozet}
    examples.append(make_entry(tam_mail, cikti))

# --- 2d. Yazılım deployment / sistem bakım tamamlandı bildirimi ---
for i in range(100):
    sistem = sistemler[i % len(sistemler)]
    servis = servis_adlari[i % len(servis_adlari)]
    gonderen = f"{servis} DevOps Ekibi <devops-alerts@{servis.lower().replace(' ','')}.com>"
    konu = f"[TAMAMLANDI] {sistem.title()} — Planlı Bakım Bitti"
    govde = (
        f"Merhaba,\n"
        f"Daha önce bildirilen {sistem} planlı bakımı başarıyla tamamlanmıştır. "
        f"Tüm servisler normal çalışmaya devam etmektedir. "
        f"Sorun yaşarsanız destek kanalımıza bildirin."
    )
    ozet = f"{sistem} planlı bakımı tamamlandı; servisler normal şekilde çalışıyor, aksiyon gerekmemektedir."
    tam_mail = f"Gönderen: {gonderen}\nKonu: {konu}\n\n{govde}"
    cikti = {"mail_turu": "bilgilendirme", "gonderen": gonderen, "oncelik": "dusuk",
              "tarihler_ve_terminler": [], "yapilacak_isler": [], "ozet": ozet}
    examples.append(make_entry(tam_mail, cikti))

# --- 2e. Şirket geneli sprint / NPS / anket sonuçları ---
for i in range(100):
    dep = departmanlar[i % len(departmanlar)]
    skor = random.randint(62, 91)
    gonderen = f"Ürün ve Strateji Ekibi <urun@sirket.com>"
    konu = f"Q{(i % 4) + 1} NPS Sonuçları Açıklandı — {dep} Skoru: {skor}"
    govde = (
        f"Merhaba,\n"
        f"{dep} bölümüne ait bu çeyrek NPS skoru {skor} olarak gerçekleşti. "
        f"Detaylı rapor kurumsal dashboard'a yüklendi. "
        f"Raporla ilgili herhangi bir aksiyon almanıza gerek yoktur."
    )
    ozet = f"{dep} Q{(i % 4) + 1} NPS skoru {skor} olarak açıklandı; bilgilendirme amaçlı."
    tam_mail = f"Gönderen: {gonderen}\nKonu: {konu}\n\n{govde}"
    cikti = {"mail_turu": "bilgilendirme", "gonderen": gonderen, "oncelik": "dusuk",
              "tarihler_ve_terminler": [], "yapilacak_isler": [], "ozet": ozet}
    examples.append(make_entry(tam_mail, cikti))

# --- 2f. Abonelik / fiyat değişikliği bilgilendirmesi ---
for i in range(100):
    servis = servis_adlari[i % len(servis_adlari)]
    plan = random.choice(["Pro", "Business", "Enterprise", "Team", "Starter"])
    yeni_fiyat = random.choice([29, 49, 79, 99, 149, 199])
    gonderen = f"{servis} <billing@{servis.lower().replace(' ','')}.com>"
    konu = f"{servis} {plan} Plan Fiyat Güncellemesi — Bilgilendirme"
    govde = (
        f"Merhaba,\n"
        f"{servis} {plan} planınızın aylık ücreti bir sonraki fatura döneminden itibaren "
        f"{yeni_fiyat} USD olarak güncellenecektir. "
        f"Mevcut aboneliğiniz otomatik olarak devam edecektir. "
        f"Planınızı değiştirmek isterseniz hesap ayarlarınızı ziyaret edebilirsiniz."
    )
    ozet = f"{servis} {plan} planı fiyatı {yeni_fiyat} USD'ye güncelleniyor; abonelik otomatik devam edecek."
    tam_mail = f"Gönderen: {gonderen}\nKonu: {konu}\n\n{govde}"
    cikti = {"mail_turu": "bilgilendirme", "gonderen": gonderen, "oncelik": "dusuk",
              "tarihler_ve_terminler": [], "yapilacak_isler": [], "ozet": ozet}
    examples.append(make_entry(tam_mail, cikti))


# =====================================================================
# 3. BÖLÜM: 600 REKLAM / SPAM MAİLİ (%30)
# Gerçek dünya kalıplarına göre 6 alt-tip × 100
# =====================================================================

sentetik_markalar = [
    ("TeknoMarket", "teknomarket"), ("SüperMağaza", "supermagaza"),
    ("ModaTrend", "modatrend"), ("DijitalStore", "dijitalstore"),
    ("MegaElektronik", "megaelektronik"), ("HızlıAlışveriş", "hizlialisveris"),
    ("AkıllıVitrin", "akillivitrin"), ("PremiumMağaza", "premiummag"),
    ("MaxiStore", "maxistore"), ("TrendShop", "trendshop"),
    ("UltraMarket", "ultramarket"), ("GigaMall", "gigamall"),
]

banka_markalari = [
    ("KrediBank", "kredibank"), ("MaxiBank", "maxibank"),
    ("UltraKart", "ultrakart"), ("HızlıPay", "hizlipay"),
    ("FinTekBank", "fintekbank"), ("PremiumKart", "premiumkart"),
]

gonderen_kaliplari = [
    '"{marka} Turkiye" <iletisim@tr.email.{domain}.com>',
    '{marka} <merhaba@email.{domain}.com>',
    '{marka} <updates-noreply@{domain}.com>',
    '{marka} <kampanya@{domain}.com.tr>',
    '{marka} Bülteni <bulten@{domain}-tr.com>',
    '{marka} Night 2026 <event2026@mail01.{domain}.com>',
]

# --- 3a. E-ticaret indirim kampanyaları ---
for i in range(100):
    marka, domain = sentetik_markalar[i % len(sentetik_markalar)]
    gonderen = gonderen_kaliplari[i % len(gonderen_kaliplari)].format(marka=marka, domain=domain)
    indirim = random.choice([20, 25, 30, 40, 50, 60, 70])
    gece = random.choice(gece_saatleri)
    kupon = f"FIRSAT{indirim}"
    konu = f"Son Çağrı: {marka}'da %{indirim} İndirim — Bu Gece {gece}'e Kadar!"
    govde = (
        f"Sayın Üyemiz,\n"
        f"Bu gece {gece}'e kadar {marka} alışverişlerinizde %{indirim} indirim ve "
        f"6 taksit avantajından yararlanın! {kupon} kupon kodunu kullanmayı unutmayın. "
        f"Stoklar sınırlıdır. Kargo bedava. "
        f"Bülten aboneliğinden çıkmak için tıklayınız."
    )
    tam_mail = f"Gönderen: {gonderen}\nKonu: {konu}\n\n{govde}"
    examples.append(make_entry(tam_mail, {"mail_turu": "reklam_spam", "islem": "yoksay"}))

# --- 3b. Banka / kredi kartı puan kampanyaları ---
for i in range(100):
    banka, domain = banka_markalari[i % len(banka_markalari)]
    gonderen = f"{banka} <kampanya@{domain}.com.tr>"
    puan = random.choice([100, 150, 200, 250, 300, 500])
    min_harcama = random.choice([200, 500, 750, 1000, 1500])
    konu = f"Kartına özel {puan} TL puan — {min_harcama} TL alışverişe {puan} TL {banka} puan!"
    govde = (
        f"Merhaba,\n"
        f"{banka} kredi kartıyla bu ay {min_harcama} TL ve üzeri alışveriş yapanlara {puan} TL puan kazandırıyoruz! "
        f"Kampanya son gün. Anlaşmalı kategoriler: market, akaryakıt, restoran ve e-ticaret. "
        f"Yazın STOP'u SMS ile göndererek abonelikten çıkabilirsiniz."
    )
    tam_mail = f"Gönderen: {gonderen}\nKonu: {konu}\n\n{govde}"
    examples.append(make_entry(tam_mail, {"mail_turu": "reklam_spam", "islem": "yoksay"}))

# --- 3c. Konferans / etkinlik bülteni (İngilizce) ---
etkinlik_markalari = [
    ("VizyonSummit", "vizyonsummit"), ("GlobalForum", "globalforum"),
    ("TechExpo", "techexpo"), ("DigitALL", "digitall"),
    ("InnovatEU", "innovateu"), ("CloudCon", "cloudcon"),
]
konferans_konusmalari = [
    "Opening Keynote & Welcome Speech",
    "The Future of AI in Enterprise",
    "Cloud Infrastructure at Scale",
    "Cybersecurity Trends 2026",
    "Young Talent Programme & ICT Cultivation",
    "Panel: Building Resilient Systems",
]

for i in range(100):
    marka, domain = etkinlik_markalari[i % len(etkinlik_markalari)]
    gonderen = f"{marka} 2026 <event2026@mail01.{domain}.com>"
    konu = f"Join Live: {marka} DigitALL Night 2026 — Tonight's Agenda"
    k1 = konferans_konusmalari[i % len(konferans_konusmalari)]
    k2 = konferans_konusmalari[(i + 1) % len(konferans_konusmalari)]
    govde = (
        f"Dear Participant,\n"
        f"17:30 – 19:30 (UTC+2) {marka} DigitALL Night 2026\n"
        f"18:00 Connecting Europe, {k1}\n"
        f"18:45 {k2}\n"
        f"19:00 Networking & Closing\n"
        f"View in browser | Unsubscribe from this list"
    )
    tam_mail = f"Gönderen: {gonderen}\nKonu: {konu}\n\n{govde}"
    examples.append(make_entry(tam_mail, {"mail_turu": "reklam_spam", "islem": "yoksay"}))

# --- 3d. Sosyal ağ / profesyonel ağ bildirimleri ---
sosyal_ag_markalari = [
    ("KariyerAğı", "kariyeragi"), ("ProNetwork", "pronetwork"),
    ("IşBul", "isbul"), ("BaglantiHub", "baglantihub"),
]

for i in range(100):
    marka, domain = sosyal_ag_markalari[i % len(sosyal_ag_markalari)]
    gonderen = f"{marka} <messages-noreply@{domain}.com>"
    gorunum = random.randint(5, 250)
    ilan_sayisi = random.randint(10, 80)
    konu = f"Profilinizi bu hafta {gorunum} kişi görüntüledi — {ilan_sayisi} yeni iş ilanı var"
    govde = (
        f"Merhaba,\n"
        f"Bu hafta profilinizi {gorunum} kişi görüntüledi ve ağınızda {ilan_sayisi} yeni iş ilanı yayımlandı. "
        f"Sponsorlu içerikleri ve yeni bağlantı davetlerini görmek için uygulamayı açın. "
        f"Bildirim ayarlarını değiştirmek için tıklayın."
    )
    tam_mail = f"Gönderen: {gonderen}\nKonu: {konu}\n\n{govde}"
    examples.append(make_entry(tam_mail, {"mail_turu": "reklam_spam", "islem": "yoksay"}))

# --- 3e. Phishing / sahte güvenlik uyarısı ---
phishing_konular = [
    "Hesabınız askıya alındı — 24 saat içinde doğrulayın",
    "Şüpheli giriş denemesi: Hesabınızı hemen güvenli hale getirin",
    "Faturanız bekliyor — Ödeme yapılmazsa hizmetiniz kesilecek",
    "Ödülünüzü talep edin — Hesabınız seçildi",
    "Son uyarı: Bilgilerinizi güncelleyin",
    "Güvenlik ihlali tespit edildi — Şifrenizi hemen değiştirin",
]

for i in range(100):
    marka_adi = random.choice(["Kurumsal Güvenlik Ekibi", "BT Destek Merkezi", "Hesap Yönetimi"])
    gonderen = f"{marka_adi} <noreply@guvenlik-dogrulama-{100+i}.com>"
    konu = phishing_konular[i % len(phishing_konular)]
    govde = (
        f"Sayın Kullanıcı,\n"
        f"{konu.rstrip('.')} tespit edildi. "
        f"Hesabınızın güvenliğini sağlamak için aşağıdaki bağlantıya tıklayarak "
        f"kimliğinizi doğrulamanız gerekmektedir. "
        f"24 saat içinde işlem yapmazsanız hesabınız kalıcı olarak kapatılacaktır."
    )
    tam_mail = f"Gönderen: {gonderen}\nKonu: {konu}\n\n{govde}"
    examples.append(make_entry(tam_mail, {"mail_turu": "reklam_spam", "islem": "yoksay"}))

# --- 3f. Kurumsal fırsat / indirimli SaaS teklifi (trap) ---
saas_markalari = [
    ("BulutDepo", "bulutdepo"), ("ProAnalitik", "proanalitik"),
    ("HızlıERP", "hizlierp"), ("AkıllıCRM", "akillicrm"),
    ("DataVizyon", "datavizyon"), ("KloudSuite", "kloudsuite"),
]

for i in range(100):
    marka, domain = saas_markalari[i % len(saas_markalari)]
    indirim = random.choice([20, 30, 40])
    plan = random.choice(["Kurumsal", "Pro", "Business", "Enterprise"])
    gonderen = f"{marka} Satış Ekibi <satis@{domain}.io>"
    konu = f"Sadece Bu Hafta: {marka} {plan} Planında %{indirim} Kurumsal İndirim"
    govde = (
        f"Sayın Yetkili,\n"
        f"{marka} {plan} planında bu hafta sonu sona erecek özel fırsatımızdan yararlanarak "
        f"%{indirim} indirimli fiyata lisans satın alabilirsiniz. "
        f"10 kullanıcıya kadar ücretsiz deneme ve sınırsız destek dahildir. "
        f"Detaylar için temsilcinizle iletişime geçin veya bu bültenden çıkmak için tıklayın."
    )
    tam_mail = f"Gönderen: {gonderen}\nKonu: {konu}\n\n{govde}"
    examples.append(make_entry(tam_mail, {"mail_turu": "reklam_spam", "islem": "yoksay"}))


# ── Karıştır ve kaydet ────────────────────────────────────────────────────────
random.shuffle(examples)

os.makedirs("data", exist_ok=True)
output_path = os.path.join("data", "mail_egitim.jsonl")

with open(output_path, "w", encoding="utf-8") as f:
    for entry in examples:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

boyut_kb = os.path.getsize(output_path) / 1024
print(f"Toplam {len(examples)} adet Isci egitim ornegi '{output_path}' dosyasina yazildi ({boyut_kb:.1f} KB).")
