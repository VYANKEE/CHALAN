"""
Phase 6 - Confidence calibration + STP threshold analysis.

KYA: Model jo confidence deta hai (softmax max-prob) raw/overconfident hota
hai - agar wo bolta hai "95% sure" toh reality me sirf ~80% baar sahi hota
hai (common neural-net behavior). Agar hum directly is raw confidence pe
STP (straight-through processing, auto-approve) ka decision lete hain, toh
galat predictions bhi confidently auto-approve ho jaayengi.

KYUN TEMPERATURE SCALING: ek single scalar T seekhte hain (dev set pe, NLL
minimize karke via grid search) jisse saare logits ko divide karte hain
before softmax. Ye MONOTONIC hai (predictions/ranking nahi badalta, sirf
confidence "sharpen"/"soften" hoti hai) - Guo et al. 2017 ka simplest,
sabse widely-used post-hoc calibration method, aur over-engineering nahi
hai (isotonic regression jaisa complex nonparametric method yahan zaroorat
se zyada hota, itne chhote dev set - 100+25 examples - ke saath).

METHODOLOGY (leakage-free, important):
- T dev set (CORD dev + synthetic dev, combined) ke token-level logits pe
  fit hota hai.
- ECE / reliability diagram / STP table TEST SET pe report hote hain - test
  set ab tak kabhi bhi (training ya checkpoint-selection me) touch nahi hua
  hai, isliye genuinely held-out hai - final calibration claim ke liye
  sabse honest yardstick.

FIELD-LEVEL CONFIDENCE (STP table ke liye): ek field (jaise
TOTAL.TOTAL_PRICE) me multiple tokens ho sakte hain. MIN confidence lete
hain us field ke saare tokens me se (weakest-link) - agar kisi bhi token pe
model unsure hai, poora field "risky" maana jaata hai STP ke liye. Production
me conservative/safe choice hai (average lene se over-optimistic auto-
approvals badh sakte).

MARKET NEED: "kitna % invoices bina human touch ke safely process ho sakte
hain, kis measured error-rate pe" - yahi cost-threshold framing invoice-
automation companies (Rossum/Nanonets/Hyperscience) ka core business metric
hai, aur project ke Problem statement ka "honest per-field confidence score"
wala hissa yahi implement karta hai.
"""
import sys

import numpy as np
import torch
from peft import PeftModel
from transformers import AutoModelForTokenClassification

sys.path.insert(0, "src/data")
sys.path.insert(0, "src/models")
sys.path.insert(0, "src/evaluation")
from cord_torch_dataset import ID2LABEL, LABEL2ID, PROCESSOR
from load_cord import LABELS, load_split as load_cord_split
from load_synthetic import load_split as load_synthetic_split
from train_lora import MODEL_NAME

from PIL import Image

ADAPTER_DIR = "models/lora_combined_v1"
OUT_DIR = "docs"


def load_model(device):
    print(f"Base model + adapter load ho raha hai ({ADAPTER_DIR})...")
    base = AutoModelForTokenClassification.from_pretrained(
        MODEL_NAME, num_labels=len(LABELS), id2label=ID2LABEL, label2id=LABEL2ID,
    )
    model = PeftModel.from_pretrained(base, ADAPTER_DIR)
    model = model.to(device)
    model.eval()
    return model


def collect_token_logits(model, device, split):
    """
    Har example ke liye model chalao, aur sirf VALID token positions
    (word_labels wale, jo -100 nahi hain - matlab har word ka pehla
    sub-token, padding/continuation tokens exclude) ke logits + true
    label + us word ka text + example id record karo.

    Ye ek baar chalane se DONO kaam ho jaate hain - token-level ECE/
    reliability (calibration) AUR field-level STP table (decode karke) -
    isliye poora record store karte hain, sirf max-prob nahi.
    """
    model.eval()
    examples = load_cord_split(split) + load_synthetic_split(split)
    records = []  # each: dict(example_idx, word_idx, word, true_label_id, logits(np array))

    for ex_idx, ex in enumerate(examples):
        image = Image.open(ex["image_path"]).convert("RGB")
        words = ex["words"]
        boxes = ex["bboxes"]
        label_ids = [LABEL2ID[tag] for tag in ex["ner_tags"]]

        encoding = PROCESSOR(
            image, words, boxes=boxes, word_labels=label_ids,
            truncation=True, padding="max_length", max_length=320,
            return_tensors="pt",
        )
        labels = encoding.pop("labels")[0]  # [seq_len], -100 for non-first-subtoken/padding
        word_ids = None
        # PROCESSOR's tokenizer output still exposes word_ids via the batch encoding
        # before popping tensors out - recompute via a parallel call without word_labels
        # to get word_ids cleanly (word_labels path doesn't retain BatchEncoding methods
        # after return_tensors="pt" squeeze-free access in this transformers version).
        enc_for_ids = PROCESSOR(
            image, words, boxes=boxes, truncation=True,
            padding="max_length", max_length=320, return_tensors="pt",
        )
        word_ids = enc_for_ids.word_ids(batch_index=0)

        encoding = {k: v.to(device) for k, v in encoding.items()}
        with torch.no_grad():
            outputs = model(**encoding)
        logits = outputs.logits.squeeze(0).cpu().numpy()  # [seq_len, num_labels]

        labels_np = labels.numpy()
        valid_positions = np.where(labels_np != -100)[0]
        for pos in valid_positions:
            w_id = word_ids[pos]
            word_text = words[w_id] if w_id is not None else ""
            records.append({
                "example_idx": ex_idx,
                "word_idx": w_id,
                "word": word_text,
                "true_label_id": int(labels_np[pos]),
                "logits": logits[pos],
            })

    return records, examples


