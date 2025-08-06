"""
Export functionality for Phoenix Analyzer results
"""
import json
import csv
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path


class DataExporter:
    """Export analysis results to various formats"""
    
    def __init__(self, output_dir: str = "exports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def export_grouped_calls_to_csv(self, duplicate_groups: Dict, filename: str = None) -> str:
        """Export grouped calls to CSV format"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"grouped_calls_{timestamp}.csv"
        
        filepath = self.output_dir / filename
        
        rows = []
        for group_num, (start_time, spans) in enumerate(duplicate_groups.items(), 1):
            for call_num, (original_idx, span) in enumerate(spans, 1):
                from phoenix_analyzer import SpanAnalyzer
                span_details = SpanAnalyzer.extract_span_details(span)
                
                rows.append({
                    'group_number': group_num,
                    'call_number': call_num,
                    'start_time': start_time,
                    'model': span_details.model,
                    'prompt_tokens': span_details.prompt_tokens,
                    'completion_tokens': span_details.completion_tokens,
                    'total_tokens': span_details.total_tokens,
                    'duration_ms': span_details.duration_ms,
                    'temperature': span_details.temperature,
                    'max_tokens': span_details.max_tokens,
                    'cost': span_details.cost,
                    'status': span_details.status
                })
        
        df = pd.DataFrame(rows)
        df.to_csv(filepath, index=False)
        print(f"📄 Exported grouped calls to: {filepath}")
        return str(filepath)
    
    def export_efficiency_report(self, duplicate_groups: Dict, analysis_results: Dict = None, filename: str = None) -> str:
        """Export comprehensive efficiency report"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"efficiency_report_{timestamp}.json"
        
        filepath = self.output_dir / filename
        
        report = {
            'metadata': {
                'export_time': datetime.now().isoformat(),
                'total_groups': len(duplicate_groups),
                'analyzer_version': '1.0.0'
            },
            'groups': []
        }
        
        for group_num, (start_time, spans) in enumerate(duplicate_groups.items(), 1):
            group_data = {
                'group_id': group_num,
                'start_time': str(start_time),
                'calls': [],
                'summary': {
                    'total_calls': len(spans),
                    'models_used': [],
                    'total_tokens': 0,
                    'average_duration': 0
                }
            }
            
            total_duration = 0
            total_tokens = 0
            
            for call_num, (original_idx, span) in enumerate(spans, 1):
                from phoenix_analyzer import SpanAnalyzer
                span_details = SpanAnalyzer.extract_span_details(span)
                
                call_data = {
                    'call_id': call_num,
                    'model': span_details.model,
                    'tokens': {
                        'prompt': span_details.prompt_tokens,
                        'completion': span_details.completion_tokens,
                        'total': span_details.total_tokens
                    },
                    'performance': {
                        'duration_ms': span_details.duration_ms,
                        'temperature': span_details.temperature,
                        'max_tokens': span_details.max_tokens
                    },
                    'cost': span_details.cost,
                    'status': span_details.status
                }
                
                group_data['calls'].append(call_data)
                
                # Update summary
                if span_details.model not in group_data['summary']['models_used']:
                    group_data['summary']['models_used'].append(span_details.model)
                
                try:
                    if span_details.total_tokens != 'N/A':
                        total_tokens += int(span_details.total_tokens)
                    if span_details.duration_ms != 'N/A':
                        total_duration += float(span_details.duration_ms)
                except:
                    pass
            
            group_data['summary']['total_tokens'] = total_tokens
            group_data['summary']['average_duration'] = total_duration / len(spans) if spans else 0
            
            report['groups'].append(group_data)
        
        # Add analysis results if provided
        if analysis_results:
            report['openai_analysis'] = analysis_results
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"📊 Exported efficiency report to: {filepath}")
        return str(filepath)
    
    def export_to_excel(self, duplicate_groups: Dict, filename: str = None) -> str:
        """Export to Excel with multiple sheets"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"phoenix_analysis_{timestamp}.xlsx"
        
        filepath = self.output_dir / filename
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # Summary sheet
            summary_data = []
            detailed_data = []
            
            for group_num, (start_time, spans) in enumerate(duplicate_groups.items(), 1):
                group_tokens = 0
                group_duration = 0
                models_in_group = []
                
                for call_num, (original_idx, span) in enumerate(spans, 1):
                    from phoenix_analyzer import SpanAnalyzer
                    span_details = SpanAnalyzer.extract_span_details(span)
                    
                    # Detailed data
                    detailed_data.append({
                        'Group': group_num,
                        'Call': call_num,
                        'Start Time': start_time,
                        'Model': span_details.model,
                        'Prompt Tokens': span_details.prompt_tokens,
                        'Completion Tokens': span_details.completion_tokens,
                        'Total Tokens': span_details.total_tokens,
                        'Duration (ms)': span_details.duration_ms,
                        'Temperature': span_details.temperature,
                        'Max Tokens': span_details.max_tokens,
                        'Cost': span_details.cost,
                        'Status': span_details.status
                    })
                    
                    # Aggregate for summary
                    try:
                        if span_details.total_tokens != 'N/A':
                            group_tokens += int(span_details.total_tokens)
                        if span_details.duration_ms != 'N/A':
                            group_duration += float(span_details.duration_ms)
                        if span_details.model not in models_in_group:
                            models_in_group.append(span_details.model)
                    except:
                        pass
                
                summary_data.append({
                    'Group': group_num,
                    'Start Time': start_time,
                    'Number of Calls': len(spans),
                    'Models Used': ', '.join(models_in_group),
                    'Total Tokens': group_tokens,
                    'Average Duration (ms)': group_duration / len(spans) if spans else 0
                })
            
            # Write sheets
            pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
            pd.DataFrame(detailed_data).to_excel(writer, sheet_name='Detailed Data', index=False)
        
        print(f"📈 Exported Excel report to: {filepath}")
        return str(filepath)


class ReportGenerator:
    """Generate formatted reports"""
    
    def __init__(self, exporter: DataExporter = None):
        self.exporter = exporter or DataExporter()
    
    def generate_markdown_report(self, duplicate_groups: Dict, analysis_results: Dict = None, filename: str = None) -> str:
        """Generate a markdown report"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"analysis_report_{timestamp}.md"
        
        filepath = self.exporter.output_dir / filename
        
        with open(filepath, 'w') as f:
            f.write("# Phoenix LLM Analysis Report\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"**Total Groups with Identical Start Times:** {len(duplicate_groups)}\n\n")
            
            for group_num, (start_time, spans) in enumerate(duplicate_groups.items(), 1):
                f.write(f"## Group {group_num}\n\n")
                f.write(f"**Start Time:** {start_time}\n")
                f.write(f"**Number of Calls:** {len(spans)}\n\n")
                
                f.write("| Variant | Model | Prompt Tokens | Completion Tokens | Total Tokens | Duration (ms) |\n")
                f.write("|---------|-------|---------------|-------------------|--------------|---------------|\n")
                
                for call_num, (original_idx, span) in enumerate(spans, 1):
                    from phoenix_analyzer import SpanAnalyzer
                    span_details = SpanAnalyzer.extract_span_details(span)
                    
                    f.write(f"| {chr(64 + call_num)} | {span_details.model} | {span_details.prompt_tokens} | "
                           f"{span_details.completion_tokens} | {span_details.total_tokens} | {span_details.duration_ms} |\n")
                
                f.write("\n")
            
            if analysis_results:
                f.write("## OpenAI Analysis Results\n\n")
                for group_id, result in analysis_results.items():
                    f.write(f"### Group {group_id}\n\n")
                    f.write(f"```\n{result}\n```\n\n")
        
        print(f"📝 Generated markdown report: {filepath}")
        return str(filepath)
