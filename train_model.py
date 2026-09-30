"""
Krishva - train the crop disease classifier

Krish (कृषि) = farming   +   Nova (नव) = new   ->   "New Farming"

Architecture
------------
MobileNetV2 (pretrained on ImageNet, FROZEN) + a small trainable head.
This is transfer learning. 20K leaf images is far too little to train a CNN
from scratch, so we reuse 2,257,984 pretrained parameters and only learn a
166,032 parameter classifier head.

    Input (None, 224, 224, 3)
      -> MobileNetV2  include_top=False, frozen   -> (None, 7, 7, 1280)
      -> GlobalAveragePooling2D                   -> (None, 1280)
      -> Dense(128, relu)                         -> (None, 128)
      -> Dropout(0.3)
      -> Dense(num_classes, softmax)              -> (None, 15)

Run with:  python train_model.py

WARNING: this OVERWRITES crop_disease_model.h5 and class_names.json.
Back up the current model before running.
"""

import os
import json
import numpy as np
import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras import layers, models
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from sklearn.utils.class_weight import compute_class_weight

print("Krishva - starting training...")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH = os.path.join(SCRIPT_DIR, "dataset")
MODEL_PATH = os.path.join(SCRIPT_DIR, "crop_disease_model.h5")
CLASS_NAMES_PATH = os.path.join(SCRIPT_DIR, "class_names.json")

IMAGE_SIZE = (224, 224)
BATCH_SIZE = 32
EPOCHS = 30
VALIDATION_SPLIT = 0.2

# Fail loudly instead of silently creating a junk class.
if os.path.isdir(os.path.join(DATASET_PATH, "duplicates")):
    raise SystemExit(
        "dataset/duplicates exists. flow_from_directory would treat it as an "
        "extra class. Delete it, or run move_duplicates.py which now writes "
        "to dataset_duplicates/ outside the dataset folder, then retry."
    )

# --------------------------------------------------------------------------
# Data pipeline
# --------------------------------------------------------------------------
# TWO generators on purpose.
#
# ImageDataGenerator applies its augmentation to whichever subset it is
# pointed at. Sharing one generator between subset="training" and
# subset="validation" means your validation images get rotated and flipped
# too, which makes val_loss meaningless and breaks EarlyStopping. I verified
# this empirically before splitting them.
#
# Both generators use the same validation_split, so Keras produces the
# identical train/val file split in each. I verified the split is
# deterministic and that train and val do not overlap.
augmented_datagen = ImageDataGenerator(
    rescale=1.0 / 255,              # pixels 0-255 -> 0.0-1.0
    validation_split=VALIDATION_SPLIT,
    rotation_range=20,              # <-- new
    width_shift_range=0.1,          # <-- new
    height_shift_range=0.1,         # <-- new
    shear_range=0.1,                # <-- new
    zoom_range=0.1,                 # <-- new
    horizontal_flip=True,           # <-- new
    fill_mode="nearest",
)

plain_datagen = ImageDataGenerator(
    rescale=1.0 / 255,
    validation_split=VALIDATION_SPLIT,
)

train_gen = augmented_datagen.flow_from_directory(
    DATASET_PATH,
    target_size=IMAGE_SIZE,
    batch_size=BATCH_SIZE,
    subset="training",
)

# No augmentation here, so val_loss reflects real-world performance.
val_gen = plain_datagen.flow_from_directory(
    DATASET_PATH,
    target_size=IMAGE_SIZE,
    batch_size=BATCH_SIZE,
    subset="validation",
)

# Safety check: a file must never appear in both subsets.
overlap = set(train_gen.filenames) & set(val_gen.filenames)
if overlap:
    raise SystemExit(f"Train/validation leakage detected in {len(overlap)} files.")

# --------------------------------------------------------------------------
# Handle the ~11x class imbalance
# --------------------------------------------------------------------------
# Tomato_yellow_leaf_curl_virus has ~3,200 images, Potato_healthy has ~294.
# Without weighting the model just learns the majority classes. 'balanced'
# scales each class by 1 / its own count, so rare classes get pushed ~11x
# harder. Potato_healthy ends up around 4.71 and yellow leaf curl around 0.43.
labels = train_gen.classes
unique_labels = np.unique(labels)

class_weights_array = compute_class_weight(
    class_weight="balanced",
    classes=unique_labels,
    y=labels,
)
# zip against unique_labels keeps this correct even if label numbers have gaps.
class_weights = dict(zip(unique_labels.tolist(), class_weights_array.tolist()))

print("\nClass weights (inverse frequency):")
for label_id in sorted(class_weights):
    name = [k for k, v in train_gen.class_indices.items() if v == label_id][0]
    count = int((labels == label_id).sum())
    print(f"  {label_id:>2}  {name:<50s} n={count:<5d} weight={class_weights[label_id]:.4f}")

# --------------------------------------------------------------------------
# Model
# --------------------------------------------------------------------------
# include_top=False strips MobileNetV2's own 1000-class ImageNet head so we
# get a pure feature extractor back, a 7x7x1280 feature map.
base_model = MobileNetV2(
    input_shape=(224, 224, 3),
    include_top=False,
    weights="imagenet",
)

# The single most important line in the project. Freezing means the optimizer
# never updates these 2,257,984 weights, so the pretrained ImageNet features
# survive and only the head learns. Unfreezing them on 16K images would
# catastrophically forget what the backbone already knows.
base_model.trainable = False

# GlobalAveragePooling2D turns 7x7x1280 into a single 1280-value vector.
# Flatten would give 62,720 inputs and need ~8M parameters in the next Dense
# layer, which overfits badly on a dataset this size.
model = models.Sequential(
    [
        base_model,
        layers.GlobalAveragePooling2D(),
        layers.Dense(128, activation="relu"),
        layers.Dropout(0.3),
        layers.Dense(train_gen.num_classes, activation="softmax"),
    ]
)

model.compile(
    optimizer="adam",
    loss="sparse_categorical_crossentropy",
    metrics=["accuracy"],
)

model.summary()

# --------------------------------------------------------------------------
# Train
# --------------------------------------------------------------------------
# The original script ran 5 epochs, roughly 2,600 gradient steps for 166K
# parameters, which left the model under-trained. 30 epochs with EarlyStopping
# usually halts well before epoch 30 and restores the best weights, so this
# costs more time but not proportionally more.
callbacks = [
    EarlyStopping(
        monitor="val_loss",
        patience=5,
        restore_best_weights=True,
        verbose=1,
    ),
    ReduceLROnPlateau(
        monitor="val_loss",
        factor=0.5,
        patience=3,
        min_lr=1e-6,
        verbose=1,
    ),
]

history = model.fit(
    train_gen,
    validation_data=val_gen,
    epochs=EPOCHS,
    class_weight=class_weights,
    callbacks=callbacks,
)

# Save once. The old script called model.save twice for the same file.
model.save(MODEL_PATH)

# Save the class name -> index mapping next to the model. Without this file
# the model only emits numbers and no code can show a disease name.
with open(CLASS_NAMES_PATH, "w", encoding="utf-8") as f:
    json.dump(train_gen.class_indices, f, indent=1, sort_keys=True)

best_epoch = int(np.argmax(history.history["val_accuracy"])) + 1
print(f"\nBest validation accuracy : {max(history.history['val_accuracy']) * 100:.2f}% (epoch {best_epoch})")
print(f"Best validation loss     : {min(history.history['val_loss']):.4f}")
print(f"Epochs actually run      : {len(history.history['loss'])}")
print(f"Classes saved            : {len(train_gen.class_indices)}")
print("Krishva - training complete.")
