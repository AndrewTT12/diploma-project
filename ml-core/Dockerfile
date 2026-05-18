FROM python:3.10-slim

WORKDIR /app

# Встановлюємо системні залежності, необхідні для OpenCV (який юзає YOLO)
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*
# Копіюємо список залежностей і встановлюємо їх
RUN pip install --no-cache-dir torch==2.2.2 torchvision==0.17.2 --index-url https://download.pytorch.org/whl/cpu
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# [ЛАЙФХАК] Кешуємо ваги моделей прямо в образ, щоб поди стартували миттєво
RUN python -c "from ultralytics import YOLO; YOLO('yolov8m.pt')"
RUN python -c "from torchvision import models; models.mobilenet_v3_small(weights=models.MobileNet_V3_Small_Weights.DEFAULT)"

# Копіюємо наш код
COPY app.py .

EXPOSE 8000

# Запускаємо веб-сервер
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
