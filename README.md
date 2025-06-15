# Macro Mancer

A financial analysis system that uses Quantified Sentiment Analysis to calculate the impact of macro indicators on financial assets.

## Project Structure

```
macro-mancer/
├── src/
│   ├── api/                    # API endpoints
│   │   ├── routes/            # API route handlers
│   │   └── models/            # Pydantic models
│   ├── agents/                # AI Agent implementations
│   │   ├── news_analyzer.py   # News analysis agent
│   │   ├── impact_calculator.py # Impact calculation
│   │   └── feedback_loop.py   # Learning feedback system
│   ├── data/
│   │   ├── scrapers/         # Web scraping
│   │   │   └── seeking_alpha.py
│   │   └── processors/       # Data processing
│   ├── ml/
│   │   ├── training/         # Model training
│   │   ├── evaluation/       # Model evaluation
│   │   └── feedback/         # Feedback processing
│   ├── storage/              # Database operations
│   │   ├── bigquery.py
│   │   └── models.py
│   └── utils/                # Utility functions
├── terraform/                # Infrastructure
│   ├── modules/
│   │   ├── cloud_run/       # API and agent services
│   │   ├── bigquery/        # Data storage
│   │   ├── cloud_scheduler/ # Scheduled jobs
│   │   └── cloud_monitoring/ # Monitoring
│   └── environments/
│       └── dev/
├── scripts/                  # Deployment scripts
├── tests/                    # Test suite
└── docs/                     # Documentation
```

## Features

- RESTful API for impact queries
- News scraping from Seeking Alpha
- AI-powered sentiment analysis
- Asset impact calculation
- Continuous learning pipeline
- Feedback loop system
- Automated scheduling
- Cloud-native architecture

## Technology Stack

- Python 3.12+
- FastAPI for API endpoints
- Google Agent Development Kit
- Google Cloud Platform
- Terraform for IaC
- UV for Python package management
- BigQuery for data storage
- Cloud Run for serverless deployment
- Cloud Scheduler for job scheduling

## API Endpoints

- `GET /api/v1/impact/{ticker}` - Get impact for a specific ticker
- `GET /api/v1/impact/{ticker}/history` - Get historical impact data
- `POST /api/v1/feedback` - Submit feedback on predictions
- `GET /api/v1/metrics` - Get model performance metrics

## Setup

1. Install dependencies:
```bash
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

2. Set up GCP credentials:
```bash
gcloud auth application-default login
```

3. Initialize Terraform:
```bash
cd terraform/environments/dev
terraform init
```

4. Deploy infrastructure:
```bash
terraform apply
```

## Development

- Use pre-commit hooks for code quality
- Run tests with pytest
- Follow PEP 8 style guide
- Document all major components

## Monitoring and Maintenance

- Cloud Monitoring for system metrics
- Cloud Logging for application logs
- Model performance tracking
- Data quality monitoring
- Cost tracking and optimization

## Feedback Loop

- User feedback collection
- Model performance tracking
- A/B testing capability
- Continuous learning implementation
- Model versioning

## Cost Management

- Budget alert set at $100
- Resource optimization
- Proper scaling policies
- Regular cost reviews
- Caching strategies

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request
