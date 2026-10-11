import gc
import json
import os
import warnings
import torch
from datasets import load_dataset
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig,
    TrainingArguments,
    Trainer,
    EarlyStoppingCallback,
    logging as hf_logging,
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

warnings.filterwarnings("ignore")
hf_logging.set_verbosity_error()

# GPU Belleğini Otomatik Algıla (Bulut 16GB+ vs Yerel 4GB)
vram_gb = 0.0
if torch.cuda.is_available():
    vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
BULUT_MODU = vram_gb >= 10.0  # Kaggle / Colab (T4 16GB, P100, L4, A100 vb.)

# =====================================================================
# 🎛️ İŞÇİ AJAN EĞİTİM KONTROL PANELİ (Bulut & Yerel Otomatik Uyumlu)
# =====================================================================
MODEL_ADI = "Qwen/Qwen2.5-1.5B-Instruct"
VERI_YOLU = "data/mail_egitim.jsonl"
HATA_DEFTERI_YOLU = "data/hata_defteri.jsonl"
KAYIT_YOLU = "./models/mail_agent_lora"
MAX_UZUNLUK = 768 if BULUT_MODU else 540

IMHA_AKTIF = True
MUFREDAT_AKTIF = True
SINAV_MAIL_SAYISI = 200 if BULUT_MODU else 40
KARNE_ORNEK_SAYISI = 40  # Hızlı karne testi için örnek sayısı (saniyeler içinde biter)
HATA_DEFTERI_AKTIF = True
HATA_DEFTERI_LIMIT = 20
SADECE_HATA_DEFTERI_ETUDU = False

LORA_R = 32 if BULUT_MODU else 16
LORA_ALPHA = 64 if BULUT_MODU else 32
LORA_DROPOUT = 0.10
HEDEF_KATMANLAR = [
    "q_proj", "k_proj", "v_proj", "o_proj",
    "gate_proj", "up_proj", "down_proj"
]

EPOCH_SAYISI = 2
OGRENME_ORANI = 0.8e-4
BATCH_SIZE = 4 if BULUT_MODU else 1
GRAD_ACCUMULATION = 4 if BULUT_MODU else 12
LR_ZAMANLAYICI = "cosine"
ISINMA_ADIMI = 20
LOG_ADIMI = 15
AGIRLIK_CEZASI = 0.01  # L2 Ezber Önleyici (Weight Decay)
ERKEN_DURDURMA_SABIR = 3  # Bulut modunda üst üste 3 kez eval_loss artarsa durdur
# =====================================================================

gc.collect()
if torch.cuda.is_available():
    torch.cuda.empty_cache()

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_quant_type="nf4"
)

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

lora_config = LoraConfig(
    r=LORA_R,
    lora_alpha=LORA_ALPHA,
    target_modules=HEDEF_KATMANLAR,
    lora_dropout=LORA_DROPOUT,
    bias="none",
    task_type="CAUSAL_LM"
)

model = get_peft_model(model, lora_config)

aktif_veri_yolu = HATA_DEFTERI_YOLU if (SADECE_HATA_DEFTERI_ETUDU and os.path.exists(HATA_DEFTERI_YOLU)) else VERI_YOLU
ham_dataset = load_dataset("json", data_files=aktif_veri_yolu, split="train")


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
        tam_metin = tokenizer.apply_chat_template(mesajlar, tokenize=False)
        return len(tokenizer(tam_metin)["input_ids"]) <= MAX_UZUNLUK
    except Exception:
        return False


if IMHA_AKTIF:
    ham_dataset = ham_dataset.filter(imha_kontrolu)


def zorluk_puani_hesapla(ornek):
    mesajlar = ornek["messages"]
    uzunluk = len(mesajlar[1]["content"]) + len(mesajlar[2]["content"])
    asistan_json = json.loads(mesajlar[2]["content"])
    tur = asistan_json.get("mail_turu", "")
    taban = 100 if tur == "reklam_spam" else (300 if tur == "bilgilendirme" else 600)
    ornek["zorluk_puani"] = taban + uzunluk
    return ornek


if len(ham_dataset) > SINAV_MAIL_SAYISI + 10:
    bolunmus = ham_dataset.train_test_split(test_size=SINAV_MAIL_SAYISI, seed=42)
    egitim_ham = bolunmus["train"]
    sinav_ham = bolunmus["test"]
