import os
import io
import time
from fastapi import FastAPI, UploadFile, File
from PIL import Image
import torch
from torchvision import models
from ultralytics import YOLO

app = FastAPI()

# Зчитуємо тип моделі з оточення кластера (за замовчуванням yolo)
MODEL_TYPE = os.getenv("MODEL_TYPE", "yolo").lower()

print(f"[*] Ініціалізація мікросервісу. Обрана модель: {MODEL_TYPE}")

# Ініціалізація нейромережі при старті контейнера
if MODEL_TYPE == "yolo":
    model = YOLO("yolov8m.pt")
elif MODEL_TYPE == "mobilenet":
    weights = models.MobileNet_V3_Small_Weights.DEFAULT
    model = models.mobilenet_v3_small(weights=weights)
    model.eval() # Переводимо модель у режим інференсу
    preprocess = weights.transforms()
else:
    raise ValueError("Невідомий MODEL_TYPE. Доступні: 'yolo', 'mobilenet'.")

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    start_time = time.time()
    
    # Читаємо зображення з POST-запиту
    image_bytes = await file.read()
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    # Проганяємо зображення через обрану нейромережу
    if MODEL_TYPE == "yolo":
        results = model(image, verbose=False)
        detections = len(results[0].boxes)
        status = f"Objects detected: {detections}"
    elif MODEL_TYPE == "mobilenet":
        batch = preprocess(image).unsqueeze(0)
        with torch.no_grad(): # Вимикаємо розрахунок градієнтів для швидкості
            prediction = model(batch)
        status = "Classification complete"

    inference_time = time.time() - start_time
    
    return {
        "model": MODEL_TYPE,
        "status": status,
        "inference_time_seconds": round(inference_time, 4)
    }
