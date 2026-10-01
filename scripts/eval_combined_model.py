"""
Phase 5 - Combined-trained model (models/lora_combined_v1) ko TEEN alag
yardsticks pe evaluate karta hai, taaki honest before/after comparison
mile (koi bhi training nahi hoti yahan, sirf saved adapter load karke
eval - fast, ~1-2 min):

1. CORD-only dev (data="cord")       -> Phase 4 ke 86.8%/88.1% (total_fields=1247)
                                         ke EXACT SAME yardstick pe compare -
                                         "kya synthetic data add karne se
                                         purane CORD fields bhool gaya model
                                         (catastrophic forgetting)?"
2. Synthetic-only dev (data="synthetic") -> naye fields (vendor/GSTIN/
                                         invoice-no/date/HSN/CGST/SGST) ka
                                         TRUE isolated number, bina CORD ke
                                         saath mix kiye (jo pichhle combined
                                         run me 93.3% overall me chhupa hua
                                         tha - us number me CORD aur
                                         synthetic dono mix the).
3. Combined dev (data="combined")    -> training script ne jo report kiya
                                         (93.3%/93.9%) - sanity check ki
                                         yahan bhi wahi number aata hai
                                         (confirm karta hai eval consistent hai).
"""
import sys
import torch
from peft import PeftModel
from transformers import AutoModelForTokenClassification

sys.path.insert(0, "src/data")
sys.path.insert(0, "src/models")
from cord_torch_dataset import ID2LABEL, LABEL2ID
from load_cord import LABELS
from train_lora import run_field_evaluation, MODEL_NAME

ADAPTER_DIR = "models/lora_combined_v1"


def load_model(device):
    print(f"Base model + adapter load ho raha hai ({ADAPTER_DIR})...")
    base = AutoModelForTokenClassification.from_pretrained(
        MODEL_NAME, num_labels=len(LABELS), id2label=ID2LABEL, label2id=LABEL2ID,
    )
    model = PeftModel.from_pretrained(base, ADAPTER_DIR)
    model = model.to(device)
    model.eval()
    return model


def print_result(title, result):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)
    print("Overall:", result["overall"])
    print("\nAll fields:")
    for field, scores in sorted(result["per_field"].items(), key=lambda x: -x[1]["count"]):
        print(f"  {field}: {scores}")


def main():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Device: {device}")

    model = load_model(device)

    result_cord = run_field_evaluation(model, device, split="dev", data="cord")
    print_result("1. CORD-ONLY dev (apples-to-apples vs Phase 4's 86.8%/88.1%, total_fields should be 1247):", result_cord)

    result_synth = run_field_evaluation(model, device, split="dev", data="synthetic")
    print_result("2. SYNTHETIC-ONLY dev (true isolated number for vendor/GSTIN/invoice-no/date/HSN/CGST/SGST etc):", result_synth)

    result_combined = run_field_evaluation(model, device, split="dev", data="combined")
    print_result("3. COMBINED dev (sanity check - should match the training run's reported 93.3%/93.9%):", result_combined)


if __name__ == "__main__":
    main()
