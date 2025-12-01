"""
Evaluation API endpoints for MendAI
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional

from ..evaluation.metrics_collector import MetricsCollector


router = APIRouter(prefix="/evaluate", tags=["evaluation"])

# Shared metrics collector instance (lazy initialization)
_metrics_collector = None


def get_metrics_collector() -> MetricsCollector:
    """Get or create metrics collector instance"""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


class QueryEvaluationRequest(BaseModel):
    """Request model for single query evaluation"""
    patient_id: str = Field(..., description="Patient identifier")
    question: str = Field(..., description="Clinical question")
    query_type: str = Field(default="medium", description="Query complexity: simple, medium, complex")


class ConsistencyEvaluationRequest(BaseModel):
    """Request model for consistency evaluation"""
    patient_id: str = Field(..., description="Patient identifier")
    question: str = Field(..., description="Clinical question")
    num_runs: int = Field(default=3, ge=2, le=10, description="Number of repetitions")


class BatchEvaluationRequest(BaseModel):
    """Request model for batch evaluation"""
    evaluations: List[QueryEvaluationRequest] = Field(..., description="List of queries to evaluate")


@router.post("/query")
async def evaluate_single_query(request: QueryEvaluationRequest):
    """
    Evaluate a single clinical query
    
    Returns metrics:
    - Response time
    - Token usage (input/output)
    - Estimated cost
    - Response characteristics (length, word count)
    """
    try:
        metrics_collector = get_metrics_collector()
        result = await metrics_collector.evaluate_query(
            patient_id=request.patient_id,
            question=request.question,
            query_type=request.query_type
        )
        return result.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")


@router.post("/batch")
async def evaluate_batch_queries(request: BatchEvaluationRequest):
    """
    Evaluate multiple queries and return individual + aggregate metrics
    """
    try:
        metrics_collector = get_metrics_collector()
        results = []
        for eval_req in request.evaluations:
            result = await metrics_collector.evaluate_query(
                patient_id=eval_req.patient_id,
                question=eval_req.question,
                query_type=eval_req.query_type
            )
            results.append(result.to_dict())
        
        return {
            "individual_results": results,
            "summary": metrics_collector.get_summary_stats()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch evaluation failed: {str(e)}")


@router.post("/consistency")
async def evaluate_consistency(request: ConsistencyEvaluationRequest):
    """
    Test response consistency by asking same question multiple times
    
    Returns:
    - Response time variance
    - Response length variance
    - Cost metrics
    - Consistency score
    - All individual responses for manual inspection
    """
    try:
        metrics_collector = get_metrics_collector()
        result = await metrics_collector.evaluate_consistency(
            patient_id=request.patient_id,
            question=request.question,
            num_runs=request.num_runs
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Consistency evaluation failed: {str(e)}")


@router.get("/summary")
async def get_evaluation_summary():
    """
    Get summary statistics from all evaluations run in this session
    
    Returns aggregated metrics grouped by query type
    """
    try:
        metrics_collector = get_metrics_collector()
        summary = metrics_collector.get_summary_stats()
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get summary: {str(e)}")


@router.get("/export")
async def export_results():
    """
    Export all evaluation results collected in this session
    """
    try:
        metrics_collector = get_metrics_collector()
        results = metrics_collector.export_results()
        return {
            "total_count": len(results),
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.delete("/reset")
async def reset_metrics():
    """
    Clear all collected metrics (useful for starting fresh evaluation runs)
    """
    global _metrics_collector
    _metrics_collector = MetricsCollector()
    return {"message": "Metrics collector reset successfully"}
