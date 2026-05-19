#!/bin/bash
set -e

echo "=== 1. Updating system and installing utilities ==="
apt-get update && apt-get upgrade -y
apt-get install -y ca-certificates gnupg curl software-properties-common python3-pip python3-venv git jq

echo "=== 2. Installing Docker ==="
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
apt-get update && apt-get install -y docker-ce docker-ce-cli containerd.io

echo "=== 3. Installing Google Cloud CLI and kubectl ==="
curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg
echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list
apt-get update && apt-get install -y google-cloud-cli google-cloud-cli-gke-gcloud-auth-plugin kubectl

echo "=== 4. Installing Helm ==="
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

echo "=== 5. Setting up Python environment ==="
python3 -m venv /opt/mlops-env
/opt/mlops-env/bin/pip install fastapi uvicorn locust google-cloud-storage kubernetes httpx
chown -R ubuntu:ubuntu /opt/mlops-env

echo "=== 6. Cloning repository ==="
REPO_URL="https://github.com/AndrewTT12/diploma-project.git"

git clone $REPO_URL /home/ubuntu/diploma-project

echo "Завантаження тестового датасету COCO128..."
cd /home/ubuntu/diploma-project/ml-controlpanel

sudo apt-get install unzip -y
wget -q https://github.com/ultralytics/yolov5/releases/download/v1.0/coco128.zip
unzip -q coco128.zip

mkdir -p dataset
mv coco128/images/train2017/* dataset/
rm -rf coco128 coco128.zip

echo "Датасет успішно підготовлено!"

chown -R ubuntu:ubuntu /home/ubuntu/diploma-project
chmod +x /home/ubuntu/diploma-project/ml-controlpanel/*.sh || true
echo "=== Done ==="