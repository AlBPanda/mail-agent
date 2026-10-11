import os
import json
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel
from agents.mail_agent import guvenli_json_coz

PROJE_DIZINI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HAKEM_ADAPTOR_YOLU = os.path.join(PROJE_DIZINI, "models", "hakem_agent_lora")
MODEL_ADI = "Qwen/Qwen2.5-1.5B-Instruct"

HAKEM_SYSTEM_PROMPT = (
    "Sen Baş Hakem ajansın. Orijinal mail ile İşçi Ajanın taslak JSON çıktısını karşılaştır; "
    "hataları ve eksikleri düzeltip kesinlikle sadece doğrulanmış nihai JSON çıktısını ver."
)


class HakemAgent:
    def __init__(self, ortak_model=None, ortak_tokenizer=None):
        if ortak_model is not None and ortak_tokenizer is not None:
            self.tokenizer = ortak_tokenizer
            self.model = ortak_model
            self.model.load_adapter(HAKEM_ADAPTOR_YOLU, adapter_name="hakem")
        else:
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
            self.model = PeftModel.from_pretrained(base_model, HAKEM_ADAPTOR_YOLU, adapter_name="hakem")
            self.model.eval()

    def denetle(self, orijinal_mail: str, isci_json: dict) -> dict:
        if hasattr(self.model, "set_adapter"):
            try:
                self.model.set_adapter("hakem")
            except Exception:
                pass

        kullanici_icerigi = (
            f"[ORİJİNAL MAİL]\n{orijinal_mail}\n\n"
            f"[İŞÇİ AJANIN ÇIKTISI]\n{json.dumps(isci_json, ensure_ascii=False)}"
        )

        mesajlar = [
            {"role": "system", "content": HAKEM_SYSTEM_PROMPT},
            {"role": "user", "content": kullanici_icerigi}
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
                max_new_tokens=512,
                do_sample=False,
                pad_token_id=self.tokenizer.eos_token_id
            )

        ham_yanit = self.tokenizer.decode(
            cikti[0][girisler["input_ids"].shape[1]:],
            skip_special_tokens=True
        ).strip()

        cozulen = guvenli_json_coz(ham_yanit)
        if cozulen is not None and "mail_turu" in cozulen:
            return cozulen

        if "mail_turu" in isci_json:
            return isci_json

        return {"hata": "Hakem JSON parse edemedi", "ham_cikti": ham_yanit, "isci_yedek": isci_json}
