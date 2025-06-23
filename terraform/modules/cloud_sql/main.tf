resource "random_password" "db_password" {
  length           = 32
  special          = true
  override_special = "!@#$%^&*()_+"
  min_special      = 1
  min_upper        = 1
  min_lower        = 1
  min_numeric      = 1
}

resource "google_secret_manager_secret" "db_password" {
  secret_id = "${var.instance_name}-db-password"
  
  replication {
    user_managed {
      replicas {
        location = "europe-west3"  # Berlin region
      }
    }
  }

  labels = {
    instance = var.instance_name
  }
}

resource "google_secret_manager_secret_version" "db_password" {
  secret      = google_secret_manager_secret.db_password.id
  secret_data = random_password.db_password.result
}

resource "google_sql_database_instance" "postgres" {
  name             = var.instance_name
  database_version = "POSTGRES_14"
  region           = var.region

  settings {
    tier = "db-f1-micro"
    
    backup_configuration {
      enabled = false
    }

    ip_configuration {
      ipv4_enabled = true
      require_ssl  = true
      
      authorized_networks {
        name  = "all"
        value = "0.0.0.0/0"
      }
    }
  }

  deletion_protection = false
}

resource "google_sql_database" "database" {
  name     = var.database_name
  instance = google_sql_database_instance.postgres.name
}

resource "google_sql_user" "user" {
  name     = var.db_user
  instance = google_sql_database_instance.postgres.name
  password = random_password.db_password.result
}

# Note: Tables will be created by SQLAlchemy's create_tables() function
# This approach lets the application handle schema management 

# Outputs for database connection
output "instance_connection_name" {
  description = "The connection name of the instance"
  value       = google_sql_database_instance.postgres.connection_name
}

output "instance_ip_address" {
  description = "The public IP address of the instance"
  value       = google_sql_database_instance.postgres.public_ip_address
}

output "database_name" {
  description = "The name of the database"
  value       = google_sql_database.database.name
}

output "db_user" {
  description = "The database user name"
  value       = google_sql_user.user.name
}

output "db_password_secret_id" {
  description = "The secret manager ID for the database password"
  value       = google_secret_manager_secret.db_password.secret_id
} 