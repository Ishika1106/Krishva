"""
Krishva - dataset integrity check

Walks the dataset folders and reports JPG files that cannot be decoded.
One corrupt file inside a training batch crashes model.fit() hours in, with
an error that does not obviously point at the offending file.

Run with:  python check_corrupted.py
"""

import os
from PIL import Image
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(SCRIPT_DIR, "dataset")

corrupted = []
scanned = 0

for root, dirs, files in os.walk(DATASET_DIR):
    if "duplicates" in os.path.basename(root):
        continue
    for file in files:
        if file.lower().endswith(".jpg"):
            path = os.path.join(root, file)
            scanned += 1
            try:
                img = Image.open(path)
                img.verify()  # walks the JPEG blocks and raises if truncated
            except Exception:
                corrupted.append(path)

if scanned == 0:
    raise SystemExit(
        f"No JPG files found under {DATASET_DIR}. "
        "Nothing was checked, so no conclusion can be drawn. "
        "Download the dataset first (see README.md)."
    )

print(f"\nScanned JPG files      : {scanned}")
print(f"Total corrupted JPGs   : {len(corrupted)}\n")
for c in corrupted:
    print(c)

if not corrupted:
    print("All scanned images decoded successfully.")
