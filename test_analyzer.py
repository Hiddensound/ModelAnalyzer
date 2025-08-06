"""
Simple tests for Phoenix Analyzer
"""
import pytest
import pandas as pd
from datetime import datetime, timezone
from phoenix_analyzer import SpanAnalyzer, LLMCallDetails
from config import PhoenixConfig


class TestSpanAnalyzer:
    """Test SpanAnalyzer functionality"""
    
    def test_extract_span_details(self):
        """Test span detail extraction"""
        # Mock span data
        mock_span = {
            'context.span_id': 'test_span_id',
            'context.trace_id': 'test_trace_id',
            'name': 'ChatCompletion',
            'start_time': '2025-08-06T18:41:59.829542+00:00',
            'end_time': '2025-08-06T18:42:02.607948+00:00',
            'status_code': 'OK',
            'attributes.llm.model_name': 'gpt-4o',
            'attributes.llm.token_count.prompt': 150,
            'attributes.llm.token_count.completion': 50,
            'attributes.llm.token_count.total': 200,
            'attributes.llm.temperature': 0.7,
            'input': 'Test input',
            'output': 'Test output'
        }
        
        # Create a mock span object that behaves like a pandas Series
        class MockSpan:
            def __init__(self, data):
                self.data = data
            
            def get(self, key, default='N/A'):
                return self.data.get(key, default)
        
        span = MockSpan(mock_span)
        details = SpanAnalyzer.extract_span_details(span)
        
        # Assertions
        assert details.span_id == 'test_span_id'
        assert details.model == 'gpt-4o'
        assert details.prompt_tokens == 150
        assert details.total_tokens == 200
        assert details.temperature == 0.7
        assert details.input_data == 'Test input'
    
    def test_filter_llm_spans(self):
        """Test LLM span filtering"""
        # Create mock DataFrame
        data = {
            'span_kind': ['LLM', 'HTTP', 'LLM', 'DATABASE'],
            'name': ['ChatCompletion', 'api_call', 'openai_call', 'db_query'],
            'start_time': [datetime.now(timezone.utc)] * 4
        }
        spans_df = pd.DataFrame(data)
        
        # Filter LLM spans
        llm_spans = SpanAnalyzer.filter_llm_spans(spans_df)
        
        # Should find 3 LLM spans (2 with span_kind='LLM', 1 with 'openai' in name)
        assert len(llm_spans) == 3
        assert all(llm_spans['span_kind'] == 'LLM' or 'openai' in llm_spans['name'].str.lower())


class TestPhoenixConfig:
    """Test configuration management"""
    
    def test_default_config(self):
        """Test default configuration values"""
        config = PhoenixConfig()
        
        assert config.endpoint == "http://localhost:6006"
        assert config.project_name == "playground"
        assert config.minutes_back == 15
        assert config.openai_model == "gpt-4o-mini"
    
    def test_custom_config(self):
        """Test custom configuration"""
        config = PhoenixConfig(
            endpoint="http://localhost:7006",
            minutes_back=30,
            project_name="custom_project"
        )
        
        assert config.endpoint == "http://localhost:7006"
        assert config.minutes_back == 30
        assert config.project_name == "custom_project"


class TestLLMCallDetails:
    """Test LLMCallDetails dataclass"""
    
    def test_dataclass_creation(self):
        """Test creating LLMCallDetails instance"""
        details = LLMCallDetails(
            span_id="test_id",
            trace_id="test_trace",
            name="ChatCompletion",
            start_time=datetime.now(),
            end_time=datetime.now(),
            status="OK",
            duration_ms=1500.0,
            model="gpt-4o",
            provider="OpenAI",
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            temperature=0.7,
            max_tokens=1000,
            top_p=1.0,
            cost=0.001,
            finish_reason="stop",
            input_data="test input",
            output_data="test output"
        )
        
        assert details.model == "gpt-4o"
        assert details.total_tokens == 150
        assert details.duration_ms == 1500.0


if __name__ == "__main__":
    # Run tests manually
    test_span = TestSpanAnalyzer()
    test_span.test_extract_span_details()
    test_span.test_filter_llm_spans()
    
    test_config = TestPhoenixConfig()
    test_config.test_default_config()
    test_config.test_custom_config()
    
    test_details = TestLLMCallDetails()
    test_details.test_dataclass_creation()
    
    print("✅ All tests passed!")