else:
    egitim_ham = ham_dataset
    sinav_ham = ham_dataset

# Bulut modunda Erken Durdurma (Early Stopping) sağlıklı çalışsın diye eğitim verisini karıştırıyoruz,
# yerel modda ise müfredat (kolaydan zora) sıralamasını koruyoruz.
if MUFREDAT_AKTIF and not BULUT_MODU:
    egitim_ham = egitim_ham.map(zorluk_puani_hesapla)
    egitim_ham = egitim_ham.sort("zorluk_puani")
    egitim_ham = egitim_ham.remove_columns(["zorluk_puani"])
else:
    egitim_ham = egitim_ham.shuffle(seed=42)


def veri_hazirla(ornek):
    mesajlar = ornek["messages"]
    soru_metni = tokenizer.apply_chat_template(
        mesajlar[:-1],
        tokenize=False,
        add_generation_prompt=True
    )
    soru_tokenlari = tokenizer(soru_metni, truncation=True, max_length=MAX_UZUNLUK)["input_ids"]
    soru_uzunlugu = len(soru_tokenlari)

    tam_metin = tokenizer.apply_chat_template(mesajlar, tokenize=False)
    sonuc = tokenizer(
        tam_metin,
        truncation=True,
        max_length=MAX_UZUNLUK,
        padding="max_length"
    )

    input_ids = sonuc["input_ids"]
    sonuc["labels"] = [
        -100 if (i < soru_uzunlugu or token_id == tokenizer.pad_token_id) else token_id
        for i, token_id in enumerate(input_ids)
    ]
    return sonuc


egitim_tokenized = egitim_ham.map(veri_hazirla, remove_columns=["messages"])
sinav_tokenized = sinav_ham.map(veri_hazirla, remove_columns=["messages"])

if BULUT_MODU:
    egitim_ayarlari = TrainingArguments(
        output_dir="./outputs/mail_lora",
        per_device_train_batch_size=BATCH_SIZE,
        per_device_eval_batch_size=BATCH_SIZE,
        gradient_accumulation_steps=GRAD_ACCUMULATION,
        num_train_epochs=EPOCH_SAYISI,
        learning_rate=OGRENME_ORANI,
        lr_scheduler_type=LR_ZAMANLAYICI,
        warmup_steps=ISINMA_ADIMI,
        fp16=True,
        logging_steps=LOG_ADIMI,
        eval_strategy="steps",
        eval_steps=25,
        save_strategy="steps",
        save_steps=25,
        save_total_limit=2,
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        prediction_loss_only=True,
        optim="adamw_torch",
        weight_decay=AGIRLIK_CEZASI
    )
    trainer = Trainer(
        model=model,
        args=egitim_ayarlari,
        train_dataset=egitim_tokenized,
        eval_dataset=sinav_tokenized,
        callbacks=[EarlyStoppingCallback(early_stopping_patience=ERKEN_DURDURMA_SABIR)]
    )
else:
    egitim_ayarlari = TrainingArguments(
        output_dir="./outputs/mail_lora",
        per_device_train_batch_size=BATCH_SIZE,
        gradient_accumulation_steps=GRAD_ACCUMULATION,
        num_train_epochs=EPOCH_SAYISI,
        learning_rate=OGRENME_ORANI,
        lr_scheduler_type=LR_ZAMANLAYICI,
        warmup_steps=ISINMA_ADIMI,
        fp16=True,
        logging_steps=LOG_ADIMI,
        eval_strategy="no",
        save_strategy="no",
        prediction_loss_only=True,
        optim="adamw_torch",
        weight_decay=AGIRLIK_CEZASI
    )
    trainer = Trainer(
        model=model,
        args=egitim_ayarlari,
        train_dataset=egitim_tokenized,
    )

mod_etiketi = "☁️ BULUT FABRİKA MODU (Erken Durdurma + Yüksek Kapasite Aktif)" if BULUT_MODU else "💻 YEREL MOD"
print(f"🚀 İşçi Ajan eğitimi başlıyor [{mod_etiketi}] ({len(egitim_ham)} örnek)...")
trainer.train()

model.save_pretrained(KAYIT_YOLU)
tokenizer.save_pretrained(KAYIT_YOLU)
print(f"✅ Eğitim tamamlandı ve ürün kaydedildi: {KAYIT_YOLU}")

