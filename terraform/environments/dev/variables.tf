variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "instance_name" {
  description = "Name of the Cloud SQL instance"
  type        = string
  default     = "macro-mancer-db"
}

variable "database_name" {
  description = "Name of the database to create"
  type        = string
  default     = "macro_mancer"
}

variable "db_user" {
  description = "Database user name"
  type        = string
  default     = "macro_mancer_user"
}

variable "region" {
  description = "The region where the instance will be created"
  type        = string
  default     = "europe-west3"  # Berlin region
} 