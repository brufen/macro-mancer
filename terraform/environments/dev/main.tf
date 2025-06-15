terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
    null = {
      source  = "hashicorp/null"
      version = "~> 3.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

module "cloud_sql" {
  source = "../../modules/cloud_sql"

  instance_name = var.instance_name
  database_name = var.database_name
  db_user       = var.db_user
  region        = var.region
} 