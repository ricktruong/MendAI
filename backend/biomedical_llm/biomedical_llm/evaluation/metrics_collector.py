"""
Metrics Collector for MendAI Evaluation
Collects: response time, token usage, cost, and consistency metrics
"""

import time
from typing import Dict, List
from datetime import datetime
from dataclasses import dataclass, asdict

from ..types.chat import ChatRequest, ChatMessage
from ..services.openai_service import get_openai_service
from ..services.patient_data_client import get_patient_data_client


@dataclass
class EvaluationResult:
    """Single evaluation result"""
    query_type: str  # simple, medium, complex
    question: str
    patient_id: str
    response_time: float  # seconds
    response_length_chars: int
    response_length_words: int
    estimated_input_tokens: int
    estimated_output_tokens: int
    estimated_cost: float
    from_cache: bool
    timestamp: str
    response_text: str  # For consistency checking
    
    def to_dict(self) -> Dict:
        return asdict(self)


class MetricsCollector:
    """Collect evaluation metrics for LLM responses"""
    
    # GPT-4o-mini pricing (as of 2024)
    INPUT_COST_PER_1M = 0.150  # $0.150 per 1M input tokens
    OUTPUT_COST_PER_1M = 0.600  # $0.600 per 1M output tokens
    
    def __init__(self):
        self.results: List[EvaluationResult] = []
        self.openai_service = get_openai_service()
        self.patient_client = get_patient_data_client()
    
    @staticmethod
    def estimate_tokens(text: str) -> int:
        """Rough token estimation: ~4 characters per token"""
        return len(text) // 4
    
    @staticmethod
    def calculate_cost(input_tokens: int, output_tokens: int) -> float:
        """Calculate OpenAI API cost"""
        input_cost = (input_tokens / 1_000_000) * MetricsCollector.INPUT_COST_PER_1M
        output_cost = (output_tokens / 1_000_000) * MetricsCollector.OUTPUT_COST_PER_1M
        return input_cost + output_cost
    
    async def evaluate_query(
        self,
        patient_id: str,
        question: str,
        query_type: str = "medium"
    ) -> EvaluationResult:
        """
        Evaluate a single query
        
        Args:
            patient_id: Patient identifier
            question: Clinical question to ask
            query_type: "simple", "medium", or "complex"
        
        Returns:
            EvaluationResult with metrics
        """
        # Fetch patient context
        patient_data = await self.patient_client.get_patient_data(patient_id)
        
        # Create user message
        user_message = ChatMessage(
            role="user",
            content=question
        )
        
        # Build request
        messages = [user_message.dict()]
        
        # Estimate input tokens (including patient context if available)
        full_prompt = question
        if patient_data:
            # Rough estimation of patient context size
            import json
            full_prompt += json.dumps(patient_data)
        estimated_input_tokens = self.estimate_tokens(full_prompt)
        
        # Measure response time
        start_time = time.time()
        response = self.openai_service.chat_completion(
            messages=messages,
            patient_context=patient_data,  # Pass patient context, not just ID
            patient_id=patient_id
        )
        response_time = time.time() - start_time
        
        # Calculate metrics
        response_length_chars = len(response)
        response_length_words = len(response.split())
        estimated_output_tokens = self.estimate_tokens(response)
        estimated_cost = self.calculate_cost(estimated_input_tokens, estimated_output_tokens)
        
        # Create result
        eval_result = EvaluationResult(
            query_type=query_type,
            question=question,
            patient_id=patient_id,
            response_time=response_time,
            response_length_chars=response_length_chars,
            response_length_words=response_length_words,
            estimated_input_tokens=estimated_input_tokens,
            estimated_output_tokens=estimated_output_tokens,
            estimated_cost=estimated_cost,
            from_cache=False,  # Would check cache if implemented
            timestamp=datetime.now().isoformat(),
            response_text=response
        )
        
        self.results.append(eval_result)
        return eval_result
    
    async def evaluate_consistency(
        self,
        patient_id: str,
        question: str,
        num_runs: int = 3
    ) -> Dict:
        """
        Test consistency by asking same question multiple times
        
        Args:
            patient_id: Patient identifier
            question: Clinical question
            num_runs: Number of times to repeat
        
        Returns:
            Dictionary with consistency metrics
        """
        responses = []
        response_times = []
        costs = []
        
        for i in range(num_runs):
            result = await self.evaluate_query(patient_id, question, "consistency_test")
            responses.append(result.response_text)
            response_times.append(result.response_time)
            costs.append(result.estimated_cost)
            
            # Wait a bit between requests to avoid rate limiting
            if i < num_runs - 1:
                time.sleep(0.5)
        
        # Calculate similarity (simple: compare lengths and word overlap)
        lengths = [len(r) for r in responses]
        length_variance = max(lengths) - min(lengths)
        avg_length = sum(lengths) / len(lengths)
        
        return {
            "question": question,
            "num_runs": num_runs,
            "responses": responses,
            "response_times": {
                "min": min(response_times),
                "max": max(response_times),
                "avg": sum(response_times) / len(response_times)
            },
            "response_lengths": {
                "min": min(lengths),
                "max": max(lengths),
                "avg": avg_length,
                "variance": length_variance
            },
            "costs": {
                "min": min(costs),
                "max": max(costs),
                "avg": sum(costs) / len(costs),
                "total": sum(costs)
            },
            "consistency_score": 1 - (length_variance / avg_length) if avg_length > 0 else 0
        }
    
    def get_summary_stats(self) -> Dict:
        """Get summary statistics from all collected results"""
        if not self.results:
            return {"error": "No results collected yet"}
        
        # Group by query type
        by_type = {}
        for result in self.results:
            if result.query_type not in by_type:
                by_type[result.query_type] = []
            by_type[result.query_type].append(result)
        
        summary = {
            "total_queries": len(self.results),
            "by_query_type": {}
        }
        
        for query_type, results in by_type.items():
            response_times = [r.response_time for r in results]
            costs = [r.estimated_cost for r in results]
            input_tokens = [r.estimated_input_tokens for r in results]
            output_tokens = [r.estimated_output_tokens for r in results]
            cached = sum(1 for r in results if r.from_cache)
            
            summary["by_query_type"][query_type] = {
                "count": len(results),
                "response_time": {
                    "min": min(response_times),
                    "max": max(response_times),
                    "avg": sum(response_times) / len(response_times)
                },
                "cost": {
                    "min": min(costs),
                    "max": max(costs),
                    "avg": sum(costs) / len(costs),
                    "total": sum(costs)
                },
                "tokens": {
                    "avg_input": sum(input_tokens) / len(input_tokens),
                    "avg_output": sum(output_tokens) / len(output_tokens),
                    "total_input": sum(input_tokens),
                    "total_output": sum(output_tokens)
                },
                "cache_hit_rate": cached / len(results) * 100
            }
        
        return summary
    
    def export_results(self) -> List[Dict]:
        """Export all results as list of dicts"""
        return [r.to_dict() for r in self.results]
