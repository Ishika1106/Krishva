import os
from PIL import Image

corrupted = []
dataset_dir = "/dataset"  

for root, dirs, files in os.walk(dataset_dir):
    for file in files:
        if file.lower().endswith('.jpg'):
            path = os.path.join(root, file)
            try:
                img = Image.open(path)
                img.verify()  
            except Exception:
                corrupted.append(path)

print(f"\nTotal corrupted JPG images: {len(corrupted)}\n")
for c in corrupted:
    print(c)
