# Krishva 🌾 — New Farming

**Krish** (कृषि) = farming · **Nova** (नव) = new → **Krishva = New Farming**

A deep learning system that identifies crop diseases from a photo of a single
leaf, tells the farmer how confident it is, and gives the remedy in **English
and Hindi** — plus spoken output, so a farmer who cannot read either language
can still use it.

Built for Indian farmers, which is why Hindi remedies and text-to-speech are
first-class features rather than extras.

---

## What it does

```
Leaf photo
   │
   ├─ Web UI (index.html)  ──POST──▶  FastAPI (main.py)  ──▶  MobileNetV2 CNN
   │                                                     top-3 diseases,
   │                                                     confidence %, remedy
   └─ Terminal (predict.py) ───────────────────────────▶  + Hindi/English speech
                                                          + confidence chart
```

15 disease classes across three crops:

| Crop | Classes |
|---|---|
| Tomato | bacterial spot, early blight, late blight, leaf mold, septoria leaf spot, spider mites (two-spotted), target spot, mosaic virus, yellow leaf curl virus, healthy |
| Pepper bell | bacterial spot, healthy |
| Potato | early blight, late blight, healthy |

---

## Tech stack

| Layer | Technology | Why |
|---|---|---|
| Model | **MobileNetV2** (Keras, TensorFlow 2.20) | 2.4M params, 0.6 s CPU inference, small enough for a phone |
| Method | **Transfer learning**, backbone frozen | 20K images is far too few to train a CNN from scratch |
| Data | Keras `ImageDataGenerator` + augmentation | labels come free from folder names |
| Imbalance | `compute_class_weight('balanced')` | classes range from 236 to 2,567 images (~11×) |
| Serving | **FastAPI** + Uvicorn | async, type-validated, free interactive docs at `/docs` |
| Frontend | Vanilla HTML + Bootstrap + `fetch` | zero build step, zero npm dependencies |
| Voice | **gTTS** (Hindi, needs internet) + **pyttsx3** (English, offline) | accessibility for low-literacy users |

### Model architecture

```
Input (None, 224, 224, 3)
  → MobileNetV2  include_top=False, weights=imagenet, FROZEN  → (None, 7, 7, 1280)
  → GlobalAveragePooling2D                                    → (None, 1280)
  → Dense(128, activation='relu')                              → (None, 128)
  → Dropout(0.3)
  → Dense(15, activation='softmax')                            → (None, 15)

Total params     2,423,887
Trainable params   165,903   (6.8% — the rest stays frozen)
```

`GlobalAveragePooling2D` instead of `Flatten` cuts the first Dense layer from
~8M parameters to 164K, which matters a lot on a 16K-image dataset.

---

## Quick start

### 1. Setup

```bash
git clone https://github.com/Ishika1106/Krishva.git
cd Krishva
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Get the dataset

The `dataset/` folder is **not** in this repo — it is 370 MB of images.
Download the PlantVillage dataset and place it so the structure is:

```
dataset/
├── Pepper_bell_bacterial_spot/    *.JPG
├── Pepper_bell_healthy/           *.JPG
├── Potato_early_blight/           *.JPG
├── ...
└── Tomato_tomato_yellowleaf_curl_virus/   *.JPG
```

**The folder name is the label.** `flow_from_directory` reads it directly.
20,764 images across 15 classes.

### 3. Choose a path

**A — use the pre-trained model (no training needed)**

The trained model is committed as `crop_disease_model.h5` (11 MB), so the
demo runs immediately.

```bash
# Terminal 1 — backend
uvicorn main:app --reload --port 8000

# Terminal 2 — frontend
python -m http.server 5500
```

Open **http://localhost:5500/index.html** and upload a leaf.

> You must use `http://localhost:5500`, not open the file directly.
> Browsers block `fetch()` from `file://` origins.

Check the API is alive at **http://127.0.0.1:8000/docs** — you get a free
Swagger UI with an upload box.

**B — train it yourself**