def softmax(x):
    x = x - np.max(x, axis=-1, keepdims=True)
    e = np.exp(x)
    return e / np.sum(e, axis=-1, keepdims=True)


def nll_at_temperature(records, T):
    total_nll, n = 0.0, 0
    for r in records:
        probs = softmax(r["logits"] / T)
        p_true = max(probs[r["true_label_id"]], 1e-12)
        total_nll += -np.log(p_true)
        n += 1
    return total_nll / n


def fit_temperature(records):
    """Grid search T in [0.5, 5.0] step 0.05 - NLL minimize karta hai dev
    set pe. Grid search isliye (LBFGS jaisa optimizer nahi) kyunki simple,
    predictable, aur is scale (~15-20k tokens) pe fast hai - koi convergence
    quirk ka risk nahi."""
    grid = np.arange(0.5, 5.01, 0.05)
    best_T, best_nll = 1.0, float("inf")
    for T in grid:
        nll = nll_at_temperature(records, T)
        if nll < best_nll:
            best_nll = nll
            best_T = T
    return best_T, best_nll


def compute_ece(records, T, n_bins=15):
    """Expected Calibration Error: confidence ko n_bins equal-width bins me
    daalo, har bin ke andar |accuracy - mean_confidence| ka weighted average."""
    confidences, corrects = [], []
    for r in records:
        probs = softmax(r["logits"] / T)
        pred = int(np.argmax(probs))
        conf = float(probs[pred])
        confidences.append(conf)
        corrects.append(1 if pred == r["true_label_id"] else 0)
    confidences = np.array(confidences)
    corrects = np.array(corrects)

    bin_edges = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    bin_stats = []
    n = len(confidences)
    for i in range(n_bins):
        lo, hi = bin_edges[i], bin_edges[i + 1]
        if i == n_bins - 1:
            mask = (confidences >= lo) & (confidences <= hi)
        else:
            mask = (confidences >= lo) & (confidences < hi)
        count = mask.sum()
        if count == 0:
            bin_stats.append((lo, hi, count, None, None))
            continue
        bin_acc = corrects[mask].mean()
        bin_conf = confidences[mask].mean()
        ece += (count / n) * abs(bin_acc - bin_conf)
        bin_stats.append((lo, hi, count, bin_conf, bin_acc))
    return ece, bin_stats


def plot_reliability(bin_stats_before, bin_stats_after, out_path):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib nahi mila - reliability diagram skip (pip install matplotlib se fix ho jaayega, table upar text me hai).")
        return

    fig, axes = plt.subplots(1, 2, figsize=(11, 5))
    for ax, bin_stats, title in zip(axes, [bin_stats_before, bin_stats_after], ["Before calibration (T=1.0)", f"After calibration"]):
        xs, accs, confs = [], [], []
        for lo, hi, count, conf, acc in bin_stats:
            if count == 0:
                continue
            xs.append((lo + hi) / 2)
            accs.append(acc)
            confs.append(conf)
        ax.plot([0, 1], [0, 1], "k--", alpha=0.4, label="perfect calibration")
        ax.bar(xs, accs, width=1 / len(bin_stats), alpha=0.7, edgecolor="black", label="accuracy")
        ax.scatter(confs, accs, color="red", zorder=5, s=20, label="bin (conf, acc)")
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_xlabel("Confidence")
        ax.set_ylabel("Accuracy")
        ax.set_title(title)
        ax.legend(fontsize=8)
    plt.tight_layout()
    import os
    os.makedirs(OUT_DIR, exist_ok=True)
    plt.savefig(out_path, dpi=120)
    print(f"Reliability diagram saved: {out_path}")


def decode_fields_with_confidence(words, tags, confidences):
    """bio_tags_to_fields() jaisa hi BIO-decode logic, bas har field ke saath
    us field ke tokens ka MIN confidence bhi track karta hai."""
    from collections import defaultdict
    fields = defaultdict(list)
    current_field, current_words, current_confs = None, [], []

    def flush():
        if current_field and current_words:
            fields[current_field].append((" ".join(current_words), min(current_confs)))

    for word, tag, conf in zip(words, tags, confidences):
        if tag == "O":
            flush()
            current_field, current_words, current_confs = None, [], []
        elif tag.startswith("B-"):
            flush()
            current_field, current_words, current_confs = tag[2:], [word], [conf]
        elif tag.startswith("I-"):
            if current_field == tag[2:]:
                current_words.append(word)
                current_confs.append(conf)
            else:
                flush()
                current_field, current_words, current_confs = tag[2:], [word], [conf]
    flush()
    return dict(fields)


