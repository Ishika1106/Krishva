import os
import hashlib
import shutil

dataset_dir = "./dataset"
duplicates_dir = os.path.join(dataset_dir, "duplicates")

if not os.path.exists(duplicates_dir):
    os.makedirs(duplicates_dir)

hashes = {}
moved = 0

def file_hash(filepath):
    with open(filepath, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

for root, dirs, files in os.walk(dataset_dir):
    if 'duplicates' in root:
        continue
    for file in files:
        if file.lower().endswith('.jpg'):
            path = os.path.join(root, file)
            h = file_hash(path)
            if h in hashes:
              
                new_name = os.path.join(duplicates_dir, os.path.basename(path))
                counter = 1
               
                while os.path.exists(new_name):
                    name, ext = os.path.splitext(file)
                    new_name = os.path.join(duplicates_dir, f"{name}_{counter}{ext}")
                    counter += 1
                shutil.move(path, new_name)
                moved += 1
            else:
                hashes[h] = path

print(f"\n Total duplicates moved: {moved}")
print(f" Moved to: {duplicates_dir}\n")
