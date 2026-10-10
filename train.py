import gc
import json
import os
import torch
from datasets import load_dataset
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig,
    TrainingArguments,
    Trainer,
    TrainerCallback,
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

# =====================================================================
# 🎛️ KONTROL PANELİ (TÜM AYARLARI BURADAN DEĞİŞTİREBİLİRSİN)
# =====================================================================

# --- 1. Model ve Veri Yolları ---
MODEL_ADI = "Qwen/Qwen2.5-1.5B-Instruct"
VERI_YOLU = "data/mail_egitim.jsonl"
HATA_DEFTERI_YOLU = "data/hata_defteri.jsonl"
KAYIT_YOLU = "./models/mail_agent_lora"
MAX_UZUNLUK = 320                  # Maksimum token uzunluğu (VRAM dostu)

# --- 2. Senin Özel Eğitim Tekniklerin ---
IMHA_AKTIF = True                  # 💣 Bozuk/eksik JSON verilerini eğitime sokmadan imha et
MUFREDAT_AKTIF = True              # 📚 Kolay/kısa maillerden zor/uzun maillere doğru sırala
SABIR_AKTIF = False                # ⏱️ Ara sınavları kapattık (4GB VRAM eğitim ortasında şişmesin diye!)
SABIR_LIMITI = 3                   # ⏱️ Kaç ölçüm üst üste iyileşmezse dursun?
DEGERLENDIRME_ADIMI = 25           # Kaç adımda bir Val Loss (sınav) ölçülsün?
SINAV_MAIL_SAYISI = 30             # Eğitim sonunda kaç sınav maili çözülsün?
HATA_DEFTERI_AKTIF = True          # 📓 Eğitim sonunda Sınav Notunu ölç ve en zor mailleri hata_defteri.jsonl'e kaydet
HATA_DEFTERI_LIMIT = 10            # En çok zorlandığı kaç mail hata defterine yazılsın?
SADECE_HATA_DEFTERI_ETUDU = False  # True yaparsan tüm veri yerine sadece hata_defteri.jsonl ile hızlı etüt yapar!

# --- 3. LoRA (Beyin Kapasitesi) Ayarları ---
LORA_R = 16                        # 16: RTX 3050 4GB VRAM için en güvenli ve hızlı boyut!
LORA_ALPHA = 32                    # Öğrenme gücü çarpanı (LORA_R * 2)
LORA_DROPOUT = 0.10                # Ezberlemeyi önleme oranı (%10)
HEDEF_KATMANLAR = [
    "q_proj", "k_proj", "v_proj", "o_proj",
    "gate_proj", "up_proj", "down_proj"
]

# --- 4. Eğitim (Training) Ayarları ---
EPOCH_SAYISI = 1                   # 1000 benzersiz mail için 1 tur (121 adım)
OGRENME_ORANI = 1.5e-4             # 0.00015 (Modelin kendi Türkçesini bozmayan hassas oran)
BATCH_SIZE = 2                     # RTX 3050 4GB VRAM için 2 sabit kalsın
GRAD_ACCUMULATION = 4              # 2 x 4 = 8 efektif batch boyutu
LR_ZAMANLAYICI = "cosine"          # Yumuşak kosinüs düşüşü
ISINMA_ADIMI = 10                  # İlk 10 adımda ısınma (warmup)
LOG_ADIMI = 10                     # Her 10 adımda bir ekrana Eğitim Loss yazdır

# =====================================================================


# Başlamadan önce GPU önbelleğini tertemiz yap
gc.collect()
if torch.cuda.is_available():
    torch.cuda.empty_cache()

# 1. Model ve Tokenizer Yükleme
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_quant_type="nf4"
)

