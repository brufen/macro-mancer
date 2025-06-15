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

resource "null_resource" "create_tables" {
  depends_on = [google_sql_database.database]

  provisioner "local-exec" {
    command = <<-EOT
      # Start Cloud SQL Auth proxy in the background
      cloud-sql-proxy ${google_sql_database_instance.postgres.connection_name} &
      PROXY_PID=$!
      
      # Wait for the proxy to start
      sleep 5
      
      # Create the table
      export PGPASSWORD='${replace(random_password.db_password.result, "'", "'\\''")}'
      psql -h localhost -p 5432 \
      -U ${var.db_user} \
      -d ${var.database_name} \
      -c "
      CREATE TABLE IF NOT EXISTS impact (
        entity VARCHAR(50) NOT NULL,
        type VARCHAR(50) NOT NULL,
        impact VARCHAR(20) CHECK (impact IN ('strong positive', 'positive', 'strong negative', 'negative')),
        impact_description TEXT,
        inserted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      );"
      
      # Kill the proxy
      kill $PROXY_PID
    EOT
  }
} 