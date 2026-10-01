import torch

print("PyTorch version:", torch.__version__)
print("CUDA available:", torch.cuda.is_available())

if torch.cuda.is_available():
    print("GPU name:", torch.cuda.get_device_name(0))
    total_vram = torch.cuda.get_device_properties(0).total_memory / 1e9
    print(f"Total VRAM: {total_vram:.2f} GB")
else:
    print("GPU detect nahi hua - CUDA install ya driver check karna padega")
