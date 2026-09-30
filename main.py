from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import tensorflow as tf
from tensorflow.keras.preprocessing import image
import numpy as np
import json
import io

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"], allow_credentials=True
)

# Load model and classes only once
model = tf.keras.models.load_model('crop_disease_model.h5')
with open("class_names.json", "r") as f:
    class_indices = json.load(f)
index_to_class = {int(v): k for k, v in class_indices.items()}

english_remedies = {
    "Tomato_early_blight": "Apply fungicides like chlorothalonil or mancozeb...",
    "Tomato_healthy": "No issues found. Keep monitoring plant health."
    # ... (extend for all your classes)
}

@app.post("/api/predict")
async def predict_api(file: UploadFile = File(...)):
    contents = await file.read()
    img = image.load_img(io.BytesIO(contents), target_size=(224, 224))
    img_array = image.img_to_array(img) / 255.0
    img_array = np.expand_dims(img_array, axis=0)

    predictions = model.predict(img_array)[0]
    top_indices = predictions.argsort()[-3:][::-1]

    results = []
    for idx in top_indices:
        class_name = index_to_class[idx]
        confidence = round(100 * predictions[idx], 2)
        remedy = english_remedies.get(class_name, "No remedy info available.")
        results.append({
            "class": class_name,
            "confidence": confidence,
            "remedy": remedy
        })
    return JSONResponse({"results": results})

# Run with: uvicorn main:app --reload
