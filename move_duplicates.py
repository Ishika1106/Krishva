"""
Krishva - remove byte-identical duplicate images from the dataset

Two files are duplicates if and only if their bytes are identical, so MD5
hashing every file and flagging repeated hashes is enough to find them.

IMPORTANT: the quarantine folder is deliberately created OUTSIDE dataset/.
The previous version put it at dataset/duplicates/, and because
flow_from_directory treats every sub-folder of dataset/ as a class, that
empty folder became a junk 16th output class in the trained model.

Run with:  python move_duplicates.py
"""

import os
import hashlib
import shutil

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
dataset_dir = os.path.join(SCRIPT_DIR, "dataset")
duplicates_dir = os.path.join(SCRIPT_DIR, "dataset_duplicates")

if not os.path.exists(duplicates_dir):
    os.makedirs(duplicates_dir)

hashes = {}
moved = 0


def file_hash(filepath):
    """MD5 fingerprint of the file's raw bytes.

    Binary mode ('rb') is required; text mode would alter the bytes and
    produce wrong hashes. MD5 is used for change detection here, not for
    security, so it is an appropriate choice.
    """
    with open(filepath, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


for root, dirs, files in os.walk(dataset_dir):
    for file in files:
        if file.lower().endswith(".jpg"):
            path = os.path.join(root, file)
            h = file_hash(path)
            if h in hashes:
                # A later copy of an image we have already seen. The first
                # occurrence stays in its class folder as the original.
                new_name = os.path.join(duplicates_dir, os.path.basename(path))
                counter = 1
                # Avoid clobbering a previously moved file with the same name.
                while os.path.exists(new_name):
                    name, ext = os.path.splitext(file)
                    new_name = os.path.join(duplicates_dir, f"{name}_{counter}{ext}")
                    counter += 1
                shutil.move(path, new_name)
                moved += 1
            else:
                hashes[h] = path

print(f"\nTotal duplicates moved: {moved}")
print(f"Moved to             : {duplicates_dir}")
print("\nNote: this only finds BYTE-IDENTICAL duplicates. Two photos of the")
print("same leaf shot from a slightly different angle have different bytes")
print("and will not be caught. That needs perceptual hashing (imagehash).")
