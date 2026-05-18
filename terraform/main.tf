# ================= VPC & SUBNET ================= #
resource "google_compute_network" "vpc" {
  name                    = var.vpc_name
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "subnet" {
  name          = var.subnet_name
  ip_cidr_range = var.subnet_cidr
  region        = var.region
  network       = google_compute_network.vpc.id
}

# ================= FIREWALL ================= #
resource "google_compute_firewall" "firewall" {
  name    = var.firewall_name
  network = google_compute_network.vpc.name

  allow {
    protocol = "tcp"
    ports    = ["22", "80", "443", "8080", "8000", "8001", "8002", "8003"]
  }
  source_ranges = ["0.0.0.0/0"]
}

# ================= MANAGER-VM ================= #
resource "google_compute_instance" "manager_vm" {
  name         = var.vm_name
  machine_type = var.machine_type
  zone         = var.zone

  boot_disk {
    initialize_params {
      image = var.image
      size  = var.disk_size
      type  = "pd-balanced"
    }
  }

  network_interface {
    subnetwork = google_compute_subnetwork.subnet.id
    access_config {} # Ефемерна публічна IP-адреса
  }

  metadata = {
    ssh-keys = "ubuntu:${var.ssh_public_key}"
  }
  metadata_startup_script = file("init.sh")
}

# # ================= STORAGE BUCKET ================= #
# resource "google_storage_bucket" "ml_bucket" {
#   name          = var.bucket_name
#   location      = var.region
#   force_destroy = true
#   uniform_bucket_level_access = true
# }

# ================= GKE CLUSTER ================= #
resource "google_container_cluster" "primary" {
  name     = var.cluster_name
  location = var.zone

  network    = google_compute_network.vpc.name
  subnetwork = google_compute_subnetwork.subnet.name

  # Відключаємо дефолтний пул нод, щоб створити свої специфічні
  remove_default_node_pool = true
  initial_node_count       = 1
  deletion_protection = false
}

# Node Pool 1: CPU (Для моніторингу та легкої моделі)
resource "google_container_node_pool" "cpu_pool" {
  name       = "cpu-pool"
  location   = var.zone
  cluster    = google_container_cluster.primary.name
  node_count = 1

  node_config {
    machine_type = var.machine_type_cpu_pool
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]
  }
}

# Node Pool 2: Heavy CPU 
resource "google_container_node_pool" "heavy_pool" {
  name       = "heavy-pool"
  location   = var.zone
  cluster    = google_container_cluster.primary.name
  node_count = 1

  node_config {
    machine_type = var.machine_type_heavy_pool
    
    # Залишаємо taint для ізоляції важких навантажень
    taint {
      key    = "workload"
      value  = "heavy"
      effect = "NO_SCHEDULE"
    }

    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]
  }
}