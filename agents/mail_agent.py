import os
import json
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel

# Proje ana dizinini otomatik bul (PyCharm'da nereden çalıştırırsan çalıştır hata vermez)
PROJE_DIZINI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADAPTOR_YOLU = os.path.join(PROJE_DIZINI, "models", "mail_agent_lora")
MODEL_ADI = "Qwen/Qwen2.5-1.5B-Instruct"

SYSTEM_PROMPT = (
    "Sen bir mail analiz uzmanısın. Sana verilen Türkçe iş maillerini analiz edip "
    "kesinlikle sadece JSON formatında çıktı veriyorsun. Hiçbir ek açıklama yapmıyorsun."
)


class MailAgent:
    def __init__(self):
        print("1. Ana model (4-bit) yükleniyor...")
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_quant_type="nf4"
        )
        self.tokenizer = AutoTokenizer.from_pretrained(MODEL_ADI)
        base_model = AutoModelForCausalLM.from_pretrained(
            MODEL_ADI,
            quantization_config=bnb_config,
            device_map="auto"
        )

        print(f"2. Eğittiğin LoRA adaptörü takılıyor: {ADAPTOR_YOLU}")
        self.model = PeftModel.from_pretrained(base_model, ADAPTOR_YOLU)
        self.model.eval()
        print("Mail Ajanı hazır!\n")

    def analiz_et(self, mail_metni: str) -> dict:
        mesajlar = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Aşağıdaki maili analiz et:\n\n{mail_metni}"}
        ]

        metin = self.tokenizer.apply_chat_template(
            mesajlar,
            tokenize=False,
            add_generation_prompt=True
        )
        girisler = self.tokenizer(metin, return_tensors="pt").to(self.model.device)

        with torch.no_grad():
            cikti = self.model.generate(
                **girisler,
                max_new_tokens=256,
                do_sample=False,  # Yaratıcılığı kapat, kesin ve net JSON üretsin
                pad_token_id=self.tokenizer.eos_token_id
            )

        ham_yanit = self.tokenizer.decode(
            cikti[0][girisler["input_ids"].shape[1]:],
            skip_special_tokens=True
        ).strip()

        # JSON'a çevirmeyi dene
        try:
            return json.loads(ham_yanit)
        except json.JSONDecodeError:
            return {"hata": "JSON parse edilemedi", "ham_cikti": ham_yanit}


# Doğrudan bu dosya çalıştırıldığında test et
if __name__ == "__main__":
    ajan = MailAgent()

    test_mailleri = [
        # Test 1: Hiç görmediği kritik bir iş maili
        """Gönderen: Volkan Demir (Sunucu Altyapı Ekibi)
Konu: Redis Önbellek Sunucusu Taşıma İşlemi

Selamlar,
Canlı ortamdaki Redis sunucusunu yeni kümeye taşıyacağız. Bu işlem için Perşembe günü saat 14:00'e kadar servis bağlantı adreslerini (connection string) yeni IP'ye yönlendirmeniz ve test ortamında doğrulamanız gerekiyor. Cuma sabahı 06:00'da eski sunucu kapatılacak.""",

        # Test 2: İçinde saat ve tarih geçen TUZAK reklam maili
        """Gönderen: firsat@teknomarketim.com
Konu: Dev Gece İndirimi Bu Akşam 21:00'de Başlıyor!

Merhaba,
Sadece bu akşam 21:00 ile 23:59 saatleri arasında geçerli tüm oyuncu laptoplarında %40 indirim fırsatını kaçırmayın! Kupon kodunuz: GECE40""",

        # Test 3: Bilgilendirme maili
        """Gönderen: İdari İşler
Konu: Yemekhane Kart Okuyucu Güncellemesi

Merhaba,
Yemekhane girişindeki kart okuyucu turnikeler yenilenmiştir. Mevcut personel kartlarınızla herhangi bir işlem yapmadan geçiş yapmaya devam edebilirsiniz."""
    ]

    for i, mail in enumerate(test_mailleri, 1):
        print(f"================ TEST MAİL {i} ================")
        sonuc = ajan.analiz_et(mail)
        print(json.dumps(sonuc, indent=2, ensure_ascii=False))
        print()