test_limiti = min(len(sinav_ham), KARNE_ORNEK_SAYISI)

if HATA_DEFTERI_AKTIF and not SADECE_HATA_DEFTERI_ETUDU:
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    model.eval()
    hatalar = []
    with torch.no_grad():
        for idx in range(test_limiti):
            ornek_tensor = {
                "input_ids": torch.tensor([sinav_tokenized[idx]["input_ids"]], device=model.device),
                "attention_mask": torch.tensor([sinav_tokenized[idx]["attention_mask"]], device=model.device),
                "labels": torch.tensor([sinav_tokenized[idx]["labels"]], device=model.device),
            }
            cikti = model(**ornek_tensor)
            hatalar.append((cikti.loss.item(), sinav_ham[idx]))

    hatalar.sort(key=lambda x: x[0], reverse=True)
    secilen_hatalar = hatalar[:HATA_DEFTERI_LIMIT]

    with open(HATA_DEFTERI_YOLU, "w", encoding="utf-8") as f:
        for _, ham_ornek in secilen_hatalar:
            f.write(json.dumps({"messages": ham_ornek["messages"]}, ensure_ascii=False) + "\n")

    ortalama_loss = sum(x[0] for x in hatalar) / len(hatalar) if hatalar else 0.0
    print(f"📓 Hata defteri güncellendi ({HATA_DEFTERI_YOLU}) | Ortalama Sınav Kaybı: {ortalama_loss:.4f}")

# ──────────────────────────────────────────────────────────────────────
# 📊 HIZLI SINAV KARNESİ — Görülmemiş veri ile gerçek sınıflandırma testi
# ──────────────────────────────────────────────────────────────────────
print(f"\n📊 Sınav Karnesi hesaplanıyor ({test_limiti} görülmemiş örnek)...")

gc.collect()
if torch.cuda.is_available():
    torch.cuda.empty_cache()

model.eval()
GECERLI_TURLER = ["aksiyon_gerekli", "bilgilendirme", "reklam_spam"]

dogru = 0
yanlis = 0
sinif_dogru = {t: 0 for t in GECERLI_TURLER}
sinif_toplam = {t: 0 for t in GECERLI_TURLER}

with torch.no_grad():
    for idx in range(test_limiti):
        ornek = sinav_ham[idx]
        mesajlar = ornek["messages"]
        beklenen_tur = json.loads(mesajlar[2]["content"]).get("mail_turu", "")

        soru_metni = tokenizer.apply_chat_template(
            mesajlar[:-1], tokenize=False, add_generation_prompt=True
        )
        giris = tokenizer(soru_metni, return_tensors="pt", truncation=True,
                          max_length=MAX_UZUNLUK).to(model.device)

        cikti_ids = model.generate(
            **giris,
            max_new_tokens=45,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
        )
        uretilen = tokenizer.decode(
            cikti_ids[0][giris["input_ids"].shape[1]:], skip_special_tokens=True
        ).strip()

        tahmin_tur = None
        for tur in GECERLI_TURLER:
            if tur in uretilen:
                tahmin_tur = tur
                break

        if beklenen_tur in sinif_toplam:
            sinif_toplam[beklenen_tur] += 1

        if tahmin_tur == beklenen_tur:
            dogru += 1
            if beklenen_tur in sinif_dogru:
                sinif_dogru[beklenen_tur] += 1
        else:
            yanlis += 1

toplam = dogru + yanlis
oran = (dogru / toplam * 100) if toplam > 0 else 0

print("\n" + "═" * 54)
print("  📋 İŞÇİ AJAN SINAV KARNESİ (Görülmemiş Veri)")
print("═" * 54)
print(f"  ✅ Doğru     : {dogru:>4} / {toplam}")
print(f"  ❌ Yanlış    : {yanlis:>4} / {toplam}")
print(f"  🎯 Başarı    : %{oran:.1f}")
print("─" * 54)
for tur in GECERLI_TURLER:
    t = sinif_toplam[tur]
    d = sinif_dogru[tur]
    oran_s = (d / t * 100) if t > 0 else 0
    etiket = {
        "aksiyon_gerekli": "Aksiyon  ",
        "bilgilendirme":   "Bilgi    ",
        "reklam_spam":     "Spam     ",
    }[tur]
    print(f"  {etiket}: {d:>3}/{t:<3} — %{oran_s:.1f}")
print("═" * 54)