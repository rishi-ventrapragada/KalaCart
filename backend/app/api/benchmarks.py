"""
Performance Benchmarking API Endpoints (Phase 8).
Executes synthetic and live performance benchmarks and serves markdown/JSON benchmark reports.
"""

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from app.core.performance import performance_engine

router = APIRouter(prefix="/api/v1/benchmarks", tags=["Performance Benchmarks"])


@router.get("/report", response_class=PlainTextResponse)
async def get_benchmark_markdown_report():
    """
    Returns the comprehensive markdown performance benchmark report.
    """
    return performance_engine.generate_markdown_report()


@router.get("/data")
async def get_benchmark_json_data():
    """
    Returns benchmark results in structured JSON format.
    """
    if performance_engine.cached_benchmark_results is None:
        return performance_engine.run_full_suite()
    return performance_engine.cached_benchmark_results


@router.post("/run")
async def run_benchmark_suite():
    """
    Executes a fresh benchmark run across all modules and returns results.
    """
    results = performance_engine.run_full_suite()
    return {"status": "completed", "results": results}
