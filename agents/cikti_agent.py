import re
import json
import textwrap
from datetime import datetime, timedelta
import torch

TURKCE_AYLAR = {
    "ocak": 1, "şubat": 2, "subat": 2, "mart": 3, "nisan": 4,
    "mayıs": 5, "mayis": 5, "haziran": 6, "temmuz": 7, "ağustos": 8, "agustos": 8,
    "eylül": 9, "eylul": 9, "ekim": 10, "kasım": 11, "kasim": 11, "aralık": 12, "aralik": 12
}

TURKCE_GUNLER = {
    "pazartesi": 0, "salı": 1, "sali": 1, "çarşamba": 2, "carsamba": 2,
    "perşembe": 3, "persembe": 3, "cuma": 4, "cumartesi": 5, "pazar": 6
}

AY_ISIMLERI = [
    "", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
    "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"
]

GUN_ISIMLERI = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]

ARSIV_SINIRI_GUN = 7


class CiktiAgent:
    """
    Merkezi Sunucu, Zaman Çözümleyici ve Yönetici Sohbet Asistanı Ajanı.
    - Hem Mail Ajanlarından hem de diğer ajanlardan (Muhasebe, Takvim vb.) gelen verileri toplar.
    - Saate duyarlı (Günaydın / İyi akşamlar / İyi geceler) doğal brifing sunar.
    - Ortak modelin LoRA kilidini geçici olarak devre dışı bırakarak (0 ek VRAM ile)
      kullanıcıyla doğal Türkçe sohbet eder ve soruları yanıtlar.
    """

    def __init__(self, ortak_model=None, ortak_tokenizer=None):
        self.model = ortak_model
        self.tokenizer = ortak_tokenizer
        # Çoklu ajan veri havuzu (Mail, Muhasebe, İK vb. tüm ajanlar buraya veri bırakabilir)
        self.hafiza = {
            "aktif_mailler": [],
            "gizlenen_mailler": [],
            "departman_raporlari": {}  # Örn: {"Muhasebe": {...}, "Takvim": {...}}
        }
        self.sohbet_gecmisi = []

    def sistem_zaman_metni(self) -> str:
        simdi = datetime.now()
        gun_adi = GUN_ISIMLERI[simdi.weekday()]
        return f"{simdi.day} {AY_ISIMLERI[simdi.month]} {simdi.year} {gun_adi}, {simdi.strftime('%H:%M')}"

    def vakit_selami_getir(self) -> tuple[str, str]:
        """Günün saatine göre uygun selamlama ve açılış cümlesi döndürür."""
        saat = datetime.now().hour
        if 6 <= saat < 12:
            return (
                "Günaydın! ☀️",
                "Sabah kahvenizi içerken güne hızlıca başlayabilmeniz için gelen kutunuzu ve şirket verilerinizi inceledim."
            )
        elif 12 <= saat < 18:
            return (
                "İyi günler! 🌤️",
                "Gün ortası itibarıyla gelen kutunuzu ve departman özetlerinizi aciliyet sırasına göre derledim."
            )
        elif 18 <= saat < 22:
            return (
                "İyi akşamlar! 🌆",
                "Günü kapatırken gözden kaçmaması gereken kritik başlıkları ve yarına sarkan işleri sizin için özetledim."
            )
        else:
            return (
                "İyi geceler! 🌙",
                "Geç bir saatteyiz; sizi yormadan sadece en acil bilmeniz gereken noktaları ve günlük özetinizi paylaşıyorum."
            )

    def departman_verisi_ekle(self, departman_adi: str, veri: dict | list | str):
        """
        Başka ajanlardan (Örn: Muhasebe Ajanı, İK Ajanı, Stok Ajanı) gelen verileri
        asistanın merkezi hafızasına ekler.
        """
        self.hafiza["departman_raporlari"][departman_adi] = veri

    def hafizayi_guncelle(self, aktif_mailler: list[dict], gizlenen_mailler: list[dict]):
        """Analiz edilen e-postaları sohbet sırasında sorulabilmesi için hafızaya kaydeder."""
        self.hafiza["aktif_mailler"] = aktif_mailler
        self.hafiza["gizlenen_mailler"] = gizlenen_mailler

    def konu_ayikla(self, orijinal_mail: str) -> str:
        if not orijinal_mail:
            return "Konu Belirtilmemiş"
        eslesme = re.search(r"^Konu:\s*(.+)$", orijinal_mail, flags=re.MULTILINE | re.IGNORECASE)
        if eslesme:
            return eslesme.group(1).strip()
        return "Kurumsal E-Posta"

    def turkce_tarih_cozumle(self, tarih_metni: str, orijinal_mail: str = "", referans_zaman: datetime = None) -> datetime | None:
        if referans_zaman is None:
            referans_zaman = datetime.now()

        if not tarih_metni:
            tarih_metni = ""

        kucuk = tarih_metni.lower().strip()
        birlesik_metin = (tarih_metni + " " + orijinal_mail).lower()

        saat, dakika = 17, 0
        saat_eslesme = re.search(r"\b([01]?\d|2[0-3]):([0-5]\d)\b", kucuk)
        if saat_eslesme:
            saat = int(saat_eslesme.group(1))
            dakika = int(saat_eslesme.group(2))
        elif "sabah" in kucuk:
            saat, dakika = 9, 0
        elif "öğle" in kucuk or "ogle" in kucuk:
            saat, dakika = 12, 0
        elif "akşam" in kucuk or "aksam" in kucuk:
            saat, dakika = 19, 0
        elif "gece" in kucuk:
            saat, dakika = 23, 0

        yil = referans_zaman.year
        yil_eslesme = re.search(r"\b(20\d{2})\b", kucuk)
        if yil_eslesme:
            yil = int(yil_eslesme.group(1))
        else:
            mail_yillari = [int(y) for y in re.findall(r"\b(202[0-9])\b", birlesik_metin)]
            eski_yillar = [y for y in mail_yillari if y < referans_zaman.year]
            if eski_yillar:
                yil = min(eski_yillar)

        noktali = re.search(r"\b(\d{1,2})[./](\d{1,2})[./](20\d{2})\b", birlesik_metin)
        if noktali:
            g, a, y = int(noktali.group(1)), int(noktali.group(2)), int(noktali.group(3))
            try:
                return datetime(y, a, g, saat, dakika)
            except ValueError:
                pass

        for ay_adi, ay_no in TURKCE_AYLAR.items():
            eslesme = re.search(rf"\b(\d{{1,2}})\s+{ay_adi}\b", kucuk)
            if not eslesme:
                eslesme = re.search(rf"\b(\d{{1,2}})\s+{ay_adi}\b", birlesik_metin)
            if eslesme:
                gun_no = int(eslesme.group(1))
                try:
                    return datetime(yil, ay_no, gun_no, saat, dakika)
                except ValueError:
                    pass

        if yil < referans_zaman.year:
            return datetime(yil, referans_zaman.month, referans_zaman.day, saat, dakika)

        if any(k in kucuk for k in ["bugün", "bugun", "bu akşam", "bu aksam", "bu gece"]):
            return datetime(referans_zaman.year, referans_zaman.month, referans_zaman.day, saat, dakika)

        if "yarın" in kucuk or "yarin" in kucuk:
            yarin = referans_zaman + timedelta(days=1)
            return datetime(yarin.year, yarin.month, yarin.day, saat, dakika)

        for gun_adi, hedef_weekday in TURKCE_GUNLER.items():
            if gun_adi in kucuk:
                fark = (hedef_weekday - referans_zaman.weekday()) % 7
                if fark == 0:
                    aday = datetime(referans_zaman.year, referans_zaman.month, referans_zaman.day, saat, dakika)
                    if aday < referans_zaman:
                        fark = 7
                hedef_gun = referans_zaman + timedelta(days=fark)
                return datetime(hedef_gun.year, hedef_gun.month, hedef_gun.day, saat, dakika)

        return None

    def kalan_sure_etiketi(self, hedef_dt: datetime, referans_zaman: datetime = None) -> tuple[str, float]:
        if referans_zaman is None:
            referans_zaman = datetime.now()

        fark = hedef_dt - referans_zaman
        toplam_saat = fark.total_seconds() / 3600.0
        gun_farki = fark.days

        if toplam_saat < -24 * ARSIV_SINIRI_GUN:
            gecen_gun = abs(gun_farki)
            if gecen_gun >= 365:
                return f"{gecen_gun // 365} Yıl Önce Geçti", toplam_saat
            return f"{gecen_gun} Gün Önce Geçti", toplam_saat
        elif toplam_saat < 0:
            gecen_saat = int(abs(toplam_saat))
            if gecen_saat < 24:
                return f"Süresi {gecen_saat} Saat Önce Doldu", toplam_saat
            return f"Süresi {abs(gun_farki)} Gün Önce Doldu", toplam_saat
        elif toplam_saat <= 24:
            kalan_saat = max(1, int(toplam_saat))
            return f"{kalan_saat} Saat Kaldı", toplam_saat
        elif toplam_saat <= 72:
            kalan_g = int(toplam_saat // 24)
            kalan_s = int(toplam_saat % 24)
            return f"{kalan_g} Gün {kalan_s} Saat Kaldı", toplam_saat
        else:
            kalan_g = int(toplam_saat // 24)
            return f"{kalan_g} Gün Kaldı", toplam_saat

    def _gorev_temizle(self, gorev: str) -> str:
        temiz = re.sub(r"(\b.+?kadar)\s+\1", r"\1", gorev, flags=re.IGNORECASE).strip()
        temiz = re.sub(r"^.+?\b(saatine|tarihine)\s+kadar\s+", "", temiz, flags=re.IGNORECASE).strip()
        if temiz:
            temiz = temiz[0].upper() + temiz[1:]
        return temiz

    def analiz_ve_zaman_hesapla(
        self,
        dogrulanmis_json: dict,
        orijinal_mail: str = "",
        mail_gonderim_tarihi: datetime = None
    ) -> dict:
        simdi = datetime.now()
        referans_takvim = mail_gonderim_tarihi if mail_gonderim_tarihi is not None else simdi
        tur = dogrulanmis_json.get("mail_turu", "")
        konu = self.konu_ayikla(orijinal_mail)

        if tur == "reklam_spam":
            return {
                "durum": "reklam_spam",
                "konu": konu,
                "siralama_puani": 999999,
                "json": dogrulanmis_json
            }

        mail_yasi_saat = (simdi - referans_takvim).total_seconds() / 3600.0
        tarihler = dogrulanmis_json.get("tarihler_ve_terminler", [])
        zengin_tarihler = []
        en_yakin_saat = 99999.0
        hepsi_cok_eski = False

        if tarihler:
            eski_sayisi = 0
            for t in tarihler:
                t_metin = t.get("tarih", "")
                cozulen_dt = self.turkce_tarih_cozumle(t_metin, orijinal_mail, referans_takvim)
                if cozulen_dt:
                    etiket, saat_farki = self.kalan_sure_etiketi(cozulen_dt, simdi)
                    if saat_farki < -24 * ARSIV_SINIRI_GUN:
                        eski_sayisi += 1
                    if saat_farki < en_yakin_saat:
                        en_yakin_saat = saat_farki
                    zengin_tarihler.append({
                        "olay": t.get("olay", "-"),
                        "tarih": t_metin,
                        "gercek_tarih": cozulen_dt.strftime("%d.%m.%Y %H:%M"),
                        "zaman_etiketi": etiket,
                        "saat_farki": saat_farki
                    })
                else:
                    if mail_yasi_saat > 24 * ARSIV_SINIRI_GUN:
                        eski_sayisi += 1
                    zengin_tarihler.append({
                        "olay": t.get("olay", "-"),
                        "tarih": t_metin,
                        "gercek_tarih": "-",
                        "zaman_etiketi": "Tarih Belirsiz",
                        "saat_farki": 5000.0
                    })
            if eski_sayisi == len(tarihler) and len(tarihler) > 0:
                hepsi_cok_eski = True
        else:
            cozulen_dt = self.turkce_tarih_cozumle("", orijinal_mail, referans_takvim)
            if cozulen_dt:
                _, saat_farki = self.kalan_sure_etiketi(cozulen_dt, simdi)
                if saat_farki < -24 * ARSIV_SINIRI_GUN:
                    hepsi_cok_eski = True
                    en_yakin_saat = saat_farki
            elif mail_yasi_saat > 24 * ARSIV_SINIRI_GUN and tur == "aksiyon_gerekli":
                hepsi_cok_eski = True
                en_yakin_saat = -mail_yasi_saat

        if hepsi_cok_eski:
            return {
                "durum": "eski_arsiv",
                "konu": konu,
                "siralama_puani": 888888,
                "en_yakin_saat": en_yakin_saat,
                "zengin_tarihler": zengin_tarihler,
                "json": dogrulanmis_json
            }

        gecerli_tarihler = [t for t in zengin_tarihler if t["gercek_tarih"] != "-"]
        if gecerli_tarihler:
            zengin_tarihler = gecerli_tarihler

        tekil_tarihler = []
        gorulen_tarih_anahtarlari = set()
        for t in zengin_tarihler:
            anahtar = t["gercek_tarih"] if t["gercek_tarih"] != "-" else t["tarih"].lower().strip()
            if anahtar not in gorulen_tarih_anahtarlari:
                gorulen_tarih_anahtarlari.add(anahtar)
                tekil_tarihler.append(t)
        zengin_tarihler = tekil_tarihler
        zengin_tarihler.sort(key=lambda x: x["saat_farki"])

        ham_gorevler = dogrulanmis_json.get("yapilacak_isler", [])
        temiz_gorevler = []
        for g in ham_gorevler:
            if not isinstance(g, str):
                continue
            g_temiz = self._gorev_temizle(g)
            norm = g_temiz.lower()
            if g_temiz and not any(norm in mevcut.lower() or mevcut.lower() in norm for mevcut in temiz_gorevler):
                temiz_gorevler.append(g_temiz)
        dogrulanmis_json["yapilacak_isler"] = temiz_gorevler

        oncelik = dogrulanmis_json.get("oncelik", "orta").lower()
        if en_yakin_saat <= 24:
            oncelik = "kritik_acil"

        siralama_puani = en_yakin_saat if tur == "aksiyon_gerekli" else 50000.0
        return {
            "durum": tur,
            "konu": konu,
            "oncelik_guncel": oncelik,
            "siralama_puani": siralama_puani,
            "en_yakin_saat": en_yakin_saat,
            "zengin_tarihler": zengin_tarihler,
            "json": dogrulanmis_json
        }

    def _dogal_ozet(self, analiz_paketi: dict) -> str:
        veri = analiz_paketi["json"]
        gonderen = veri.get("gonderen", "İlgili kişi")
        gorevler = veri.get("yapilacak_isler", [])
        z_tarihler = analiz_paketi.get("zengin_tarihler", [])

        parcalar = [f"{gonderen} tarafından gönderilen bu e-postada"]
        if z_tarihler:
            ilk_t = z_tarihler[0]
            parcalar.append(f"en yakın termin {ilk_t['tarih']} ({ilk_t['gercek_tarih']}) olarak belirlenmiştir.")
        else:
            parcalar.append("yapılması gereken işlemler bulunmaktadır.")

        if gorevler:
            gorev_metni = " ve ".join([f"'{g}'" for g in gorevler])
            parcalar.append(f"Beklenen aksiyonlar: {gorev_metni}.")

        return " ".join(parcalar)

    def sohbet_tarzi_acilis_ozeti(self) -> str:
        """
        Günün saatine göre (Günaydın / İyi geceler vb.) sıcak bir karşılama ve
        tüm ajanlardan (Mail + Muhasebe vb.) gelen verilerin samimi bir yönetici özetini üretir.
        """
        selam, giris_cumlesi = self.vakit_selami_getir()
        aktif = self.hafiza["aktif_mailler"]
        gizlenen = self.hafiza["gizlenen_mailler"]
        departmanlar = self.hafiza["departman_raporlari"]

        aksiyonlar = [x for x in aktif if x["durum"] == "aksiyon_gerekli"]
        bilgiler = [x for x in aktif if x["durum"] == "bilgilendirme"]
        spam_sayisi = sum(1 for x in gizlenen if x["durum"] == "reklam_spam")
        arsiv_sayisi = sum(1 for x in gizlenen if x["durum"] == "eski_arsiv")

        paragraf = [f"🤖 ASİSTANIN GÜNLÜK SOHBET ÖZETİ:\n   \"{selam} {giris_cumlesi}"]

        if spam_sayisi > 0 or arsiv_sayisi > 0:
            temizlik = []
            if spam_sayisi > 0:
                temizlik.append(f"{spam_sayisi} reklam/bülten mailini")
            if arsiv_sayisi > 0:
                temizlik.append(f"vakti geçmiş {arsiv_sayisi} eski maili")
            paragraf.append(f"Öncelikle sizi meşgul etmemesi için {' ve '.join(temizlik)} otomatik olarak eledim.")

        if aksiyonlar:
            ilk = aksiyonlar[0]
            ilk_paket = self.analiz_ve_zaman_hesapla(ilk["onayli_json"], ilk["mail_metni"], ilk["gonderim_tarihi"])
            ilk_gonderen = ilk["onayli_json"].get("gonderen", "Bir gönderici")
            ilk_konu = ilk_paket["konu"]
            kalan = ilk_paket["zengin_tarihler"][0]["zaman_etiketi"] if ilk_paket["zengin_tarihler"] else "yakın zamanda"
            paragraf.append(
                f"Şu an önünüzde aksiyon bekleyen {len(aksiyonlar)} önemli iş e-postası var. "
                f"En acili {ilk_gonderen} tarafından gönderilen '{ilk_konu}' konulu e-posta ({kalan})."
            )
        else:
            paragraf.append("Gelen kutunuzda acil aksiyon gerektiren hiçbir iş e-postası bulunmuyor, rahat bir nefes alabilirsiniz!")

        if bilgiler:
            paragraf.append(f"Ayrıca sadece bilgi amaçlı {len(bilgiler)} kurumsal duyurunuz mevcut.")

        if departmanlar:
            dep_isimleri = ", ".join(departmanlar.keys())
            paragraf.append(f"Ek olarak {dep_isimleri} ajanlarından gelen güncel veriler de sisteme işlendi.")

        paragraf.append("Detayları aşağıda görebilir veya bana istediğiniz soruyu sorabilirsiniz!\"")
        tam_metin = " ".join(paragraf)
        return "\n   ".join(textwrap.wrap(tam_metin, width=72, replace_whitespace=False))

    def _hafiza_baglami_olustur(self) -> str:
        """Modelin sorulara doğru cevap verebilmesi için eldeki tüm veriyi özet bir metne çevirir."""
        satirlar = [f"Sistem Tarihi ve Saati: {self.sistem_zaman_metni()}"]

        aktif = self.hafiza["aktif_mailler"]
        gizlenen = self.hafiza["gizlenen_mailler"]
        satirlar.append(f"Toplam İncelenen Mail: {len(aktif) + len(gizlenen)} (Aktif: {len(aktif)}, Gizlenen Spam/Arşiv: {len(gizlenen)})")

        if aktif:
            satirlar.append("\n[AKTİF E-POSTALAR VE GÖREVLER]:")
            for idx, item in enumerate(aktif, 1):
                paket = self.analiz_ve_zaman_hesapla(item["onayli_json"], item["mail_metni"], item["gonderim_tarihi"])
                veri = paket["json"]
                konu = paket["konu"]
                gonderen = veri.get("gonderen", "Bilinmiyor")
                tur = paket["durum"]
                tarihler = ", ".join([f"{t['olay']}: {t['tarih']} ({t['gercek_tarih']} - {t['zaman_etiketi']})" for t in paket["zengin_tarihler"]]) or "Tarih yok"
                gorevler = ", ".join(veri.get("yapilacak_isler", [])) or "Görev yok"
                ozet = veri.get("ozet", "")
                satirlar.append(
                    f"{idx}. Tür: {tur} | Gönderen: {gonderen} | Konu: {konu} | "
                    f"Terminler: {tarihler} | Yapılacaklar: {gorevler} | Özet: {ozet}"
                )

        if self.hafiza["departman_raporlari"]:
            satirlar.append("\n[DİĞER AJANLARDAN GELEN VERİLER (MUHASEBE / İK / TAKVİM)]:")
            for dep_adi, dep_veri in self.hafiza["departman_raporlari"].items():
                if isinstance(dep_veri, (dict, list)):
                    veri_str = json.dumps(dep_veri, ensure_ascii=False)
                else:
                    veri_str = str(dep_veri)
                satirlar.append(f"- {dep_adi} Ajanı Raporu: {veri_str}")

        return "\n".join(satirlar)

    def sohbet_et(self, kullanici_sorusu: str) -> str:
        """
        Ortak modelin JSON LoRA adaptörlerini geçici olarak devre dışı bırakıp (0 ek VRAM!),
        temel Qwen2.5-Instruct modeliyle doğal Türkçe sohbet ve soru-cevap yapar.
        """
        if self.model is None or self.tokenizer is None:
            return "Model bağlı olmadığı için şu an yalnızca özet gösterebiliyorum."

        baglam = self._hafiza_baglami_olustur()
        selam, _ = self.vakit_selami_getir()

        sistem_mesaji = (
            "Sen kibar, zeki ve samimi bir Türkçe Yönetici Asistanısın (Çıktı ve İletişim Ajanı). "
            "Kullanıcı senin yöneticin. Onunla doğal, sıcak ve akıcı bir Türkçe ile konuş. "
            "KESİNLİKLE JSON formatında çıktı verme, normal insan gibi sohbet et ve sadece Türkçe karakterler kullan. "
            "Eğer 'nasılsın', 'ne haber', 'günaydın' gibi günlük sohbet soruları sorarsa samimi şekilde hal hatır sorarak cevap ver. "
            "Eğer e-postalar, yapılacak işler, saatler veya muhasebe/departman verileri hakkında soru sorarsa "
            "sadece aşağıdaki güncel brifing verilerine dayanarak net ve doğru cevap ver:\n\n"
            f"{baglam}"
        )

        mesajlar = [{"role": "system", "content": sistem_mesaji}]
        # Son 4 mesajlık geçmişi ekle
        for gecmis in self.sohbet_gecmisi[-4:]:
            mesajlar.append(gecmis)
        mesajlar.append({"role": "user", "content": kullanici_sorusu})

        metin = self.tokenizer.apply_chat_template(
            mesajlar,
            tokenize=False,
            add_generation_prompt=True
        )
        girisler = self.tokenizer(metin, return_tensors="pt").to(self.model.device)

        # LoRA adaptörlerini (JSON kilidini) geçici olarak kapatıyoruz -> Orijinal sohbet modeli uyanır!
        with torch.no_grad():
            if hasattr(self.model, "disable_adapter"):
                with self.model.disable_adapter():
                    cikti_ids = self.model.generate(
                        **girisler,
                        max_new_tokens=220,
                        do_sample=True,
                        temperature=0.4,
                        top_p=0.9,
                        repetition_penalty=1.1,
                        pad_token_id=self.tokenizer.eos_token_id
                    )
            else:
                cikti_ids = self.model.generate(
                    **girisler,
                    max_new_tokens=220,
                    do_sample=True,
                    temperature=0.4,
                    top_p=0.9,
                    pad_token_id=self.tokenizer.eos_token_id
                )

        yanit = self.tokenizer.decode(
            cikti_ids[0][girisler["input_ids"].shape[1]:],
            skip_special_tokens=True
        ).strip()

        # Olası yabancı karakter (Çince vb.) sızıntılarını temizle
        yanit = re.sub(r"[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]+", "", yanit).strip()

        self.sohbet_gecmisi.append({"role": "user", "content": kullanici_sorusu})
        self.sohbet_gecmisi.append({"role": "assistant", "content": yanit})
        return yanit

    def raporla(
        self,
        dogrulanmis_json: dict,
        orijinal_mail: str = "",
        mail_gonderim_tarihi: datetime = None,
        sira_no: int = None
    ) -> str:
        paket = self.analiz_ve_zaman_hesapla(dogrulanmis_json, orijinal_mail, mail_gonderim_tarihi)
        durum = paket["durum"]
        veri = paket["json"]
        konu = paket["konu"]
        gonderen = veri.get("gonderen", "Bilinmiyor")
        sira_etiketi = f"#{sira_no} " if sira_no is not None else ""

        if durum == "reklam_spam":
            return f"   🚫 [SPAM ENGELLENDİ] {konu}"

        if durum == "eski_arsiv":
            eski_bilgi = paket["zengin_tarihler"][0]["zaman_etiketi"] if paket["zengin_tarihler"] else "Tarihi Geçmiş"
            return f"   🗄️  [ARŞİVLENDİ - {eski_bilgi}] {konu} ({gonderen})"

        if durum == "bilgilendirme":
            ozet = veri.get("ozet", "Bilgilendirme amaçlı duyuru.")
            ozet = re.sub(r"[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]+", "", ozet).strip()
            sarili_ozet = "\n     ".join(textwrap.wrap(ozet, width=66))
            return (
                "┌────────────────────────────────────────────────────────────────────────┐\n"
                f"│ ℹ️  {sira_etiketi}BİLGİLENDİRME DUYURUSU                                              │\n"
                "└────────────────────────────────────────────────────────────────────────┘\n"
                f"  📌 Konu     : {konu}\n"
                f"  👤 Gönderen : {gonderen}\n"
                f"  📝 Özet     : {sarili_ozet}\n"
                "  ✅ Durum    : Herhangi bir aksiyon almanıza gerek yoktur."
            )

        oncelik = paket["oncelik_guncel"]
        zengin_tarihler = paket["zengin_tarihler"]
        kalan_rozet = zengin_tarihler[0]["zaman_etiketi"] if zengin_tarihler else "Süre Belirtilmedi"

        if oncelik == "kritik_acil":
            seviye_baslik = f"🔴 {sira_etiketi}KRİTİK ACİL  •  ⏱️ {kalan_rozet.upper()}"
        elif oncelik == "yuksek":
            seviye_baslik = f"🟠 {sira_etiketi}YÜKSEK ÖNCELİK  •  ⏳ {kalan_rozet}"
        elif oncelik == "orta":
            seviye_baslik = f"🟡 {sira_etiketi}ORTA ÖNCELİK  •  ⏳ {kalan_rozet}"
        else:
            seviye_baslik = f"🟢 {sira_etiketi}DÜŞÜK ÖNCELİK  •  ⏳ {kalan_rozet}"

        gorevler = veri.get("yapilacak_isler", [])
        dogal_ozet = self._dogal_ozet(paket)
        sarili_ozet = "\n     ".join(textwrap.wrap(dogal_ozet, width=66))

        satirlar = [
            "┌────────────────────────────────────────────────────────────────────────┐",
            f"│ {seviye_baslik:<70} │",
            "└────────────────────────────────────────────────────────────────────────┘",
            f"  📌 Konu     : {konu}",
            f"  👤 Gönderen : {gonderen}",
            "",
            "  📅 Takvim ve Terminler:"
        ]

        if zengin_tarihler:
            for t in zengin_tarihler:
                satirlar.append(
                    f"     • [{t['gercek_tarih']}] {t['tarih']} ({t['zaman_etiketi']}) ➔ {t['olay']}"
                )
        else:
            satirlar.append("     • Belirtilmiş net bir tarih yok.")

        satirlar.append("\n  ☑️  Yapılacak İşler:")
        if gorevler:
            for idx, g in enumerate(gorevler, 1):
                satirlar.append(f"     {idx}. [ ] {g}")
        else:
            satirlar.append("     • Belirtilmiş görev yok.")

        satirlar.append(f"\n  💬 Asistan Özeti:\n     {sarili_ozet}")
        return "\n".join(satirlar)
