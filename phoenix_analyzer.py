"""
Phoenix LLM Analyzer - Modular class-based implementation
"""
import phoenix as px
import pandas as pd
import json
import openai
import os
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from dotenv import load_dotenv
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass


@dataclass
class LLMCallDetails:
    """Data class for LLM call information"""
    span_id: str
    trace_id: str
    name: str
    start_time: Any
    end_time: Any
    status: str
    duration_ms: float
    model: str
    provider: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    temperature: float
    max_tokens: int
    top_p: float
    cost: float
    finish_reason: str
    input_data: Any
    output_data: Any


class PhoenixConfig:
    """Configuration management"""
    def __init__(self, 
                 endpoint: str = "http://localhost:6006",
                 minutes_back: int = 15,
                 project_name: str = "playground",
                 fallback_project: str = "default"):
        self.endpoint = endpoint
        self.minutes_back = minutes_back
        self.project_name = project_name
        self.fallback_project = fallback_project


class PhoenixClient:
    """Phoenix connection and data fetching"""
    
    def __init__(self, config: PhoenixConfig):
        self.config = config
        self._client = None
    
    def connect(self) -> bool:
        """Establish connection to Phoenix"""
        try:
            self._client = px.Client(endpoint=self.config.endpoint)
            print("✅ Successfully connected to Phoenix Docker instance")
            return True
        except Exception as e:
            print(f"❌ Error connecting to Phoenix: {e}")
            return False
    
    def fetch_spans(self) -> pd.DataFrame:
        """Fetch spans from Phoenix with fallback logic"""
        if not self._client:
            raise Exception("Phoenix client not connected")
        
        # Try main project first
        spans_df = self._client.get_spans_dataframe(project_name=self.config.project_name)
        
        if spans_df.empty:
            print(f"⚠️  No spans found in '{self.config.project_name}' project.")
            print(f"🔄 Trying '{self.config.fallback_project}' project...")
            spans_df = self._client.get_spans_dataframe(project_name=self.config.fallback_project)
            
            if spans_df.empty:
                print(f"❌ No spans found in '{self.config.fallback_project}' project.")
                return pd.DataFrame()
            else:
                print(f"✅ Found {len(spans_df)} spans in '{self.config.fallback_project}' project")
        else:
            print(f"✅ Found {len(spans_df)} spans in '{self.config.project_name}' project")
        
        return spans_df


