#!/bin/bash
set -e
echo "=== Розгортання Prometheus та Grafana ==="
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -

# Дізнаємось внутрішній IP для NodePort
NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')

helm install kube-prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --set grafana.nodeSelector.cloud\.google\.com/gke-nodepool=cpu-pool \
  --set prometheus.prometheusSpec.nodeSelector.cloud\.google\.com/gke-nodepool=cpu-pool \
  --set grafana.service.type=NodePort \
  --set grafana.service.nodePort=30030 \
  --set prometheus.service.type=NodePort \
  --set prometheus.service.nodePort=30090 \
  --set grafana."grafana\.ini".security.allow_embedding=true \
  --set grafana."grafana\.ini".auth.anonymous.enabled=true \
  --set grafana."grafana\.ini".auth.anonymous.org_role=Admin

echo "========================================================"
echo "Моніторинг розгорнуто! Внутрішній IP ноди: $NODE_IP"
echo "========================================================"