print("Model yükleniyor...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_ADI)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

model = AutoModelForCausalLM.from_pretrained(
    MODEL_ADI,
    quantization_config=bnb_config,
    device_map="auto"
)

model = prepare_model_for_kbit_training(
    model,
    gradient_checkpointing_kwargs={"use_reentrant": False}
)

# 2. LoRA Adaptörlerini Takma
lora_config = LoraConfig(
    r=LORA_R,
    lora_alpha=LORA_ALPHA,
    target_modules=HEDEF_KATMANLAR,
    lora_dropout=LORA_DROPOUT,
    bias="none",
    task_type="CAUSAL_LM"
)

model = get_peft_model(model, lora_config)
model.print_trainable_parameters()

# 3. Veri Setini Yükleme
aktif_veri_yolu = HATA_DEFTERI_YOLU if (SADECE_HATA_DEFTERI_ETUDU and os.path.exists(HATA_DEFTERI_YOLU)) else VERI_YOLU
print(f"\nVeri kaynağı okunuyor: {aktif_veri_yolu}")
ham_dataset = load_dataset("json", data_files=aktif_veri_yolu, split="train")


# --- 💣 İMHA FİLTRESİ ---
def imha_kontrolu(ornek):
    try:
        mesajlar = ornek["messages"]
        if len(mesajlar) != 3:
            return False
        mail_metni = mesajlar[1]["content"]
        asistan_cevabi = mesajlar[2]["content"]
        if len(mail_metni.strip()) < 30:
            return False
        veri_json = json.loads(asistan_cevabi)
        if veri_json.get("mail_turu") not in ["aksiyon_gerekli", "bilgilendirme", "reklam_spam"]:
            return False
        return True
    except Exception:
        return False


if IMHA_AKTIF:
    ilk_sayi = len(ham_dataset)
    ham_dataset = ham_dataset.filter(imha_kontrolu)
    imha_edilen = ilk_sayi - len(ham_dataset)
    print(f"💣 [İMHA FİLTRESİ] {ilk_sayi} örnek tarandı -> {len(ham_dataset)} sağlam, {imha_edilen} bozuk örnek imha edildi!")


# --- 📚 MÜFREDAT ÖĞRENME (KOLAYDAN ZORA SIRALAMA) ---
def zorluk_puani_hesapla(ornek):
    mesajlar = ornek["messages"]
    uzunluk = len(mesajlar[1]["content"]) + len(mesajlar[2]["content"])
    asistan_json = json.loads(mesajlar[2]["content"])
    tur = asistan_json.get("mail_turu", "")
    taban = 100 if tur == "reklam_spam" else (300 if tur == "bilgilendirme" else 600)
    ornek["zorluk_puani"] = taban + uzunluk
    return ornek


# Eğitim ve Sınav (Validation) Ayırma (VRAM dostu 30 sınav maili)
if len(ham_dataset) > SINAV_MAIL_SAYISI + 10:
    bolunmus = ham_dataset.train_test_split(test_size=SINAV_MAIL_SAYISI, seed=42)
    egitim_ham = bolunmus["train"]
    sinav_ham = bolunmus["test"]
else:
    egitim_ham = ham_dataset
    sinav_ham = ham_dataset

if MUFREDAT_AKTIF:
    egitim_ham = egitim_ham.map(zorluk_puani_hesapla)
    egitim_ham = egitim_ham.sort("zorluk_puani")
    egitim_ham = egitim_ham.remove_columns(["zorluk_puani"])
    print("📚 [MÜFREDAT ÖĞRENME] Eğitim verileri kolaydan (reklam/kısa) zora (uzun/çift tarihli) doğru sıralandı!")

print(f"📊 Veri Dağılımı: {len(egitim_ham)} Eğitim Maili | {len(sinav_ham)} Sınav (Validation) Maili\n")


# 4. Tokenize Etme ve Soru Maskelemesi (-100)
def veri_hazirla(ornek):
    mesajlar = ornek["messages"]

    soru_metni = tokenizer.apply_chat_template(
        mesajlar[:-1],
        tokenize=False,
        add_generation_prompt=True
    )
    soru_tokenlari = tokenizer(soru_metni, truncation=True, max_length=MAX_UZUNLUK)["input_ids"]
    soru_uzunlugu = len(soru_tokenlari)

    tam_metin = tokenizer.apply_chat_template(
        mesajlar,
        tokenize=False
    )
    sonuc = tokenizer(
        tam_metin,
        truncation=True,
        max_length=MAX_UZUNLUK,
        padding="max_length"
    )

    input_ids = sonuc["input_ids"]
    labels = []
    for i, token_id in enumerate(input_ids):
        if i < soru_uzunlugu or token_id == tokenizer.pad_token_id:
            labels.append(-100)
        else:
            labels.append(token_id)

    sonuc["labels"] = labels
    return sonuc


egitim_tokenized = egitim_ham.map(veri_hazirla, remove_columns=["messages"])
sinav_tokenized = sinav_ham.map(veri_hazirla, remove_columns=["messages"])


# --- ⏱️ ÖZEL SABIRMETRE VE VRAM SÜPÜRGESİ CALLBACK ---
# Hugging Face'in hantal checkpoint kaydı yerine sadece 17 MB'lık en iyi LoRA beynini kaydeder, asla kilitlenmez!
class SabirmetreVeTemizlikCallback(TrainerCallback):
    def __init__(self, sabir_limiti, kayit_yolu, model_ref, tokenizer_ref):
        self.sabir_limiti = sabir_limiti
        self.kayit_yolu = kayit_yolu
        self.model_ref = model_ref
        self.tokenizer_ref = tokenizer_ref
        self.en_iyi_val_loss = float("inf")
        self.sabir_sayaci = 0

    def on_evaluate(self, args, state, control, metrics=None, **kwargs):
        # Sınav biter bitmez VRAM önbelleğini temizle ki eğitim takılmasın!
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        if not metrics or "eval_loss" not in metrics:
            return

        val_loss = metrics["eval_loss"]
        adim = state.global_step

        if val_loss < self.en_iyi_val_loss:
            self.en_iyi_val_loss = val_loss
            self.sabir_sayaci = 0
            # Sadece 17 MB'lık LoRA adaptörünü kaydet (0.2 saniye sürer, kilitlenmez!)
            self.model_ref.save_pretrained(self.kayit_yolu)
            self.tokenizer_ref.save_pretrained(self.kayit_yolu)
            print(f"\n🎯 [SABIRMETRE - Adım {adim}] Yeni En İyi Val Loss: {val_loss:.4f} -> En iyi beyin kaydedildi! (Sabır: 0/{self.sabir_limiti})\n")
        else:
            self.sabir_sayaci += 1
            print(f"\n⚠️ [SABIRMETRE - Adım {adim}] Val Loss iyileşmedi ({val_loss:.4f} >= {self.en_iyi_val_loss:.4f}). Sabır: {self.sabir_sayaci}/{self.sabir_limiti}\n")
            if self.sabir_sayaci >= self.sabir_limiti:
                print(f"\n🛑 [SABIRMETRE] Sabır limiti ({self.sabir_limiti}) doldu! Eğitim erken durduruluyor.\n")
                control.should_training_stop = True


# 5. Eğitim Ayarları (save_strategy="no" ile optimizer kilitlenmesi tamamen engellendi!)
egitim_ayarlari = TrainingArguments(
    output_dir="./outputs/mail_lora",
    per_device_train_batch_size=BATCH_SIZE,
    per_device_eval_batch_size=1,      # Sınavda 1'er 1'er oku -> Sıfır VRAM şişmesi!
    gradient_accumulation_steps=GRAD_ACCUMULATION,
    num_train_epochs=EPOCH_SAYISI,
    learning_rate=OGRENME_ORANI,
    lr_scheduler_type=LR_ZAMANLAYICI,
    warmup_steps=ISINMA_ADIMI,
    fp16=True,
    logging_steps=LOG_ADIMI,
    eval_strategy="steps" if SABIR_AKTIF else "no",
    eval_steps=DEGERLENDIRME_ADIMI if SABIR_AKTIF else None,
    save_strategy="no",                # Kilitlenmeye yol açan ağır optimizer kaydını kapattık!
    prediction_loss_only=True,
    optim="adamw_torch"                # Windows'ta ekran kartı sürücüsünü kilitlemeyen güvenli optimizer!
)

callbacks = []
if SABIR_AKTIF:
    callbacks.append(SabirmetreVeTemizlikCallback(SABIR_LIMITI, KAYIT_YOLU, model, tokenizer))
    print(f"⏱️ [SABIRMETRE AKTİF] Her {DEGERLENDIRME_ADIMI} adımda bir 30 sınav maili çözülecek ve VRAM süpürülecek!")

trainer = Trainer(
    model=model,
    args=egitim_ayarlari,
    train_dataset=egitim_tokenized,
    eval_dataset=sinav_tokenized if SABIR_AKTIF else None,
    callbacks=callbacks
)

print("\nEğitim başlıyor! 🚀")
trainer.train()

# Eğer Sabırmetre kapalıysa sonda kaydet
if not SABIR_AKTIF:
    model.save_pretrained(KAYIT_YOLU)
    tokenizer.save_pretrained(KAYIT_YOLU)

print(f"\n✅ Eğitim tamamlandı! En iyi uzman ajan adaptörü '{KAYIT_YOLU}' klasöründe hazır.")


# --- 📓 HATA DEFTERİ (ZORLANILAN ÖRNEKLERİ YAKALAMA) ---
if HATA_DEFTERI_AKTIF and not SADECE_HATA_DEFTERI_ETUDU:
    print("\n📓 [HATA DEFTERİ] Sınav mailleri taranıyor, modelin en çok zorlandığı örnekler bulunuyor...")
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    model.eval()
    hatalar = []

    with torch.no_grad():
        for idx in range(len(sinav_tokenized)):
            ornek_tensor = {
                "input_ids": torch.tensor([sinav_tokenized[idx]["input_ids"]], device=model.device),
                "attention_mask": torch.tensor([sinav_tokenized[idx]["attention_mask"]], device=model.device),
                "labels": torch.tensor([sinav_tokenized[idx]["labels"]], device=model.device),
            }
            cikti = model(**ornek_tensor)
            kayip_degeri = cikti.loss.item()
            hatalar.append((kayip_degeri, sinav_ham[idx]))

    hatalar.sort(key=lambda x: x[0], reverse=True)
    secilen_hatalar = hatalar[:HATA_DEFTERI_LIMIT]

    with open(HATA_DEFTERI_YOLU, "w", encoding="utf-8") as f:
        for kayip, ham_ornek in secilen_hatalar:
            f.write(json.dumps({"messages": ham_ornek["messages"]}, ensure_ascii=False) + "\n")

    en_yuksek = secilen_hatalar[0][0] if secilen_hatalar else 0.0
    en_dusuk = hatalar[-1][0] if hatalar else 0.0
    print(f"📓 [HATA DEFTERİ HAZIR] En zor {len(secilen_hatalar)} mail '{HATA_DEFTERI_YOLU}' dosyasına yazıldı!")
    print(f"   (En zor mail Loss: {en_yuksek:.4f} | En kolay mail Loss: {en_dusuk:.4f})")