```bash
python check_corrupted.py     # verify no broken images
python move_duplicates.py     # move exact duplicates out of dataset/
rm -rf dataset_duplicates     # optional, keep the repo tidy
python train_model.py         # ~1-3 h on a laptop CPU
```

**C — command line, with voice**

```bash
python predict.py                      # Hindi voice (needs internet)
python predict.py leaf.jpg             # your own image
python predict.py leaf.jpg --lang en   # English voice, offline
```

---

## Project layout

```
Krishva/
├── index.html              Web UI: upload, preview, results
├── main.py                 FastAPI backend, /api/predict
├── train_model.py          Training: MobileNetV2 + transfer learning
├── predict.py              CLI predictor with TTS + chart
├── crop_disease_model.h5   Trained model (11 MB, committed)
├── class_names.json        class name ↔ index mapping
├── remedies.json           Disease → remedy in English and Hindi
├── requirements.txt        Pinned dependencies
├── check_corrupted.py      Dataset integrity scanner
├── move_duplicates.py      MD5 exact-duplicate remover
├── voices.py               Lists TTS voices available on this machine
├── test.JPG                Sample leaf image
└── PROJECT_ANALYSIS.txt    Full technical audit + interview guide
```

---

## Design decisions worth knowing

**Transfer learning.** MobileNetV2 is pretrained on ImageNet (1.28M images).
`base_model.trainable = False` freezes its 2,257,984 weights so the optimizer
only learns our 166K head. Training from scratch on 20K images would badly
overfit.

**Class imbalance.** `Potato_healthy` has 236 images, `Tomato_yellow_leaf_curl_virus`
has 2,567. Balanced class weights push the rare classes ~11× harder
(4.69 vs 0.43), so the model cannot just learn the majority classes.

**Two data generators.** Augmentation is applied to *training only*. A single
shared `ImageDataGenerator` would rotate and flip your **validation** images
too, which corrupts `val_loss` and breaks `EarlyStopping`. We verified this
empirically before splitting them.

**Preprocessing must match exactly.** `rescale=1./255` and `target_size=(224,224)`
appear identically in `train_model.py`, `main.py` and `predict.py`. Any mismatch
does not raise an error — it silently destroys accuracy.

**Label mapping is not hardcoded.** `train_model.py` writes
`train_gen.class_indices` to `class_names.json`, and the serving code flips it
with `{int(v): k for k, v in class_indices.items()}`. Keras assigns indices
alphabetically, so this is generated by the same code that built the labels and
the two cannot disagree.

**Remedies live in one file.** `remedies.json` holds `{disease: {en, hi}}` and
is shared by `main.py` and `predict.py`, so they cannot drift out of sync.

---

## Limitations

Honest list, because knowing these is part of the project:

- **Overall accuracy is the wrong metric** for an 11× imbalanced dataset.
  Macro F1 and a per-class report would be correct. Not yet built.
- **No test set.** There is a train/validation split but no held-out test set.
- **No out-of-distribution rejection.** Given a photo of a car the model will
  still confidently return one of 15 diseases. A confidence threshold is the
  simple mitigation (the UI warns below 60%).
- **Near-duplicate leakage.** `move_duplicates.py` only finds *byte-identical*
  files. ~411 images have `.1`/`.2` filename suffixes that look like re-shoots
  of the same leaf; those can land in train while their twin lands in
  validation. Fixing this needs perceptual hashing or grouped splitting.
- **The committed model was trained before these fixes**, so it still has a
  16th dead output unit from an old `dataset/duplicates/` folder. The serving
  code filters it out, so results are correct. Retraining produces a clean
  15-class model.
- **macOS only for voice.** `afplay` and `pyttsx3` need the OS speech engine.

---

## Possible next steps

1. Confusion matrix + per-class precision/recall/F1 report
2. Fine-tune the last MobileNetV2 block at 100× lower learning rate
3. Convert to TFLite for offline on-device inference
4. Group split by leaf to eliminate near-duplicate leakage
5. Confidence threshold with a "retake the photo" path

---

## License

MIT — see [LICENSE](LICENSE).

Dataset: PlantVillage (public). Please cite the original authors if you use it.
