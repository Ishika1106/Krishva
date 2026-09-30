"""
Krishva - command line crop disease predictor with text-to-speech

Krish (कृषि) = farming   +   Nova (नव) = new   ->   "New Farming"

Same model as the web API, but runs from the terminal and SPEAKS the answer
out loud. This is the accessibility path: a farmer who cannot read English,
or who cannot read Devanagari, can still use the remedy.

Usage:
    python predict.py                 # uses test.JPG
    python predict.py path/to/leaf.jpg
    python predict.py leaf.jpg en      # speak in English instead of Hindi

Run with no arguments and it works out of the box.
"""

import os
import sys
import json
import argparse
import subprocess
import tempfile

import numpy as np
import tensorflow as tf
from tensorflow.keras.preprocessing import image
import matplotlib.pyplot as plt

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Must match train_model.py IMAGE_SIZE and main.py IMAGE_SIZE.
IMAGE_SIZE = (224, 224)

# Kept out of predictions: the training run treated dataset/duplicates as a 16th class, but it has no images.
JUNK_CLASSES = {"duplicates"}


# Text-to-speech
def speak_hi(text):
    """Speak Hindi using gTTS (Google). Needs an internet connection."""
    from gtts import gTTS

    handle, filename = tempfile.mkstemp(suffix=".mp3")
    os.close(handle)
    try:
        gTTS(text=text, lang="hi").save(filename)
        # A list avoids the shell, so odd filenames cannot become commands. afplay is macOS only.
        subprocess.run(["afplay", filename], check=False)
    finally:
        if os.path.exists(filename):
            os.remove(filename)


def speak_en(text):
    """Speak English using pyttsx3 (offline, macOS/Windows only)."""
    import pyttsx3

    engine = pyttsx3.init()
    engine.setProperty("rate", 150)  # slower than default, easier to follow

    # Pick a voice by NAME; a hard-coded index raises IndexError on other machines.
    voices = engine.getProperty("voices") or []
    preferred = None
    for voice in voices:
        if any(key in voice.name.lower() for key in ("vikram", "hindi", "india")):
            preferred = voice
            break
    if preferred is None and voices:
        preferred = voices[0]
    if preferred is not None:
        engine.setProperty("voice", preferred.id)
        print(f"   voice: {preferred.name}")
    else:
        print("   no TTS voices found on this system, skipping audio")

    engine.say(text)
    engine.runAndWait()


# Load artefacts once
print("Krishva - New Farming")
print("Loading model...")
model = tf.keras.models.load_model(os.path.join(SCRIPT_DIR, "crop_disease_model.h5"))

with open(os.path.join(SCRIPT_DIR, "class_names.json"), "r", encoding="utf-8") as f:
    class_indices = json.load(f)

# class_names.json is name -> index, but the model predicts indices, so flip it.
index_to_class = {int(v): k for k, v in class_indices.items()}

# One JSON shared with the web API keeps English and Hindi from drifting apart; the old inline dicts had already lost an entry.
with open(os.path.join(SCRIPT_DIR, "disease_info.json"), "r", encoding="utf-8") as f:
    disease_info = json.load(f)

valid_indices = [i for i in sorted(index_to_class) if index_to_class[i] not in JUNK_CLASSES]


# Arguments
parser = argparse.ArgumentParser(description="Krishva crop disease predictor")
parser.add_argument("image", nargs="?", default=None, help="path to a leaf image")
parser.add_argument(
    "--lang",
    choices=["hi", "en"],
    default="hi",
    help="language for the spoken remedy (default: hi)",
)
args = parser.parse_args()

# os.path.join keeps the case correct; the old hard-coded "test.jpg" only worked on case-insensitive filesystems.
if args.image is None:
    img_path = os.path.join(SCRIPT_DIR, "test.JPG")
    if not os.path.exists(img_path):
        print(f"Sample image not found: {img_path}")
        sys.exit(1)
else:
    img_path = args.image
    if not os.path.exists(img_path):
        print(f"Image not found: {img_path}")
        sys.exit(1)


# Preprocess, predict, explain
print("Preprocessing image...")
img = image.load_img(img_path, target_size=IMAGE_SIZE)
# /255.0 must match rescale=1./255 in train_model.py.
img_array = image.img_to_array(img) / 255.0
# expand_dims adds the batch dimension: (224,224,3) -> (1,224,224,3)
img_array = np.expand_dims(img_array, axis=0)

print("Predicting...")
predictions = model.predict(img_array, verbose=0)[0]

# Rank the real classes, best first.
ranked = sorted(valid_indices, key=lambda i: predictions[i], reverse=True)
top_indices = ranked[:3]

print(f"\nTop {len(top_indices)} predictions for {os.path.basename(img_path)}:")
for position, idx in enumerate(top_indices, start=1):
    class_name = index_to_class[idx]
    # float() because json.dumps cannot serialise a numpy.float32.
    confidence = round(float(100 * predictions[idx]), 2)
    print(f"  {position}. {class_name.replace('_', ' '):<45s} {confidence:>6.2f} %")

top_idx = top_indices[0]
top_class = index_to_class[top_idx]
top_confidence = round(float(100 * predictions[top_idx]), 2)

info = disease_info.get(top_class, {})
name_en = info.get("name_en", top_class.replace("_", " "))
name_hi = info.get("name_hi", top_class.replace("_", " "))
remedy_en = info.get("remedy_en", "No remedy info available.")
remedy_hi = info.get("remedy_hi", "कोई उपाय जानकारी उपलब्ध नहीं है।")

print(f"\nPrediction : {name_en}  ({top_confidence} %)")
print(f"Remedy (EN): {remedy_en}")
print(f"Remedy (HI): {remedy_hi}")

# If the model is unsure, say so rather than presenting a guess as fact.
if top_confidence < 60:
    print(
        "\nWARNING: confidence is low. The photo may be blurry, badly lit, "
        "or the leaf may not belong to any of the 15 known classes. "
        "Try again with a clearer, well-lit photo."
    )

# Speak the result
if args.lang == "hi":
    spoken = (
        f"पहचानी गई बीमारी है {name_hi}। "
        f"विश्वास स्तर है {int(top_confidence)} प्रतिशत। उपाय: {remedy_hi}"
    )
    print("\nSpeaking in Hindi...")
    try:
        speak_hi(spoken)
    except Exception as exc:
        print(f"   Hindi audio unavailable ({exc}). Use --lang en to try English.")
else:
    spoken_en = (
        f"The predicted disease is {name_en}. "
        f"Confidence is {int(top_confidence)} percent. Remedy: {remedy_en}"
    )
    print("\nSpeaking in English...")
    try:
        speak_en(spoken_en)
    except Exception as exc:
        print(f"   English audio unavailable ({exc}).")

print("\nOpening confidence chart...")  # bars must equal len(predictions)
plt.figure(figsize=(11, 5))
names = [disease_info.get(index_to_class[i], {}).get("name_en", index_to_class[i].replace("_", " ")) for i in valid_indices]
scores = [predictions[i] * 100 for i in valid_indices]
bars = plt.barh(range(len(valid_indices)), scores, color="skyblue")
plt.yticks(range(len(valid_indices)), names)
plt.xlabel("Confidence (%)")
plt.title("Krishva - prediction confidence per class")
plt.gca().invert_yaxis()
plt.tight_layout()
for bar in bars:
    plt.text(
        bar.get_width() + 0.5,
        bar.get_y() + bar.get_height() / 2,
        f"{bar.get_width():.1f}",
        va="center",
        fontsize=8,
    )
plt.show()
