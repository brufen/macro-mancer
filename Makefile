# Terraform commands
.PHONY: terraform-init terraform-plan terraform-apply terraform-destroy gcp-login check-deps

check-deps:
	@echo "Checking dependencies..."
	@if ! command -v psql >/dev/null 2>&1; then \
		echo "PostgreSQL client tools not found. Installing..."; \
		if [ "$(shell uname)" = "Darwin" ]; then \
			brew install postgresql@14; \
		elif [ -f /etc/debian_version ]; then \
			sudo apt-get update && sudo apt-get install -y postgresql-client; \
		elif [ -f /etc/redhat-release ]; then \
			sudo yum install -y postgresql; \
		else \
			echo "Unsupported OS. Please install PostgreSQL client tools manually."; \
			exit 1; \
		fi \
	fi
	@if ! command -v cloud-sql-proxy >/dev/null 2>&1; then \
		echo "Cloud SQL Auth proxy not found. Installing..."; \
		if [ "$(shell uname)" = "Darwin" ]; then \
			curl -o /usr/local/bin/cloud-sql-proxy https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.8.1/cloud-sql-proxy.darwin.amd64; \
			chmod +x /usr/local/bin/cloud-sql-proxy; \
		elif [ -f /etc/debian_version ]; then \
			curl -o /usr/local/bin/cloud-sql-proxy https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.8.1/cloud-sql-proxy.linux.amd64; \
			chmod +x /usr/local/bin/cloud-sql-proxy; \
		else \
			echo "Unsupported OS. Please install Cloud SQL Auth proxy manually."; \
			exit 1; \
		fi \
	fi

gcp-login: check-deps
	@echo "Setting up Google Cloud authentication..."
	@echo "Please follow these steps:"
	@echo "1. Run: gcloud auth login"
	@echo "2. Run: gcloud config set project YOUR_PROJECT_ID"
	@echo "3. Run: gcloud auth application-default login"
	@echo "\nAfter authentication is complete, press Enter to continue..."
	@read
	@echo "\nSetting up GCP services..."
	gcloud services enable sqladmin.googleapis.com \
		compute.googleapis.com \
		iam.googleapis.com \
		secretmanager.googleapis.com

terraform-init: check-deps
	cd terraform/environments/dev && terraform init

terraform-plan: check-deps
	cd terraform/environments/dev && terraform plan

terraform-apply: check-deps
	cd terraform/environments/dev && terraform apply

terraform-destroy: check-deps
	cd terraform/environments/dev && terraform destroy

# Development commands
.PHONY: install-dev run-web test

install-dev:
	uv venv
	uv pip install -e ".[dev]"
	uv pip install -r requirements-dev.txt

run-web:
	uvicorn src.web.main:app --reload --port 8000

test:
	pytest tests/ -v --cov=src

# ADK commands
.PHONY: run-adk-web deploy-agents

run-adk-web:
	adk web --project-id $(ADK_PROJECT_ID) --location $(ADK_LOCATION)

deploy-agents:
	adk deploy --project-id $(ADK_PROJECT_ID) --location $(ADK_LOCATION) src/agents/

# Prerequisites
# 1. Install Google Cloud SDK: https://cloud.google.com/sdk/docs/install
# 2. Run these commands in order:
#    - gcloud auth login
#    - gcloud config set project YOUR_PROJECT_ID
#    - gcloud auth application-default login
# 3. Set your project ID in terraform.tfvars

# gcloud auth login
# gcloud config set project YOUR_PROJECT_ID

# gcloud services enable sqladmin.googleapis.com \
#   compute.googleapis.com \
#   iam.googleapis.com

# gcloud services enable secretmanager.googleapis.com
# cloud-sql-proxy YOUR_INSTANCE_CONNECTION_NAME
# psql -h localhost -p 5432 -U macro_mancer_user -d macro_mancer