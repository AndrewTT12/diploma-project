terraform {
  backend "gcs" {
    bucket  = "terraform-state-diploma"
    prefix  = "terraform/state"
  }
}