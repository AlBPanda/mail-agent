import os
import json
import warnings
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig, logging as hf_logging
from peft import PeftModel

warnings.filterwarnings("ignore")
hf_logging.set_verbosity_error()

PROJE_DIZINI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADAPTOR_YOLU = os.path.join(PROJE_DIZINI, "models", "mail_agent_lora")
MODEL_ADI = "Qwen/Qwen2.5-1.5B-Instruct"

SYSTEM_PROMPT = (
    "Sen bir mail analiz uzmanısın. Sana verilen Türkçe iş maillerini analiz edip "
    "kesinlikle sadece JSON formatında çıktı veriyorsun. Hiçbir ek açıklama yapmıyorsun."
)


def guvenli_json_coz(ham_metin: str) -> dict | None:
    if not ham_metin:
        return None
    temiz = ham_metin.strip()

    try:
        return json.loads(temiz)
    except json.JSONDecodeError:
        pass

    ilk = temiz.find("{")
    son = temiz.rfind("}")
    if ilk != -1 and son != -1 and son > ilk:
        try:
            return json.loads(temiz[ilk:son + 1])
        except json.JSONDecodeError:
            pass

    if ilk != -1:
        parca = temiz[ilk:]
        for ek in ['"}', '"]', '"}]}', '}']:
            try:
                return json.loads(parca + ek)
            except json.JSONDecodeError:
                continue

    return None


class MailAgent:
    def __init__(self):
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
        self.model = PeftModel.from_pretrained(base_model, ADAPTOR_YOLU, adapter_name="isci")
        self.model.eval()

    def analiz_et(self, mail_metni: str) -> dict:
        if hasattr(self.model, "set_adapter"):
            try:
                self.model.set_adapter("isci")
            except Exception:
                pass

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
        return {"hata": "JSON parse edilemedi", "ham_cikti": ham_yanit}