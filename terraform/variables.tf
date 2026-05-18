variable "project_id" { type = string }
variable "region" { default = "europe-west3" }
variable "zone" { default = "europe-west3-a" }

variable "vpc_name" { type = string }
variable "subnet_name" { type = string }
variable "subnet_cidr" { type = string }
variable "firewall_name" { type = string }

variable "vm_name" { type = string }
variable "machine_type" { type = string }
variable "disk_size" { type = number }
variable "image" { type = string }

# variable "bucket_name" { type = string }
variable "ssh_public_key" { type = string }

# Додані змінні для GKE
variable "cluster_name" { type = string }
variable "machine_type_cpu_pool" { type = string }
variable "machine_type_heavy_pool" { type = string }

variable "gcp_creds" {type = string}