def stp_threshold_table(model, device, T, split="test"):
    """
    TEST set pe: har field-instance ke liye predicted value + confidence
    (post-temperature) + true value nikaalo, phir alag-alag thresholds pe
    "STP% (kitne % auto-approve honge)" aur "error rate un auto-approved
    me se" compute karo.
    """
    from metrics import bio_tags_to_fields

    model.eval()
    examples = load_cord_split(split) + load_synthetic_split(split)
    all_records = []  # (pred_value, true_value, confidence)

    for ex in examples:
        image = Image.open(ex["image_path"]).convert("RGB")
        words = ex["words"]
        boxes = ex["bboxes"]

        encoding = PROCESSOR(
            image, words, boxes=boxes, truncation=True,
            padding="max_length", max_length=320, return_tensors="pt",
        )
        word_ids = encoding.word_ids(batch_index=0)
        encoding_dev = {k: v.to(device) for k, v in encoding.items()}

        with torch.no_grad():
            outputs = model(**encoding_dev)
        logits = outputs.logits.squeeze(0).cpu().numpy()
        probs_all = softmax(logits / T)

        pred_tags, pred_confs, prev_word_id = [], [], None
        for idx, word_id in enumerate(word_ids):
            if word_id is None:
                continue
            if word_id != prev_word_id:
                pred_id = int(np.argmax(probs_all[idx]))
                pred_tags.append(ID2LABEL[pred_id])
                pred_confs.append(float(probs_all[idx][pred_id]))
                prev_word_id = word_id

        words_truncated = words[:len(pred_tags)]
        pred_fields = decode_fields_with_confidence(words_truncated, pred_tags, pred_confs)
        true_fields = bio_tags_to_fields(ex["words"], ex["ner_tags"])

        for field, true_values in true_fields.items():
            got = pred_fields.get(field, [])
            for i, true_val in enumerate(true_values):
                if i < len(got):
                    pred_val, conf = got[i]
                else:
                    pred_val, conf = "", 0.0
                all_records.append((pred_val.strip().lower(), true_val.strip().lower(), conf))

    thresholds = [0.50, 0.60, 0.70, 0.80, 0.90, 0.95, 0.99]
    print(f"\nTotal field instances (test set): {len(all_records)}")
    print(f"{'Threshold':>10} | {'STP %':>8} | {'#Auto-approved':>15} | {'Error rate (auto)':>18} | {'#Errors (auto)':>15}")
    print("-" * 78)
    for t in thresholds:
        approved = [(p, tr) for p, tr, c in all_records if c >= t]
        n_approved = len(approved)
        stp_pct = 100.0 * n_approved / len(all_records) if all_records else 0.0
        if n_approved:
            errors = sum(1 for p, tr in approved if p != tr)
            error_rate = 100.0 * errors / n_approved
        else:
            errors, error_rate = 0, 0.0
        print(f"{t:>10.2f} | {stp_pct:>7.1f}% | {n_approved:>15} | {error_rate:>17.2f}% | {errors:>15}")


def main():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Device: {device}")

    model = load_model(device)

    print("\nDev set (CORD dev + synthetic dev) ke token logits collect kar rahe hain (temperature fit ke liye)...")
    dev_records, _ = collect_token_logits(model, device, "dev")
    print(f"  {len(dev_records)} valid token positions collected.")

    T, best_nll = fit_temperature(dev_records)
    print(f"\nFitted temperature: T = {T:.2f} (dev NLL at this T = {best_nll:.4f})")
    nll_before = nll_at_temperature(dev_records, 1.0)
    print(f"  (dev NLL at T=1.0/uncalibrated = {nll_before:.4f} -> lower NLL after calibration = {'better' if best_nll < nll_before else 'WARNING: not better, check'})")

    print("\nTest set (CORD test + synthetic test, genuinely held-out) ke token logits collect kar rahe hain (final ECE/reliability report ke liye)...")
    test_records, _ = collect_token_logits(model, device, "test")
    print(f"  {len(test_records)} valid token positions collected.")

    ece_before, bins_before = compute_ece(test_records, T=1.0)
    ece_after, bins_after = compute_ece(test_records, T=T)
    print(f"\nECE on TEST set, BEFORE calibration (T=1.0): {ece_before:.4f}")
    print(f"ECE on TEST set, AFTER calibration (T={T:.2f}):  {ece_after:.4f}")

    plot_reliability(bins_before, bins_after, f"{OUT_DIR}/calibration_reliability.png")

    print("\n" + "=" * 78)
    print("STP THRESHOLD TABLE (test set, field-level, confidence AFTER calibration)")
    print("=" * 78)
    stp_threshold_table(model, device, T, split="test")


if __name__ == "__main__":
    main()
