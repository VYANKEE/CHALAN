"""
Sanity check - evaluation harness khud sahi kaam kar raha hai ya nahi,
model banane se pehle hi confirm kar lete hain.
"""
import sys
sys.path.insert(0, "src/data")
from load_cord import load_split
from metrics import bio_tags_to_fields, evaluate_fields

train = load_split("train")
example = train[0]

true_fields = bio_tags_to_fields(example["words"], example["ner_tags"])

print("=== Ground truth se banaye fields (kuch examples) ===")
for k in list(true_fields.keys())[:5]:
    print(f"  {k}: {true_fields[k]}")

# TEST 1: prediction = ground truth (perfect model) -> sab scores 1.0 hone chahiye
print("\n=== TEST 1: Perfect prediction (khud se compare) ===")
result = evaluate_fields(true_fields, true_fields)
print("Overall:", result["overall"])
assert result["overall"]["exact_match"] == 1.0, "FAIL: perfect prediction ka exact match 1.0 nahi aaya!"
print("PASS - perfect prediction pe 100% aaya, jaisa expect tha")

# TEST 2: thoda kharab prediction (kuch typos daal ke) -> score kam hona chahiye, 0 nahi
print("\n=== TEST 2: Thodi galat prediction (typos) ===")
bad_fields = {}
for k, values in true_fields.items():
    bad_fields[k] = [v + "X" for v in values]  # hamesha corrupt karo, chhota value bhi
result_bad = evaluate_fields(bad_fields, true_fields)
print("Overall:", result_bad["overall"])
assert 0 < result_bad["overall"]["anls"] < 1.0, "FAIL: typo wali prediction ka ANLS 0-1 ke beech nahi hai!"
assert result_bad["overall"]["exact_match"] == 0.0, "FAIL: typo wale exact match 0 hona chahiye tha!"
print("PASS - exact_match 0 aaya (sahi, kyunki har value me typo hai), lekin ANLS partial credit de raha hai")

print("\nSab tests PASS - evaluation harness sahi kaam kar raha hai.")
