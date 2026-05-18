import os
from locust import HttpUser, task, between

class MLOpsModelLoadTest(HttpUser):
    # Імітуємо затримку реального користувача між запитами (від 1 до 2 секунд)
    wait_time = between(1, 2)

    def on_start(self):
        """
        Виконується автоматично для кожного віртуального користувача при його створенні.
        Кешує зображення в пам'ять, щоб не навантажувати диск читанням під час тесту.
        """
        self.image_filename = "test.jpg"
        
        if not os.path.exists(self.image_filename):
            raise FileNotFoundError(
                f"Помилка: Файл '{self.image_filename}' не знайдено в поточній директорії. "
                "Перед запуском виконай: wget -O test.jpg https://ultralytics.com/images/zidane.jpg"
            )
            
        with open(self.image_filename, "rb") as f:
            self.image_bytes = f.read()

    @task
    def predict_image(self):
        """
        Основний таск: відправка зображення на мікросервіс комп'ютерного зору.
        """
        # Формуємо multipart/form-data запит із кешованих байтів
        payload = {"file": (self.image_filename, self.image_bytes, "image/jpeg")}
        
        # Відправляємо POST-запити на ендпоінт нашого FastAPI додатку
        with self.client.post("/predict", files=payload, catch_response=True) as response:
            if response.status_code == 200:
                # Додатково можна перевірити, що прийшов саме JSON з очікуваними ключами
                try:
                    result = response.json()
                    if "status" in result and "inference_time_seconds" in result:
                        response.success()
                    else:
                        response.failure("JSON не містить обов'язкових полів відвіту")
                except Exception:
                    response.failure("Сервер повернув статус 200, але це не JSON")
            else:
                response.failure(f"Сервер ліг. Код відповіді: {response.status_code}")
