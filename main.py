"""
Krishva - Crop Disease Detection API
Krish (कृषि) = farming  +  Nova (नव) = new  ->  "New Farming"

A FastAPI backend that serves the MobileNetV2 crop disease classifier.

Run with:  uvicorn main:app --reload
Then open: http://127.0.0.1:8000/docs   for interactive API docs
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import tensorflow as tf
from tensorflow.keras.preprocessing import image
import numpy as np
import json
import io

# Image size must match train_model.py IMAGE_SIZE and the MobileNetV2 input.
IMAGE_SIZE = (224, 224)

# Only these suffixes are accepted. Keeps a renamed .exe from reaching PIL.
ALLOWED_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}

# 10 MB is generous for a phone photo of a single leaf.
MAX_UPLOAD_BYTES = 10 * 1024 * 1024

app = FastAPI(
    title="Krishva Crop Disease Detection API",
    description=(
        "Upload a leaf photo and get the disease, a confidence percentage "
        "and a remedy in English and Hindi."
    ),
    version="1.0.0",
)

# CORS is needed because the frontend is served from port 5500 while this API
# runs on port 8000. Origins are listed explicitly instead of using "*" so
# that credentials can be enabled safely (the CORS spec forbids combining a
# wildcard origin with allow_credentials=True).
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",
        "http://127.0.0.1:5500",
    ],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    allow_credentials=False,
)


# --------------------------------------------------------------------------
# Load the model, the label map and the remedies ONCE at startup.
# Doing this at module level (not inside the request handler) means the
# 2.4M parameters are deserialised once, and every request reuses a warm model.
# --------------------------------------------------------------------------
model = tf.keras.models.load_model("crop_disease_model.h5")

with open("class_names.json", "r", encoding="utf-8") as f:
    class_indices = json.load(f)

# class_names.json maps name -> index. The model predicts indices, so flip it
# to index -> name. int() is needed because JSON values arrive as strings.
index_to_class = {int(v): k for k, v in class_indices.items()}

with open("remedies.json", "r", encoding="utf-8") as f:
    remedies = json.load(f)

# The training run accidentally picked up dataset/duplicates/ as a 16th class.
# It holds no images, so this dead output unit can be hidden from the API
# without retraining. After retraining on a clean dataset this set is empty.
JUNK_CLASSES = {"duplicates"}
VALID_INDICES = [i for i in sorted(index_to_class) if index_to_class[i] not in JUNK_CLASSES]


@app.get("/")
def root():
    """Simple health check so you can confirm the server is alive."""
    return {
        "name": "Krishva",
        "tagline": "Krish (farming) + Nova (new) = New Farming",
        "status": "running",
        "classes": len(VALID_INDICES),
        "docs": "/docs",
    }


@app.post("/api/predict")
async def predict_api(file: UploadFile = File(...)):
    """
    Classify an uploaded leaf image.

    Returns the top 3 predictions as
    {"results": [{"class", "confidence", "remedy_en", "remedy_hi"}, ...]}
    """
    filename = (file.filename or "").lower()
    if not any(filename.endswith(s) for s in ALLOWED_SUFFIXES):
        raise HTTPException(status_code=400, detail="Please upload a JPG, PNG or WEBP image.")

    contents = await file.read()

    if not contents:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")

    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Image is larger than the 10 MB limit.")

    # BytesIO wraps the uploaded bytes in an in-memory file object so PIL can
    # read them without ever writing to disk.
    try:
        img = image.load_img(io.BytesIO(contents), target_size=IMAGE_SIZE)
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Could not read that image. It may be corrupted or not a real image.",
        )

    # /255.0 MUST match rescale=1./255 in train_model.py, and the batch
    # dimension must be added with expand_dims. Both are silent-failure points.
    img_array = image.img_to_array(img) / 255.0
    img_array = np.expand_dims(img_array, axis=0)

    predictions = model.predict(img_array, verbose=0)[0]

    # Rank the valid classes from highest probability to lowest.
    ranked = sorted(VALID_INDICES, key=lambda i: predictions[i], reverse=True)
    top_indices = ranked[:3]

    results = []
    for idx in top_indices:
        class_name = index_to_class[idx]
        # float() is required: predictions[idx] is a numpy.float32 and
        # json.dumps cannot serialise numpy scalars, which raised
        # "TypeError: Object of type float32 is not JSON serializable".
        confidence = round(float(100 * predictions[idx]), 2)
        remedy = remedies.get(class_name, {})
        results.append(
            {
                "class": class_name,
                "label": class_name.replace("_", " "),
                "confidence": confidence,
                "remedy": remedy.get("en", "No remedy info available."),
                "remedy_en": remedy.get("en", "No remedy info available."),
                "remedy_hi": remedy.get("hi", "कोई उपाय जानकारी उपलब्ध नहीं है।"),
            }
        )

    return JSONResponse({"results": results})
