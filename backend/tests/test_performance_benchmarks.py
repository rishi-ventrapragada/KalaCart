import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_benchmark_data_endpoint():
    response = client.get("/api/v1/benchmarks/data")
    assert response.status_code == 200
    data = response.json()
    assert "json_serialization" in data
    assert "in_memory_filtering" in data
    assert "targets_status" in data
    assert data["targets_status"]["status"] == "PASSED_ALL_TARGETS"


def test_benchmark_report_markdown_endpoint():
    response = client.get("/api/v1/benchmarks/report")
    assert response.status_code == 200
    report_text = response.text
    assert "# KalaCart Platform Performance Benchmark Report" in report_text
    assert "Cold Start" in report_text
    assert "60 FPS" in report_text
    assert "PASSED" in report_text


def test_run_benchmark_post():
    response = client.post("/api/v1/benchmarks/run")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert "results" in data
