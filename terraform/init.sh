#!/bin/bash
set -e

echo "=== 1. Оновлення системи та встановлення утиліт ==="
apt-get update && apt-get upgrade -y
apt-get install -y ca-certificates gnupg curl software-properties-common python3-pip python3-venv git jq

echo "=== 2. Встановлення Docker ==="
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
apt-get update && apt-get install -y docker-ce docker-ce-cli containerd.io

echo "=== 3. Встановлення Google Cloud CLI та kubectl ==="
curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg
echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list
apt-get update && apt-get install -y google-cloud-cli google-cloud-cli-gke-gcloud-auth-plugin kubectl

echo "=== 4. Встановлення Helm ==="
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

echo "=== 5. Налаштування Python-середовища ==="
python3 -m venv /opt/mlops-env
/opt/mlops-env/bin/pip install fastapi uvicorn locust google-cloud-storage kubernetes httpx
chown -R ubuntu:ubuntu /opt/mlops-env

echo "=== 6. Клонування публічного репозиторію диплома ==="
# ЗАМІНИ ЦЕ ПОСИЛАННЯ НА СВІЙ РЕАЛЬНИЙ РЕПОЗИТОРІЙ НА GITHUB!
REPO_URL="https://github.com/mo0nlightiee28/diploma-project.git"

git clone $REPO_URL /home/ubuntu/diploma-project
chown -R ubuntu:ubuntu /home/ubuntu/diploma-project

# Даємо права на виконання всім скриптам, які ти закинув у репо
chmod +x /home/ubuntu/diploma-project/manager-panel/*.sh || true

echo "=== БАЗОВИЙ СЕТАП ЗАВЕРШЕНО! ==="