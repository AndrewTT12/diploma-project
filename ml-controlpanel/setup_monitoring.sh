#!/bin/bash
set -e
echo "=== Розгортання Prometheus та Grafana ==="

helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -

NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')

# Створюємо тимчасовий values файл
cat > /tmp/monitoring-values.yaml <<EOF
grafana:
  nodeSelector:
    cloud.google.com/gke-nodepool: cpu-pool
  service:
    type: NodePort
    nodePort: 30030
  grafana.ini:
    security:
      allow_embedding: true
    auth:
      anonymous:
        enabled: true
        org_role: Admin

prometheus:
  prometheusSpec:
    nodeSelector:
      cloud.google.com/gke-nodepool: cpu-pool
  service:
    type: NodePort
    nodePort: 30090
EOF

helm install kube-prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  -f /tmp/monitoring-values.yaml

echo "========================================================"
echo "Моніторинг розгорнуто! Внутрішній IP ноди: $NODE_IP"
echo "========================================================"