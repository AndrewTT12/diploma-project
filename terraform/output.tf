output "manager_vm_ip" {
  description = "Public IP of Manager VM"
  value       = google_compute_instance.manager_vm.network_interface[0].access_config[0].nat_ip
}

output "vpc_id" {
  description = "VPC ID"
  value       = google_compute_network.vpc.id
}

output "gke_cluster_name" {
  description = "GKE Cluster Name"
  value       = google_container_cluster.primary.name
}

output "gke_cluster_endpoint" {
  description = "GKE Cluster Endpoint IP"
  value       = google_container_cluster.primary.endpoint
}