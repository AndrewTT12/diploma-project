import subprocess
import httpx
import math
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

app = FastAPI(title="Andrii Savitskyi Control Panel", version="1.0")

class TestConfig(BaseModel):
    model_type: str
    cpu_limit: str
    memory_limit: str

# Автоматично дізнаємось внутрішній IP першої ноди для Prometheus API
try:
    NODE_IP = subprocess.check_output(
        "kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type==\"InternalIP\")].address}'",
        shell=True, text=True
    ).strip()
except Exception:
    NODE_IP = "127.0.0.1"

PROMETHEUS_URL = f"http://{NODE_IP}:30090/api/v1/query"
LOCUST_URL = "http://localhost:8089/stats/requests"

# ================= FrontEnd =================
@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    """Віддає ізольований HTML-файл інтерфейсу панелі керування"""
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

# ================= BackEnd =================

@app.get("/api/metrics")
async def get_live_metrics():
    """Стягує Live-метрики з Locust API та Prometheus API для дашборда"""
    metrics = {
        "locust_rps": 0.0, "locust_fail_ratio": 0, "locust_avg_latency": 0,
        "k8s_cpu_usage": "0.0", "k8s_cpu_throttling": 0
    }
    
    async with httpx.AsyncClient() as client:
        # Стягуємо дані з Locust API
        try:
            res = await client.get(LOCUST_URL, timeout=1.0)
            if res.status_code == 200:
                data = res.json()
                metrics["locust_rps"] = round(data.get("total_rps", 0.0), 1)
                metrics["locust_fail_ratio"] = int(data.get("fail_ratio", 0) * 100)
                
                for stat in data.get("stats", []):
                    if stat.get("name") == "Aggregated":
                        metrics["locust_avg_latency"] = int(stat.get("avg_response_time", 0))
        except Exception: 
            pass

        # Стягуємо поточну утилізацію CPU контейнера з Prometheus
        try:
            q_cpu = 'sum(rate(container_cpu_usage_seconds_total{container="ml-container"}[1m]))'
            res_cpu = await client.get(PROMETHEUS_URL, params={"query": q_cpu}, timeout=1.0)
            metrics["k8s_cpu_usage"] = round(float(res_cpu.json()['data']['result'][0]['value'][1]), 3)
        except Exception: 
            metrics["k8s_cpu_usage"] = "0.0"

        # Стягуємо відсоток CPU Throttling контейнера з Prometheus
        try:
            q_th = 'sum(increase(container_cpu_cfs_throttled_periods_total{container="ml-container"}[1m])) / sum(increase(container_cpu_cfs_periods_total{container="ml-container"}[1m])) * 100'
            res_th = await client.get(PROMETHEUS_URL, params={"query": q_th}, timeout=1.0)
            val = float(res_th.json()['data']['result'][0]['value'][1])
            metrics["k8s_cpu_throttling"] = int(val) if not math.isnan(val) else 0
        except Exception: 
            pass

    return metrics

@app.get("/api/logs")
async def get_pod_logs():
    """Стягує останні 100 рядків логів з актуального пода моделі у GKE"""
    try:
        logs = subprocess.check_output(
            ["kubectl", "logs", "-l", "app=ml-api", "--tail=100"],
            stderr=subprocess.STDOUT, text=True
        )
        if not logs.strip():
            return {"status": "success", "logs": "Под живий, але логів поки немає..."}
        return {"status": "success", "logs": logs}
    except subprocess.CalledProcessError as e:
        return {"status": "warning", "logs": f"Очікування старту контейнера...\n{e.output}"}
    except Exception as e:
        return {"status": "error", "logs": f"Помилка отримання логів: {str(e)}"}

@app.post("/configure")
async def configure_infrastructure(config: TestConfig):
    """Динамічно генерує маніфест та передеплоює под моделі з новими лімітами"""
    yaml_content = f"""
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ml-model-deployment
  labels:
    app: ml-api
spec:
  replicas: 1
  strategy:
    type: Recreate
  selector:
    matchLabels:
      app: ml-api
  template:
    metadata:
      labels:
        app: ml-api
    spec:
      terminationGracePeriodSeconds: 2
      tolerations:
      - key: "workload"
        operator: "Equal"
        value: "heavy"
        effect: "NoSchedule"
      containers:
      - name: ml-container
        image: mo0nl1ghttt/ml-docker-api:v1
        imagePullPolicy: Always
        ports:
        - containerPort: 8000
        env:
        - name: MODEL_TYPE
          value: "{config.model_type}"
        resources:
          requests:
            cpu: "500m"
            memory: "1Gi"
          limits:
            cpu: "{config.cpu_limit}"
            memory: "{config.memory_limit}"
---
apiVersion: v1
kind: Service
metadata:
  name: ml-service
spec:
  selector:
    app: ml-api
  ports:
    - protocol: TCP
      port: 8000
      targetPort: 8000
      nodePort: 30080
  type: NodePort
"""
    try:
        process = subprocess.Popen(["kubectl", "apply", "-f", "-"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate(input=yaml_content)
        if process.returncode != 0: 
            return {"status": "error", "message": stderr}
        return {"status": "success", "details": f"{config.model_type.upper()} | CPU: {config.cpu_limit} | RAM: {config.memory_limit}"}
    except Exception as e: 
        return {"status": "error", "message": str(e)}