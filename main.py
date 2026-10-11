import os
import json
from datetime import datetime
from agents.mail_agent import MailAgent
from agents.hakem_agent import HakemAgent
from agents.cikti_agent import CiktiAgent


class CokluAjanMailSistemi:
    def __init__(self):
        print("⏳ Akıllı Yönetici Asistanı hazırlanıyor...")
        self.isci = MailAgent()
        self.hakem = HakemAgent(
            ortak_model=self.isci.model,
            ortak_tokenizer=self.isci.tokenizer
        )
        self.cikti = CiktiAgent(
            ortak_model=self.isci.model,
            ortak_tokenizer=self.isci.tokenizer
        )

    def baska_ajandan_veri_ekle(self, departman_adi: str, veri: dict | list | str):
        """
        İleride eklenecek Muhasebe Ajanı, İK Ajanı vb. ajanların çıktılarını
        doğrudan Çıktı/Sunum Ajanına bağlamak için kullanılır.
        """
        self.cikti.departman_verisi_ekle(departman_adi, veri)

    def tek_mail_analiz_et(self, mail_metni: str, gonderim_tarihi: datetime = None) -> dict:
        isci_json = self.isci.analiz_et(mail_metni)
        onayli_json = self.hakem.denetle(mail_metni, isci_json)
        zaman_paketi = self.cikti.analiz_ve_zaman_hesapla(
            onayli_json,
            mail_metni,
            mail_gonderim_tarihi=gonderim_tarihi
        )
        return {
            "mail_metni": mail_metni,
            "gonderim_tarihi": gonderim_tarihi,
            "onayli_json": onayli_json,
            "durum": zaman_paketi["durum"],
            "siralama_puani": zaman_paketi["siralama_puani"]
        }

    def panoyu_yazdir(self, sonuclar: list[dict]):
        sirali_liste = sorted(sonuclar, key=lambda x: x["siralama_puani"])

        aktif_mailler = [x for x in sirali_liste if x["durum"] in ("aksiyon_gerekli", "bilgilendirme")]
        gizlenen_mailler = [x for x in sirali_liste if x["durum"] in ("eski_arsiv", "reklam_spam")]

        # Çıktı ajanının hafızasını güncelle (sohbet ve özet için)
        self.cikti.hafizayi_guncelle(aktif_mailler, gizlenen_mailler)

        aksiyon_sayisi = sum(1 for x in sirali_liste if x["durum"] == "aksiyon_gerekli")
        bilgi_sayisi = sum(1 for x in sirali_liste if x["durum"] == "bilgilendirme")
        arsiv_sayisi = sum(1 for x in sirali_liste if x["durum"] == "eski_arsiv")
        spam_sayisi = sum(1 for x in sirali_liste if x["durum"] == "reklam_spam")

        print("\n" + "═" * 74)
        print("📬 AKILLI YÖNETİCİ ASİSTANI  •  ÖNCELİK SIRALI GÜNLÜK BRİFİNG")
        print(f"🕒 Sistem Zamanı : {self.cikti.sistem_zaman_metni()}")
        print(
            f"📊 Gelen Kutusu  : {len(sonuclar)} E-Posta İncelendi  "
            f"(🚨 {aksiyon_sayisi} Acil İş | ℹ️ {bilgi_sayisi} Bilgi | 🗄️ {arsiv_sayisi} Arşiv | 🚫 {spam_sayisi} Spam)"
        )
        print("═" * 74)

        # Saate duyarlı (Günaydın / İyi akşamlar / İyi geceler) samimi karşılama özeti
        print("\n" + self.cikti.sohbet_tarzi_acilis_ozeti() + "\n")
        print("─" * 74 + "\n")

        for oncelik_no, item in enumerate(aktif_mailler, 1):
            kart = self.cikti.raporla(
                item["onayli_json"],
                item["mail_metni"],
                mail_gonderim_tarihi=item["gonderim_tarihi"],
                sira_no=oncelik_no
            )
            print(kart)
            print()

        # Başka ajanlardan (Muhasebe vb.) gelen raporlar varsa göster
        if self.cikti.hafiza["departman_raporlari"]:
            print("┌────────────────────────────────────────────────────────────────────────┐")
            print("│ 📊 DİĞER DEPARTMAN AJANLARINDAN GELEN ÖZETLER                          │")
            print("└────────────────────────────────────────────────────────────────────────┘")
            for dep_adi, dep_veri in self.cikti.hafiza["departman_raporlari"].items():
                print(f"  🔹 [{dep_adi} Ajanı]: {dep_veri}")
            print()

        if gizlenen_mailler:
            print("┌────────────────────────────────────────────────────────────────────────┐")
            print("│ 🧹 OTOMATİK GİZLENENLER (VAKTİ GEÇMİŞ ARŞİV & SPAM E-POSTALAR)        │")
            print("└────────────────────────────────────────────────────────────────────────┘")
            for item in gizlenen_mailler:
                satir = self.cikti.raporla(
                    item["onayli_json"],
                    item["mail_metni"],
                    mail_gonderim_tarihi=item["gonderim_tarihi"]
                )
                print(satir)
            print("═" * 74)

    def canli_sohbet_baslat(self):
        """Brifing sonrasında kullanıcıyla interaktif sohbet döngüsü başlatır."""
        print("\n💬 Asistanınızla Sohbet Edebilirsiniz (Çıkmak için 'q' veya 'çık' yazın)")
        print("   Örnek: 'Nasılsın?', 'Bugün en acil işim ne?', 'Haluk Bey ne istemişti?'\n")
        while True:
            try:
                soru = input("👤 Siz      : ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n👋 İyi çalışmalar dilerim!")
                break

            if not soru:
                continue
            if soru.lower() in ("q", "quit", "exit", "çık", "cik", "kapat"):
                selam, _ = self.cikti.vakit_selami_getir()
                print(f"🤖 Asistan  : Görüşmek üzere! {selam}")
                break

            yanit = self.cikti.sohbet_et(soru)
            print(f"🤖 Asistan  : {yanit}\n")

    def json_dosyasindan_calistir(self, dosya_yolu: str, sohbet_aktif: bool = True):
        if not os.path.exists(dosya_yolu):
            raise FileNotFoundError(f"Dosya bulunamadı: {dosya_yolu}")

        with open(dosya_yolu, "r", encoding="utf-8") as f:
            kayitlar = json.load(f)

        print(f"🔍 {len(kayitlar)} e-posta analiz ediliyor ve aciliyet sırasına diziliyor...")
        sonuclar = []
        for kayit in kayitlar:
            analiz = self.tek_mail_analiz_et(kayit["mail_metni"])
            sonuclar.append(analiz)

        self.panoyu_yazdir(sonuclar)

        if sohbet_aktif:
            self.canli_sohbet_baslat()


if __name__ == "__main__":
    proje_ana_dizin = os.path.dirname(os.path.abspath(__file__))
    test_json_yolu = os.path.join(proje_ana_dizin, "data", "ornek_mailler_test.json")

    sistem = CokluAjanMailSistemi()

    # İleride Muhasebe Ajanı eklendiğinde tek satırla şöyle bağlanacak:
    # sistem.baska_ajandan_veri_ekle("Muhasebe", {"bekleyen_fatura": 2, "toplam_odeme": "145.000 TL", "durum": "Nakit akışı dengeli"})

    sistem.json_dosyasindan_calistir(test_json_yolu, sohbet_aktif=True)
