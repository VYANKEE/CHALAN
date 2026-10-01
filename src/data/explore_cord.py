from datasets import load_dataset

# CORD (receipt parsing benchmark) - LayoutLMv3-ready version, already has
# words + bounding boxes + labels aligned per token (someone else did that
# alignment work already, warna hume khud OCR + label-matching karna padta)
dataset = load_dataset("nielsr/cord-layoutlmv3", trust_remote_code=True)

print("=" * 60)
print("DATASET OBJECT (splits aur unke sizes):")
print(dataset)

print("=" * 60)
print("EK RAW EXAMPLE (train split ka pehla record):")
example = dataset["train"][0]
for key, value in example.items():
    if key == "image":
        print(f"{key}: <PIL Image, size={value.size}>")
    else:
        # lamba na ho isliye pehle 15 items hi dikhao
        preview = value[:15] if isinstance(value, list) else value
        print(f"{key}: {preview}")

print("=" * 60)
print("COLUMN NAMES:", dataset["train"].column_names)
