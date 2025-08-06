"""
Configuration file for Phoenix Analyzer
"""
from dataclasses import dataclass
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

@dataclass
class PhoenixConfig:
    """Phoenix connection and analysis configuration"""
    # Phoenix connection
    endpoint: str = "http://localhost:6006"
    project_name: str = "playground"
    fallback_project: str = "default"
    
    # Time filtering
    minutes_back: int = 15
    
    # OpenAI configuration
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"
    max_analysis_tokens: int = 1000
    analysis_temperature: float = 0.3
    
    # Display settings
    max_recent_calls_display: int = 10
    max_input_preview_length: int = 200
    max_output_preview_length: int = 200
    
    # Cost tracking
    enable_cost_tracking: bool = True
    gpt_4o_mini_cost_per_token: float = 0.000002
    
    def __post_init__(self):
        """Initialize API key from environment if not provided"""
        if self.openai_api_key is None:
            self.openai_api_key = os.getenv("OPENAI_API_KEY")

# Different preset configurations
DEVELOPMENT_CONFIG = PhoenixConfig(
    minutes_back=5,
    max_recent_calls_display=5
)

PRODUCTION_CONFIG = PhoenixConfig(
    minutes_back=60,
    max_recent_calls_display=20,
    enable_cost_tracking=True
)

EXTENDED_ANALYSIS_CONFIG = PhoenixConfig(
    minutes_back=120,
    max_analysis_tokens=2000,
    max_recent_calls_display=25
)
