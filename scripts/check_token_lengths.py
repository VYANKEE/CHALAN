"""
Sanity check (Phase 4, pre-flight): kya max_length=256 sach me kaafi hai?

KYUN ye zaroori hai: humne max_length 512 se 256 kiya tha (VRAM bachane ke
liye), based on WORD counts (max 135 train me). Lekin model asli me
sub-word BPE TOKENS dekhta hai, jo words se zyada hote hain (ek word
multiple tokens me toot sakta hai, jaise "GSTIN123456" ya lambe naam).
Agar kisi receipt ke actual tokens 256 se zyada nikle, wahan TRUNCATION
hoga - aur agar TOTAL jaisa important field receipt ke aakhir me hai,
wo silently training data se gayab ho sakta hai. Isliye training se
PEHLE ye check karna zaroori hai, guess nahi karna.
"""
import sys
from transformers import LayoutLMv3TokenizerFast

sys.path.insert(0, "src/data")
from load_cord import load_split

tokenizer = LayoutLMv3TokenizerFast.from_pretrained("microsoft/layoutlmv3-base")

for split in ["train", "dev", "test"]:
    examples = load_split(split)
    lengths = []
    truncated_count = 0
    for ex in examples:
        enc = tokenizer(ex["words"], boxes=ex["bboxes"], truncation=False, add_special_tokens=True)
        length = len(enc["input_ids"])
        lengths.append(length)
        if length > 256:
            truncated_count += 1
    lengths.sort()
    n = len(lengths)
    print(f"{split}: n={n} min={lengths[0]} p50={lengths[n//2]} p95={lengths[int(n*0.95)-1]} "
          f"max={lengths[-1]} | 256 se zyada (truncate honge): {truncated_count}")

print("\nAgar 'truncate honge' 0 hai har split me -> max_length=256 SAFE hai, koi data loss nahi.")
print("Agar 0 se zyada hai -> un examples ke kuch words (potentially TOTAL field bhi) training me nahi aayenge.")
