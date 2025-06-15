import os
import sys
from pathlib import Path

# Add the src directory to the Python path
src_path = str(Path(__file__).parent.parent / "src")
sys.path.insert(0, src_path)

import pytest
from google.cloud import bigquery
from unittest.mock import Mock
from ml.training.model_manager import ModelPrediction


@pytest.fixture(scope="session")
def project_id():
    """Get project ID from environment or use default."""
    return os.getenv("GOOGLE_CLOUD_PROJECT", "macro-mancer-dev")


@pytest.fixture(scope="session")
def test_dataset():
    """Get test dataset ID."""
    return "macro_mancer_test"


@pytest.fixture(scope="session")
def bigquery_client(project_id):
    """Create BigQuery client for testing."""
    return bigquery.Client(project=project_id)


@pytest.fixture(scope="session")
def impact_calculator(project_id, test_dataset):
    """Create ImpactCalculator instance for testing."""
    return ImpactCalculator(
        project_id=project_id,
        dataset_id=test_dataset,
        table_id="test_impacts",
    )


@pytest.fixture(scope="session")
def test_data_dir():
    """Get test data directory."""
    return Path(__file__).parent / "data"


@pytest.fixture(scope="session")
def eval_sets_dir():
    """Get evaluation sets directory."""
    return Path(__file__).parent / "eval_sets"


@pytest.fixture(scope="session")
def eval_results_dir():
    """Get evaluation results directory."""
    return Path(__file__).parent / "eval_results"


@pytest.fixture
def mock_model_manager():
    """Create a mock model manager for testing."""
    manager = Mock()
    manager.analyze_news.return_value = ModelPrediction(
        asset_classes=["equities", "bonds"],
        scope="global",
        confidence=0.85,
        impact_score=0.75,
        reasoning="Test reasoning",
    )
    return manager 