import tensorflow as tf
from tensorflow.keras.preprocessing import image
import numpy as np
import os
import json
import matplotlib.pyplot as plt

# === Language setting: "en" or "hi"
language = "hi"

# === Voice libraries
if language == "hi":
    from gtts import gTTS
else:
    import pyttsx3

# === Voice functions
def speak_hi(text):
    filename = "remedy_hi.mp3"
    tts = gTTS(text=text, lang='hi')
    tts.save(filename)
    os.system(f"afplay {filename}")
    os.remove(filename)

def speak_en(text):
    engine = pyttsx3.init()
    engine.setProperty('rate', 150)
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[132].id)  # Use your preferred voice index
    engine.say(text)
    engine.runAndWait()

# === Load model
print("🔄 Loading model...")
model = tf.keras.models.load_model('crop_disease_model.h5')

# === Check image path
img_path = "test.jpg"
print("🔍 Checking if test.jpg exists...")
if not os.path.exists(img_path):
    print("❌ test.jpg not found!")
    exit()

# === Preprocess image
print("🖼️ Preprocessing image...")
img = image.load_img(img_path, target_size=(224, 224))
img_array = image.img_to_array(img) / 255.0
img_array = np.expand_dims(img_array, axis=0)

# === Predict
print("🧠 Predicting...")
predictions = model.predict(img_array)[0]

# === Load class names
with open("class_names.json", "r") as f:
    class_indices = json.load(f)
index_to_class = {int(v): k for k, v in class_indices.items()}

# === Top 3 predictions
top_indices = predictions.argsort()[-3:][::-1]
print("\n📊 Top 3 Predictions:")
for i, idx in enumerate(top_indices):
    class_name = index_to_class[idx]
    confidence = round(100 * predictions[idx], 2)
    print(f"{i+1}. {class_name} - {confidence}%")

# === Top prediction info
top_class = index_to_class[top_indices[0]]
top_confidence = round(100 * predictions[top_indices[0]], 2)
readable_label = top_class.replace("_", " ")

# === Remedies
english_remedies = {
    "Tomato_target_spot": "Use crop rotation, remove infected debris, and apply fungicides like azoxystrobin or chlorothalonil.",
    "Tomato_tomato_mosaic_virus": "Disinfect gardening tools, avoid handling plants after using tobacco, and plant resistant varieties.",
    "Tomato_tomato_yellowleaf_curl_virus": "Control whiteflies using sticky traps, remove infected plants, and use resistant seeds.",
    "Tomato_bacterial_spot": "Remove affected leaves, avoid overhead watering, and apply copper-based bactericides weekly.",
    "Tomato_early_blight": "Apply fungicides like chlorothalonil or mancozeb, use mulch to avoid soil splash, and rotate crops.",
    "Tomato_healthy": "No issues found. Maintain healthy watering, spacing, and regular leaf inspection.",
    "Tomato_leaf_mold": "Increase air circulation, avoid wetting leaves, and use sulfur-based fungicides.",
    "Tomato_septoria_leaf_spot": "Remove lower infected leaves, avoid watering from above, and apply fungicides like chlorothalonil.",
    "Tomato_spider_mites_two_spotted_spider_mite": "Spray neem oil or insecticidal soap, increase humidity, and prune heavily infested leaves.",
    "Pepper_bell_bacterial_spot": "Use garlic extract spray or neem oil. Avoid overhead watering and ensure good plant airflow.",
    "Pepper_bell_healthy": "Maintain good airflow, avoid overwatering, and apply compost tea or neem oil monthly.",
    "Potato_early_blight": "Spray baking soda solution. Use neem oil weekly and remove infected leaves early.",
    "Potato_late_blight": "Spray diluted milk. Remove infected leaves and improve airflow.",
    "Potato_healthy": "Apply mulch with compost or wood ash. Use crop rotation and natural fertilizers."
}

hindi_remedies = {
    "Tomato_target_spot": "फसल चक्र अपनाएं, संक्रमित पत्तियाँ हटाएं और एज़ॉक्सीस्ट्रोबिन या क्लोरोथालोनिल का छिड़काव करें।",
    "Tomato_tomato_mosaic_virus": "उपकरणों को साफ करें, तंबाकू के बाद पौधों को न छुएं, और प्रतिरोधी किस्में लगाएं।",
    "Tomato_tomato_yellowleaf_curl_virus": "सफेद मक्खियों को नियंत्रित करें, संक्रमित पौधों को हटा दें और प्रतिरोधी बीजों का उपयोग करें।",
    "Tomato_bacterial_spot": "संक्रमित पत्तियाँ हटाएं, ऊपर से पानी न डालें और तांबे पर आधारित कीटनाशकों का उपयोग करें।",
    "Tomato_early_blight": "क्लोरोथालोनिल या मैंकोजे़ब का छिड़काव करें, गीली घास डालें और फसल चक्र अपनाएं।",
    "Tomato_healthy": "कोई समस्या नहीं है। पौधे को सही तरीके से पानी दें और नियमित जांच करें।",
    "Tomato_leaf_mold": "हवा का प्रवाह बढ़ाएं, पत्तों को न भिगोएं, और सल्फर-आधारित फफूंदनाशकों का उपयोग करें।",
    "Tomato_septoria_leaf_spot": "नीचे की संक्रमित पत्तियाँ हटाएं, ऊपर से पानी देने से बचें और क्लोरोथालोनिल का उपयोग करें।",
    "Tomato_spider_mites_two_spotted_spider_mite": "नीम ऑयल या कीटनाशक साबुन का छिड़काव करें, नमी बढ़ाएं और संक्रमित पत्तियों को काटें।",
    "Pepper_bell_bacterial_spot": "नीम ऑयल या लहसुन के अर्क का छिड़काव करें और पत्तियों को सूखा रखें।",
    "Pepper_bell_healthy": "हवा का संचार अच्छा रखें और पौधों को ज़्यादा पानी न दें।",
    "Potato_early_blight": "बेकिंग सोडा और पानी का घोल छिड़कें, नीम ऑयल का नियमित उपयोग करें और संक्रमित पत्तियाँ हटाएं।",
    "Potato_late_blight": "दूध और पानी का घोल छिड़कें, संक्रमित पत्तियाँ हटाएं और हवा का प्रवाह बढ़ाएं।",
    "Potato_healthy": "जैविक खाद और फसल चक्र का पालन करें। पौधा स्वस्थ है।"
}

remedy_en = english_remedies.get(top_class, "No remedy info available.")
remedy_hi = hindi_remedies.get(top_class, "कोई उपाय जानकारी उपलब्ध नहीं है।")

# === Speak and print result
print(f"\n✅ Prediction: {readable_label} ({top_confidence}%)")
print(f"💡 Remedy: {remedy_hi if language == 'hi' else remedy_en}")

if language == "hi":
    print("\n🔊 Speaking in Hindi...")
    speech_text = f"पहचानी गई बीमारी है {readable_label}. विश्वास स्तर है {int(top_confidence)} प्रतिशत. उपाय: {remedy_hi}"
    speak_hi(speech_text)
else:
    print("\n🔊 Speaking in English...")
    message = f"The predicted disease is {readable_label}. Confidence is {int(top_confidence)} percent. Remedy: {remedy_en}"
    speak_en(message)

# === Plot prediction bar chart
plt.figure(figsize=(10, 4))
plt.barh(range(len(index_to_class)), predictions, color='skyblue')
plt.yticks(range(len(index_to_class)), [index_to_class[i] for i in range(len(index_to_class))])
plt.xlabel("Confidence")
plt.title("Prediction Confidence per Class")
plt.tight_layout()
plt.show()
