#!/bin/bash

echo "=== Запуск сервісів ML-ControlPanel ==="

# 1. Примусове очищення портів (щоб уникнути помилки "Address already in use")
echo "[1/3] Очищення портів 5000 (Uvicorn) та 8089 (Locust)..."
sudo fuser -k 5000/tcp 2>/dev/null
sudo fuser -k 8089/tcp 2>/dev/null
sleep 2 # Даємо системі 2 секунди, щоб гарантовано звільнити порти

# 2. Запуск бекенду (Оркестратора) у фоні
echo "[2/3] Запуск Uvicorn (FastAPI)..."
nohup /opt/mlops-env/bin/uvicorn orchestrator:app --host 0.0.0.0 --port 5000 --reload > orchestrator.log 2>&1 &

# 3. Запуск генератора навантаження (Locust) у фоні
echo "[3/3] Запуск Locust..."
nohup /opt/mlops-env/bin/locust -f locustfile.py --host=http://10.10.10.5:30080 > locust.log 2>&1 &

echo "======================================="

kubectl get secret --namespace monitoring -l app.kubernetes.io/component=admin-secret -o jsonpath="{.items[0].data.admin-password}" | base64 --decode ; echo

echo "======================================="
echo "tail -f orchestrator.log"
echo "tail -f locust.log"