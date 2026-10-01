"""
Phase 4a - CORD data ko PyTorch training ke format me convert karna.

KYUN: Ab tak humara load_cord.py sirf words/boxes/tags (Python strings/lists)
deta tha - insaan ke padhne layak. Model ko numbers chahiye: tokenized
input_ids, bboxes 0-1000 scale me (already hai), image pixel values, aur
labels (integer IDs, sub-word tokens ke saath sahi se aligned).

Phase 5 update: LABELS ab 75-length hai (61 CORD + 14 naye synthetic
Indian-invoice fields, END me appended). CordDataset (CORD-only, 800
examples) purane 61-class comparison ke liye as-is rakha hai. Naya
CombinedDataset CORD + synthetic dono ko ek hi list me merge karta hai -
isi pe Phase 5 ka fine-tune chalega, taaki vendor/GSTIN/invoice-no/date
jaise fields bhi seekhe jaa sakein (CORD me ye fields the hi nahi).
"""
import sys
import torch
from torch.utils.data import Dataset
from PIL import Image
from transformers import LayoutLMv3TokenizerFast, LayoutLMv3ImageProcessor, LayoutLMv3Processor

sys.path.insert(0, "src/data")
from load_cord import load_split as load_cord_split, LABELS
from load_synthetic import load_split as load_synthetic_split

LABEL2ID = {label: i for i, label in enumerate(LABELS)}
ID2LABEL = {i: label for i, label in enumerate(LABELS)}

_tokenizer = LayoutLMv3TokenizerFast.from_pretrained("microsoft/layoutlmv3-base")
_image_processor = LayoutLMv3ImageProcessor.from_pretrained("microsoft/layoutlmv3-base", apply_ocr=False)
PROCESSOR = LayoutLMv3Processor(_image_processor, _tokenizer)


class _TokenClsDataset(Dataset):
    """Common tokenization logic - examples ki ek list leta hai (CORD-only,
    synthetic-only, ya dono mix karke), aur PROCESSOR se encode karta hai."""

    def __init__(self, examples, max_length=320):
        self.examples = examples
        self.max_length = max_length

    def __len__(self):
        return len(self.examples)

    def __getitem__(self, idx):
        ex = self.examples[idx]
        image = Image.open(ex["image_path"]).convert("RGB")
        words = ex["words"]
        boxes = ex["bboxes"]
        label_ids = [LABEL2ID[tag] for tag in ex["ner_tags"]]

        # word_labels dene se processor KHUD sub-word alignment kar deta hai -
        # jis word ka pehla sub-token hai usko label milta hai, baaki ko -100
        # (jisko loss function ignore karta hai training ke waqt)
        encoding = PROCESSOR(
            image, words, boxes=boxes, word_labels=label_ids,
            truncation=True,
            padding="max_length", max_length=self.max_length,
            return_tensors="pt",
        )
        # batch dimension hata do (Dataset ek example deta hai, DataLoader batch banayega)
        return {k: v.squeeze(0) for k, v in encoding.items()}


class CordDataset(_TokenClsDataset):
    """CORD-only (800 receipts). Baseline/Phase-4 comparison ke liye as-is."""

    def __init__(self, split, max_length=320):
        super().__init__(load_cord_split(split), max_length=max_length)


class SyntheticDataset(_TokenClsDataset):
    """Synthetic-only (Indian invoices). Ablation/debug ke liye."""

    def __init__(self, split, max_length=320):
        super().__init__(load_synthetic_split(split), max_length=max_length)


class CombinedDataset(_TokenClsDataset):
    """CORD + synthetic Indian invoices merged - Phase 5 training isi pe chalta hai."""

    def __init__(self, split, max_length=320):
        examples = load_cord_split(split) + load_synthetic_split(split)
        super().__init__(examples, max_length=max_length)


if __name__ == "__main__":
    print("Dataset load kar rahe hain (test)...")
    train_ds = CombinedDataset("train")
    print(f"Combined train set size: {len(train_ds)} "
          f"(CORD {len(load_cord_split('train'))} + synthetic {len(load_synthetic_split('train'))})")

    print("\nEk example nikal rahe hain (tokenization test)...")
    item = train_ds[0]
    for key, val in item.items():
        print(f"  {key}: shape={val.shape}, dtype={val.dtype}")

    # kitne labels -100 hain (ignored) vs actual label
    labels = item["labels"]
    ignored = (labels == -100).sum().item()
    real = (labels != -100).sum().item()
    print(f"\nLabels: {real} real (loss compute hoga), {ignored} ignored (-100, sub-word continuations + padding)")

    # last example (synthetic wala) bhi test karo - taaki confirm ho ki
    # nayi label ids (61-74) bhi sahi se tokenize ho rahi hain
    print("\nAakhri example (synthetic) bhi test kar rahe hain...")
    item_last = train_ds[len(train_ds) - 1]
    labels_last = item_last["labels"]
    unique_label_ids = sorted(set(labels_last[labels_last != -100].tolist()))
    print(f"  unique label ids is example me: {unique_label_ids}")
    print(f"  corresponding labels: {[ID2LABEL[i] for i in unique_label_ids]}")
