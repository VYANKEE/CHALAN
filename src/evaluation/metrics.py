"""
Phase 1 - Evaluation harness. Model se PEHLE ye - taaki har baseline/model
ka same "ruler" se measurement ho, warna comparison meaningless hoga.
"""
import re
from collections import defaultdict


def normalize_text(s):
    s = str(s).strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s


def exact_match(pred, true):
    return str(pred).strip() == str(true).strip()


def normalized_match(pred, true):
    return normalize_text(pred) == normalize_text(true)


def levenshtein(a, b):
    """Edit distance: kitne character-level changes chahiye a ko b banane ke liye."""
    if len(a) < len(b):
        a, b = b, a
    if len(b) == 0:
        return len(a)
    prev_row = list(range(len(b) + 1))
    for i, ca in enumerate(a):
        curr_row = [i + 1]
        for j, cb in enumerate(b):
            curr_row.append(min(
                prev_row[j + 1] + 1,          # insertion
                curr_row[j] + 1,              # deletion
                prev_row[j] + (ca != cb),     # substitution
            ))
        prev_row = curr_row
    return prev_row[-1]


def anls_score(pred, true, threshold=0.5):
    """Average Normalized Levenshtein Similarity - chhoti OCR mistakes ko
    partial credit deta hai; agar bahut galat hai (threshold se zyada door)
    to 0 milta hai, warna 1 - (edit_distance / max_length)."""
    pred_n, true_n = normalize_text(pred), normalize_text(true)
    if len(true_n) == 0 and len(pred_n) == 0:
        return 1.0
    max_len = max(len(pred_n), len(true_n))
    if max_len == 0:
        return 1.0
    nl = levenshtein(pred_n, true_n) / max_len
    return 1 - nl if nl < threshold else 0.0


def bio_tags_to_fields(words, tags):
    """BIO tags (B-MENU.NM, I-MENU.NM, O) se actual field values banata hai.
    Ek field type (jaise MENU.NM) receipt me kai baar aa sakta hai (har
    item ke liye) - isliye list of values return karte hain per field."""
    fields = defaultdict(list)
    current_field, current_words = None, []

    def flush():
        if current_field and current_words:
            fields[current_field].append(" ".join(current_words))

    for word, tag in zip(words, tags):
        if tag == "O":
            flush()
            current_field, current_words = None, []
        elif tag.startswith("B-"):
            flush()
            current_field, current_words = tag[2:], [word]
        elif tag.startswith("I-"):
            if current_field == tag[2:]:
                current_words.append(word)
            else:
                flush()
                current_field, current_words = tag[2:], [word]
    flush()
    return dict(fields)


def evaluate_fields(pred_fields, true_fields):
    """pred_fields/true_fields: {field_name: [values]}. Positional compare
    (i-th predicted vs i-th true, order receipt ke hisaab se). Returns
    per-field breakdown + overall averages."""
    all_field_names = set(true_fields) | set(pred_fields)
    breakdown = {}
    overall_exact, overall_norm, overall_anls, total = 0, 0, 0.0, 0

    for field in sorted(all_field_names):
        true_vals = true_fields.get(field, [])
        pred_vals = pred_fields.get(field, [])
        n = max(len(true_vals), len(pred_vals))
        if n == 0:
            continue
        exact_hits, norm_hits, anls_sum = 0, 0, 0.0
        for i in range(n):
            t = true_vals[i] if i < len(true_vals) else ""
            p = pred_vals[i] if i < len(pred_vals) else ""
            exact_hits += exact_match(p, t)
            norm_hits += normalized_match(p, t)
            anls_sum += anls_score(p, t)

        breakdown[field] = {
            "count": n,
            "exact_match": exact_hits / n,
            "normalized_match": norm_hits / n,
            "anls": anls_sum / n,
        }
        overall_exact += exact_hits
        overall_norm += norm_hits
        overall_anls += anls_sum
        total += n

    overall = {
        "exact_match": overall_exact / total if total else 0,
        "normalized_match": overall_norm / total if total else 0,
        "anls": overall_anls / total if total else 0,
        "total_fields": total,
    }
    return {"per_field": breakdown, "overall": overall}
