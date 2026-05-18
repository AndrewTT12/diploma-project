provider "google" {
  credentials = file(var.gcp_creds)
  project = var.project_id
  region  = var.region
  zone    = var.zone
}