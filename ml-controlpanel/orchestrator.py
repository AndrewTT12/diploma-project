import subprocess
import httpx
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

app = FastAPI(title="MLOps Unified Command Center")

class TestConfig(BaseModel):
    model_type: str
    cpu_limit: str
    memory_limit: str

# Спроба отримати внутрішній IP ноди для Prometheus
try:
    NODE_IP = subprocess.check_output(
        "kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type==\"InternalIP\")].address}'",
        shell=True, text=True
    ).strip()
except Exception:
    NODE_IP = "127.0.0.1"

PROMETHEUS_URL = f"http://{NODE_IP}:30090/api/v1/query"
LOCUST_URL = "http://127.0.0.1:8089/stats/requests"

# ================= ХАБ МОНІТОРИНГУ ТА КЕРУВАННЯ (ФРОНТЕНД) =================
@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    html_content = f"""
    <!DOCTYPE html>
    <html lang="uk">
    <head>
        <meta charset="UTF-8">
        <title>MLOps Головний Командний Центр</title>
        <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
    </head>
    <body class="bg-slate-900 text-slate-100 font-sans min-h-screen p-6">
        <div class="max-w-7xl mx-auto space-y-6">
            
            <div class="bg-slate-800 p-6 rounded-xl border border-slate-700 flex justify-between items-center shadow-xl">
                <div>
                    <h1 class="text-3xl font-black text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-emerald-400">
                        MLOps Unified Dashboard
                    </h1>
                    <p class="text-slate-400 text-sm">Централізоване керування та Live-моніторинг експерименту</p>
                </div>
                <div class="flex space-x-3">
                    <a href="http://localhost:30030" target="_blank" class="bg-orange-600 hover:bg-orange-700 text-xs font-bold py-2 px-4 rounded transition">Grafana 📊</a>
                    <a href="http://localhost:8089" target="_blank" class="bg-lime-600 hover:bg-lime-700 text-xs font-bold py-2 px-4 rounded transition">Locust 🐜</a>
                </div>
            </div>

            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                
                <div class="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg h-fit">
                    <h2 class="text-xl font-bold mb-4 text-blue-400 border-b border-slate-700 pb-2">⚙️ Керування К8s</h2>
                    <form id="configForm" class="space-y-4">
                        <div>
                            <label class="block text-xs font-bold text-slate-400 uppercase mb-1">Модель</label>
                            <select name="model_type" class="w-full bg-slate-900 border border-slate-700 rounded p-2 text-sm text-slate-200">
                                <option value="yolo">YOLOv8-Medium (Detection)</option>
                                <option value="mobilenet">MobileNetV3-Small (Classification)</option>
                            </select>
                        </div>
                        <div>
                            <label class="block text-xs font-bold text-slate-400 uppercase mb-1">CPU Limit</label>
                            <select name="cpu_limit" class="w-full bg-slate-900 border border-slate-700 rounded p-2 text-sm text-slate-200">
                                <option value="0.5">0.5 vCPU (Throttling Test)</option>
                                <option value="1">1.0 vCPU (Standard)</option>
                                <option value="2">2.0 vCPU (Max Power)</option>
                            </select>
                        </div>
                        <div>
                            <label class="block text-xs font-bold text-slate-400 uppercase mb-1">RAM Limit</label>
                            <select name="memory_limit" class="w-full bg-slate-900 border border-slate-700 rounded p-2 text-sm text-slate-200">
                                <option value="1Gi">1 GiB (OOM Risk)</option>
                                <option value="2Gi">2 GiB (Optimal)</option>
                                <option value="4Gi">4 GiB (Safe)</option>
                            </select>
                        </div>
                        <button type="submit" class="w-full bg-blue-500 hover:bg-blue-600 text-white font-bold py-2.5 px-4 rounded transition text-sm">
                            Передеплоїти Кластер
                        </button>
                    </form>
                    <div id="resultBox" class="mt-4 p-3 bg-slate-900 rounded border border-slate-700 text-xs font-mono hidden"></div>
                </div>

                <div class="lg:col-span-2 bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg flex flex-col justify-between">
                    <div>
                        <h2 class="text-xl font-bold mb-4 text-emerald-400 border-b border-slate-700 pb-2">📈 Показники в Реальному Часі</h2>
                        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                            <div class="bg-slate-900 p-4 rounded-lg border border-slate-700 text-center">
                                <p class="text-xs text-slate-400 font-medium uppercase">Locust RPS</p>
                                <p id="metricRps" class="text-2xl font-black text-blue-400 mt-1">0.0</p>
                            </div>
                            <div class="bg-slate-900 p-4 rounded-lg border border-slate-700 text-center">
                                <p class="text-xs text-slate-400 font-medium uppercase">Failures</p>
                                <p id="metricFails" class="text-2xl font-black text-rose-500 mt-1">0%</p>
                            </div>
                            <div class="bg-slate-900 p-4 rounded-lg border border-slate-700 text-center">
                                <p class="text-xs text-slate-400 font-medium uppercase">Latency (Avg)</p>
                                <p id="metricLatency" class="text-2xl font-black text-amber-400 mt-1">0 ms</p>
                            </div>
                            <div class="bg-slate-900 p-4 rounded-lg border border-slate-700 text-center">
                                <p class="text-xs text-slate-400 font-medium uppercase">CPU Throttling</p>
                                <p id="metricThrottling" class="text-2xl font-black text-purple-400 mt-1">0%</p>
                            </div>
                        </div>
                    </div>

                    <div class="bg-slate-900 p-4 rounded-lg border border-slate-700 space-y-2">
                        <h3 class="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Стан Контейнера з Prometheus API</h3>
                        <div class="flex justify-between text-sm">
                            <span class="text-slate-400">Поточна утилізація CPU:</span>
                            <span id="k8sCpuUsage" class="font-mono text-slate-200 font-bold">Завантаження...</span>
                        </div>
                        <div class="w-full bg-slate-800 rounded-full h-2">
                            <div id="cpuBar" class="bg-blue-500 h-2 rounded-full transition-all" style="width: 0%"></div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg">
                <div class="flex justify-between items-center mb-4 border-b border-slate-700 pb-2">
                    <h2 class="text-xl font-bold text-purple-400">📝 Live Pod Terminal</h2>
                    <span class="flex h-3 w-3">
                        <span class="animate-ping absolute inline-flex h-3 w-3 rounded-full bg-purple-400 opacity-75"></span>
                        <span class="relative inline-flex rounded-full h-3 w-3 bg-purple-500"></span>
                    </span>
                </div>
                <div class="bg-black p-4 rounded-lg border border-slate-700 h-64 overflow-y-auto">
                    <pre id="podLogs" class="text-green-400 font-mono text-xs whitespace-pre-wrap">Очікування логів...</pre>
                </div>
            </div>

        </div>

        <script>
            // Логіка відправки форми конфігурації
            document.getElementById('configForm').addEventListener('submit', async (e) => {{
                e.preventDefault();
                const resultBox = document.getElementById('resultBox');
                resultBox.classList.remove('hidden');
                resultBox.innerText = "⏳ Оновлення конфігурації GKE...";
                
                const response = await fetch('/configure', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify(Object.fromEntries(new FormData(e.target)))
                }});
                const res = await response.json();
                resultBox.innerText = res.status === 'success' ? `✅ ${{res.details}}` : `❌ ${{res.message}}`;
                // Очищаємо логи при редеплої
                document.getElementById('podLogs').innerText = "Контейнер перезапускається. Очікування нових логів...";
            }});

            // Опитування метрик (кожні 2 секунди)
            async function updateMetrics() {{
                try {{
                    const response = await fetch('/api/metrics');
                    const data = await response.json();
                    
                    document.getElementById('metricRps').innerText = data.locust_rps;
                    document.getElementById('metricFails').innerText = data.locust_fail_ratio + '%';
                    document.getElementById('metricLatency').innerText = data.locust_avg_latency + ' ms';
                    document.getElementById('metricThrottling').innerText = data.k8s_cpu_throttling + '%';
                    document.getElementById('k8sCpuUsage').innerText = data.k8s_cpu_usage + ' Cores';
                    
                    const percent = Math.min((parseFloat(data.k8s_cpu_usage) / 2) * 100, 100);
                    document.getElementById('cpuBar').style.width = percent + '%';
                }} catch (e) {{}}
            }}

            // Опитування логів (кожні 3 секунди)
            async function updateLogs() {{
                try {{
                    const response = await fetch('/api/logs');
                    const data = await response.json();
                    const logContainer = document.getElementById('podLogs');
                    
                    // Перевіряємо, чи юзер зараз не скролить вгору, щоб не перебивати йому скрол
                    const isAtBottom = logContainer.parentElement.scrollHeight - logContainer.parentElement.scrollTop <= logContainer.parentElement.clientHeight + 20;
                    
                    logContainer.innerText = data.logs;
                    
                    if (isAtBottom) {{
                        logContainer.parentElement.scrollTop = logContainer.parentElement.scrollHeight;
                    }}
                }} catch (e) {{}}
            }}

            setInterval(updateMetrics, 2000);
            setInterval(updateLogs, 3000);
        </script>
    </body>
    </html>
    """
    return html_content

