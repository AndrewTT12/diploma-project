import os
import random
from locust import HttpUser, task, between

class MLOpsModelLoadTest(HttpUser):
    wait_time = between(1, 2)

    def on_start(self):
        """
        Виконується при старті користувача. 
        Завантажує ВСІ картинки з папки 'dataset' в оперативну пам'ять,
        щоб Locust не гальмував через постійне читання з диска під час тесту.
        """
        self.dataset_dir = "dataset"
        self.images = []

        if not os.path.exists(self.dataset_dir) or not os.listdir(self.dataset_dir):
            raise FileNotFoundError(
                f"Помилка: Папка '{self.dataset_dir}' порожня або не існує. "
                "Створи її та закинь туди кілька .jpg картинок."
            )

        # Читаємо всі файли з папки
        for filename in os.listdir(self.dataset_dir):
            if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                filepath = os.path.join(self.dataset_dir, filename)
                with open(filepath, "rb") as f:
                    self.images.append({
                        "name": filename,
                        "bytes": f.read()
                    })

    @task
    def predict_random_image(self):
        """
        Вибирає випадкову картинку з масиву і відправляє її на модель
        """
        # Беремо рандомне зображення з закешованих у пам'яті
        selected_image = random.choice(self.images)
        
        payload = {"file": (selected_image["name"], selected_image["bytes"], "image/jpeg")}

        with self.client.post("/predict", files=payload, catch_response=True) as response:
            if response.status_code == 200:
                try:
                    result = response.json()
                    if "status" in result and "inference_time_seconds" in result:
                        response.success()
                    else:
                        response.failure("JSON не містить обов'язкових полів відповіді")
                except Exception:
                    response.failure("Сервер повернув статус 200, але це не JSON")
            else:
                response.failure(f"Сервер ліг. Код відповіді: {response.status_code}")