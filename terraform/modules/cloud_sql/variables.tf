variable "instance_name" {
  description = "Name of the Cloud SQL instance"
  type        = string
}

variable "database_name" {
  description = "Name of the database to create"
  type        = string
}

variable "db_user" {
  description = "Database user name"
  type        = string
}

variable "region" {
  description = "The region where the instance will be created"
  type        = string
  default     = "europe-west3"  # Berlin region
} 