# ================= АПІ БЕКЕНД =================

@app.get("/api/metrics")
async def get_live_metrics():
    metrics = {
        "locust_rps": 0.0, "locust_fail_ratio": 0, "locust_avg_latency": 0,
        "k8s_cpu_usage": "0.0", "k8s_cpu_throttling": 0
    }
    async with httpx.AsyncClient() as client:
        try:
            res = await client.get(LOCUST_URL, timeout=1.0)
            if res.status_code == 200:
                data = res.json()
                metrics["locust_rps"] = round(data.get("current_rps", 0.0), 1)
                metrics["locust_fail_ratio"] = int(data.get("fail_ratio", 0) * 100)
                for stat in data.get("stats", []):
                    if stat.get("name") == "Total":
                        metrics["locust_avg_latency"] = int(stat.get("avg_response_time", 0))
        except Exception: pass

        try:
            q_cpu = 'sum(rate(container_cpu_usage_seconds_total{container="ml-container"}[1m]))'
            res_cpu = await client.get(PROMETHEUS_URL, params={"query": q_cpu}, timeout=1.0)
            metrics["k8s_cpu_usage"] = round(float(res_cpu.json()['data']['result'][0]['value'][1]), 3)
        except Exception: metrics["k8s_cpu_usage"] = "0.0"

        try:
            q_th = 'sum(increase(container_cpu_cfs_throttled_periods_total{container="ml-container"}[1m])) / sum(increase(container_cpu_cfs_periods_total{container="ml-container"}[1m])) * 100'
            res_th = await client.get(PROMETHEUS_URL, params={"query": q_th}, timeout=1.0)
            val = float(res_th.json()['data']['result'][0]['value'][1])
            metrics["k8s_cpu_throttling"] = int(val) if not __import__('math').isnan(val) else 0
        except Exception: pass

    return metrics

@app.get("/api/logs")
async def get_pod_logs():
    """Стягує останні 50 рядків логів з актуального пода FastAPI"""
    try:
        # Використовуємо label selector (-l app=ml-api), щоб не залежати від точного імені пода
        logs = subprocess.check_output(
            ["kubectl", "logs", "-l", "app=ml-api", "--tail=50"],
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
    yaml_content = f"""
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ml-model-deployment
  labels:
    app: ml-api
spec:
  replicas: 1
  selector:
    matchLabels:
      app: ml-api
  template:
    metadata:
      labels:
        app: ml-api
    spec:
      tolerations:
      - key: "workload"
        operator: "Equal"
        value: "heavy"
        effect: "NoSchedule"
      containers:
      - name: ml-container
        image: mo0nlighttt/ml-docker-api:v1
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