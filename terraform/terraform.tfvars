region  = "europe-west3"
project_id = "project-f25527aa-52e9-41df-b53"
zone    = "europe-west3-a"

# Мережа
vpc_name    = "ml-diploma-vpc"
subnet_name = "ml-diploma-subnet"
subnet_cidr = "10.10.10.0/24"
firewall_name = "ml-diploma-firewall"

# Manager-VM (Бастіон / Веб-сервер)
vm_name      = "ml-manager-vm"
machine_type = "e2-medium"
disk_size    = 20
image        = "ubuntu-os-cloud/ubuntu-2404-lts-amd64"

# GKE Cluster
cluster_name          = "ml-gke-cluster"
machine_type_cpu_pool = "e2-standard-2" # Для легких моделей та Grafana/Prometheus
machine_type_heavy_pool = "e2-standard-4" 

# bucket_name = "terraform-state-diploma-andrii"

gcp_creds = "auth.json"