class SpanAnalyzer:
    """Analyze and process spans"""
    
    @staticmethod
    def filter_llm_spans(spans_df: pd.DataFrame) -> pd.DataFrame:
        """Filter for LLM/OpenAI spans"""
        llm_spans = spans_df[
            (spans_df['span_kind'] == 'LLM') | 
            (spans_df['name'].str.contains('openai', case=False, na=False))
        ]
        
        if llm_spans.empty:
            print("❌ No LLM/OpenAI spans found")
            return pd.DataFrame()
        
        print(f"🎯 Found {len(llm_spans)} LLM spans")
        return llm_spans.sort_values('start_time', ascending=False)
    
    @staticmethod
    def extract_span_details(span) -> LLMCallDetails:
        """Extract detailed information from a span"""
        # Calculate duration
        duration_ms = 'N/A'
        try:
            if pd.notna(span.get('start_time')) and pd.notna(span.get('end_time')):
                start = pd.to_datetime(span['start_time'])
                end = pd.to_datetime(span['end_time'])
                duration_ms = round((end - start).total_seconds() * 1000, 2)
        except:
            pass
        
        # Extract input/output
        input_data = (
            span.get('input') or 
            span.get('input.value') or 
            span.get('attributes.llm.input_messages') or
            'N/A'
        )
        
        output_data = (
            span.get('output') or 
            span.get('output.value') or 
            span.get('attributes.llm.output_messages') or
            'N/A'
        )
        
        return LLMCallDetails(
            span_id=span.get('context.span_id', 'N/A'),
            trace_id=span.get('context.trace_id', 'N/A'),
            name=span.get('name', 'N/A'),
            start_time=span.get('start_time', 'N/A'),
            end_time=span.get('end_time', 'N/A'),
            status=span.get('status_code', 'N/A'),
            duration_ms=duration_ms,
            model=span.get('attributes.llm.model_name', 'N/A'),
            provider=span.get('attributes.llm.provider', span.get('attributes.llm.system', 'N/A')),
            prompt_tokens=span.get('attributes.llm.token_count.prompt', 'N/A'),
            completion_tokens=span.get('attributes.llm.token_count.completion', 'N/A'),
            total_tokens=span.get('attributes.llm.token_count.total', 'N/A'),
            temperature=span.get('attributes.llm.temperature', 'N/A'),
            max_tokens=span.get('attributes.llm.max_tokens', 'N/A'),
            top_p=span.get('attributes.llm.top_p', 'N/A'),
            cost=span.get('attributes.llm.cost', 'N/A'),
            finish_reason=span.get('attributes.llm.response.finish_reason', 'N/A'),
            input_data=input_data,
            output_data=output_data
        )
    
    def group_by_start_time(self, llm_spans: pd.DataFrame, minutes_back: int) -> Tuple[Dict, List]:
        """Group spans by start time and filter recent ones"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=minutes_back)
        print(f"🕐 Looking for calls from the past {minutes_back} minutes (since {cutoff_time})")
        
        time_groups = defaultdict(list)
        recent_spans = []
        
        for idx, (_, span) in enumerate(llm_spans.iterrows()):
            start_time = span.get('start_time')
            
            if pd.notna(start_time):
                start_datetime = pd.to_datetime(start_time)
                
                # Handle timezone comparison
                if start_datetime.tz is None:
                    cutoff_time_compare = cutoff_time.replace(tzinfo=None)
                else:
                    cutoff_time_compare = cutoff_time
                
                if start_datetime >= cutoff_time_compare:
                    recent_spans.append((idx, span))
                    time_key = start_datetime.floor('S')
                    time_groups[time_key].append((idx, span))
        
        print(f"📊 Found {len(recent_spans)} recent LLM calls")
        
        # Find duplicate groups
        duplicate_groups = {k: v for k, v in time_groups.items() if len(v) > 1}
        
        if duplicate_groups:
            print(f"⚠️  Found {len(duplicate_groups)} time groups with multiple calls!")
        else:
            print("✅ No duplicate start times found")
        
        return duplicate_groups, recent_spans


class EfficiencyAnalyzer:
    """OpenAI-powered efficiency analysis"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.client = openai.OpenAI(api_key=self.api_key) if self.api_key else None
    
    def analyze_grouped_calls(self, duplicate_groups: Dict, ask_permission: bool = True) -> None:
        """Analyze grouped calls for efficiency"""
        if not self.client:
            print("❌ OpenAI client not initialized. Check your API key.")
            return
        
        if not duplicate_groups:
            print("No grouped calls to analyze")
            return
        
        if ask_permission:
            print(f"\n{'='*80}")
            print(f"🤖 OPENAI EFFICIENCY ANALYSIS AVAILABLE")
            print(f"{'='*80}")
            print(f"Found {len(duplicate_groups)} groups with identical start times.")
            print("This suggests model comparison testing.")
            
            user_input = input("\nAnalyze with OpenAI? (y/n): ").lower().strip()
            if user_input not in ['y', 'yes']:
                print("Skipping OpenAI analysis.")
                return
        
        print(f"\n{'='*100}")
        print(f"🤖 SENDING DATA TO OPENAI FOR MODEL EFFICIENCY ANALYSIS")
        print(f"{'='*100}")
        
        for group_num, (start_time, spans) in enumerate(duplicate_groups.items(), 1):
            self._analyze_single_group(group_num, start_time, spans)
    
    def _analyze_single_group(self, group_num: int, start_time: Any, spans: List) -> None:
        """Analyze a single group of spans"""
        print(f"\n🔍 Analyzing Group #{group_num} (Start Time: {start_time})")
        
        # Prepare analysis data
        analysis_data = []
        for call_num, (original_idx, span) in enumerate(spans, 1):
            span_details = SpanAnalyzer.extract_span_details(span)
            
            variant_data = {
                "variant": f"Variant {chr(64 + call_num)}",
                "model": span_details.model,
                "prompt_tokens": span_details.prompt_tokens,
                "completion_tokens": span_details.completion_tokens,
                "total_tokens": span_details.total_tokens,
                "duration_ms": span_details.duration_ms,
                "input_preview": str(span_details.input_data)[:200] if span_details.input_data != 'N/A' else 'N/A',
                "output_preview": str(span_details.output_data)[:200] if span_details.output_data != 'N/A' else 'N/A'
            }
            analysis_data.append(variant_data)
        
        # Create analysis prompt
        prompt = f"""
I ran the same prompt across multiple OpenAI models simultaneously and tracked performance. Analyze efficiency in terms of cost vs quality.

Performance Data:
{json.dumps(analysis_data, indent=2)}

Provide:
1. Comparison table (Variant, Model, Token Usage, Time)
2. Key observations about token efficiency in 2-3 lines
3. Recommendations for best cost/performance ratio in 2-3 lines
4. Provide a conclusion on which model is the most efficient for this prompt based on the data provided.

Format with clear headers and bullet points.
"""
        
        try:
            print("   🔄 Sending data to OpenAI...")
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert AI model performance analyst. Provide actionable insights about model efficiency and cost optimization."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.3
            )
            
            print(f"\n📊 OPENAI ANALYSIS FOR GROUP #{group_num}:")
            print(f"{'─' * 80}")
            print(response.choices[0].message.content)
            print(f"{'─' * 80}")
            
            # Cost tracking
            analysis_cost = response.usage.total_tokens * 0.000002
            print(f"💰 Analysis cost: ~${analysis_cost:.4f} ({response.usage.total_tokens} tokens)")
            
        except Exception as e:
            print(f"❌ Error in OpenAI analysis: {e}")


class DisplayManager:
    """Handle all display operations"""
    
    @staticmethod
    def format_json_output(data: Any) -> str:
        """Format JSON data for readability"""
        if isinstance(data, dict):
            return json.dumps(data, indent=2, ensure_ascii=False)
        elif isinstance(data, str):
            try:
                parsed = json.loads(data)
                return json.dumps(parsed, indent=2, ensure_ascii=False)
            except:
                return data
        return str(data)
    
    def display_grouped_calls(self, duplicate_groups: Dict) -> None:
        """Display grouped calls with same start times"""
        if not duplicate_groups:
            return
        
        print(f"\n{'='*100}")
        print(f"🔄 CALLS WITH IDENTICAL START TIMES (POTENTIAL COMPARISONS)")
        print(f"{'='*100}")
        
        for group_num, (start_time, spans) in enumerate(duplicate_groups.items(), 1):
            self._display_single_group(group_num, start_time, spans)
    
    def _display_single_group(self, group_num: int, start_time: Any, spans: List) -> None:
        """Display a single group of spans"""
        print(f"\n{'🕐' * 3} GROUP #{group_num} - Start Time: {start_time} {'🕐' * 3}")
        print(f"📊 Number of calls: {len(spans)}")
        print(f"{'─' * 80}")
        
        total_tokens_group = 0
        
        for call_num, (original_idx, span) in enumerate(spans, 1):
            span_details = SpanAnalyzer.extract_span_details(span)
            
            print(f"\n{'┌' + '─' * 50} CALL {call_num}/{len(spans)} {'─' * 10}")
            print(f"│ Position: #{original_idx + 1}")
            print(f"│ Model: {span_details.model}")
            print(f"│ Total Tokens: {span_details.total_tokens}")
            print(f"│ Duration: {span_details.duration_ms} ms")
            print(f"└{'─' * 60}")
            
            # Add to group total
            try:
                if span_details.total_tokens != 'N/A':
                    total_tokens_group += int(span_details.total_tokens)
            except:
                pass
        
        print(f"\n📈 GROUP SUMMARY:")
        print(f"   Total calls: {len(spans)}")
        print(f"   Combined tokens: {total_tokens_group}")
        if total_tokens_group > 0:
            print(f"   Average tokens per call: {total_tokens_group / len(spans):.1f}")
    
    def display_recent_calls_summary(self, recent_spans: List, minutes_back: int = 15) -> None:
        """Display summary of recent calls"""
        if not recent_spans:
            return
        
        print(f"\n{'='*80}")
        print(f"📋 RECENT CALLS SUMMARY (Past {minutes_back} minutes)")
        print(f"{'='*80}")
        
        for call_num, (original_idx, span) in enumerate(recent_spans[:10], 1):
            span_details = SpanAnalyzer.extract_span_details(span)
            print(f"#{call_num:2d} | {span_details.start_time} | Tokens: {span_details.total_tokens:>6.0f} | Duration: {span_details.duration_ms:>8.2f}ms")
        
        if len(recent_spans) > 10:
            print(f"... and {len(recent_spans) - 10} more recent calls")


class PhoenixAnalyzer:
    """Main analyzer class that orchestrates everything"""
    
    def __init__(self, config: PhoenixConfig = None):
        load_dotenv()
        self.config = config or PhoenixConfig()
        self.phoenix_client = PhoenixClient(self.config)
        self.span_analyzer = SpanAnalyzer()
        self.efficiency_analyzer = EfficiencyAnalyzer()
        self.display_manager = DisplayManager()
    
    def run_analysis(self) -> None:
        """Run the complete analysis pipeline"""
        # Connect to Phoenix
        if not self.phoenix_client.connect():
            return
        
        # Fetch and filter spans
        spans_df = self.phoenix_client.fetch_spans()
        if spans_df.empty:
            return
        
        llm_spans = self.span_analyzer.filter_llm_spans(spans_df)
        if llm_spans.empty:
            return
        
        # Group by start time
        duplicate_groups, recent_spans = self.span_analyzer.group_by_start_time(
            llm_spans, self.config.minutes_back
        )
        
        # Display results
        if duplicate_groups:
            self.display_manager.display_grouped_calls(duplicate_groups)
            self.efficiency_analyzer.analyze_grouped_calls(duplicate_groups)
        
        self.display_manager.display_recent_calls_summary(recent_spans, self.config.minutes_back)


if __name__ == "__main__":
    # Configuration
    config = PhoenixConfig(
        endpoint="http://localhost:6006",
        minutes_back=15,
        project_name="playground",
        fallback_project="default"
    )
    
    # Run analysis
    analyzer = PhoenixAnalyzer(config)
    analyzer.run_analysis()
