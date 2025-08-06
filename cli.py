"""
Command Line Interface for Phoenix Analyzer
"""
import argparse
import sys
from config import PhoenixConfig, DEVELOPMENT_CONFIG, PRODUCTION_CONFIG, EXTENDED_ANALYSIS_CONFIG
from phoenix_analyzer import PhoenixAnalyzer
from exporters import DataExporter, ReportGenerator


def create_parser():
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(
        description="Phoenix LLM Call Analyzer - Analyze and compare LLM model efficiency",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Run with default settings
  %(prog)s --minutes-back 30        # Look back 30 minutes
  %(prog)s --config dev             # Use development config
  %(prog)s --export-csv             # Export results to CSV
  %(prog)s --no-openai              # Skip OpenAI analysis
  %(prog)s --endpoint http://localhost:7006  # Custom Phoenix endpoint
        """
    )
    
    # Phoenix connection
    parser.add_argument(
        '--endpoint',
        default='http://localhost:6006',
        help='Phoenix endpoint URL (default: http://localhost:6006)'
    )
    
    parser.add_argument(
        '--project',
        default='playground',
        help='Phoenix project name (default: playground)'
    )
    
    parser.add_argument(
        '--fallback-project',
        default='default',
        help='Fallback project name (default: default)'
    )
    
    # Time filtering
    parser.add_argument(
        '--minutes-back',
        type=int,
        default=15,
        help='Look back N minutes for recent calls (default: 15)'
    )
    
    # Configuration presets
    parser.add_argument(
        '--config',
        choices=['dev', 'prod', 'extended'],
        help='Use predefined configuration (dev/prod/extended)'
    )
    
    # OpenAI analysis
    parser.add_argument(
        '--no-openai',
        action='store_true',
        help='Skip OpenAI efficiency analysis'
    )
    
    parser.add_argument(
        '--openai-model',
        default='gpt-4o-mini',
        help='OpenAI model for analysis (default: gpt-4o-mini)'
    )
    
    parser.add_argument(
        '--auto-analyze',
        action='store_true',
        help='Automatically run OpenAI analysis without asking'
    )
    
    # Export options
    parser.add_argument(
        '--export-csv',
        action='store_true',
        help='Export results to CSV'
    )
    
    parser.add_argument(
        '--export-excel',
        action='store_true',
        help='Export results to Excel'
    )
    
    parser.add_argument(
        '--export-json',
        action='store_true',
        help='Export results to JSON'
    )
    
    parser.add_argument(
        '--export-markdown',
        action='store_true',
        help='Export results to Markdown'
    )
    
    parser.add_argument(
        '--output-dir',
        default='exports',
        help='Output directory for exports (default: exports)'
    )
    
    # Display options
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Reduce output verbosity'
    )
    
    parser.add_argument(
        '--max-recent',
        type=int,
        default=10,
        help='Maximum recent calls to display (default: 10)'
    )
    
    return parser


def get_config_from_args(args):
    """Create configuration from command line arguments"""
    # Use preset configs
    if args.config == 'dev':
        config = DEVELOPMENT_CONFIG
    elif args.config == 'prod':
        config = PRODUCTION_CONFIG
    elif args.config == 'extended':
        config = EXTENDED_ANALYSIS_CONFIG
    else:
        config = PhoenixConfig()
    
    # Override with command line arguments
    if args.endpoint != 'http://localhost:6006':
        config.endpoint = args.endpoint
    if args.project != 'playground':
        config.project_name = args.project
    if args.fallback_project != 'default':
        config.fallback_project = args.fallback_project
    if args.minutes_back != 15:
        config.minutes_back = args.minutes_back
    if args.openai_model != 'gpt-4o-mini':
        config.openai_model = args.openai_model
    if args.max_recent != 10:
        config.max_recent_calls_display = args.max_recent
    
    return config


class CLIAnalyzer(PhoenixAnalyzer):
    """CLI version of Phoenix Analyzer with additional features"""
    
    def __init__(self, config: PhoenixConfig, args):
        super().__init__(config)
        self.args = args
        self.exporter = DataExporter(args.output_dir)
        self.report_generator = ReportGenerator(self.exporter)
        self.analysis_results = {}
    
    def run_analysis(self):
        """Run analysis with CLI-specific features"""
        if not self.args.quiet:
            print("🚀 Starting Phoenix LLM Analysis...")
            print(f"📊 Configuration: {self.config.minutes_back} minutes back, endpoint: {self.config.endpoint}")
        
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
            if not self.args.quiet:
                self.display_manager.display_grouped_calls(duplicate_groups)
            
            # OpenAI analysis
            if not self.args.no_openai:
                ask_permission = not self.args.auto_analyze
                self.efficiency_analyzer.analyze_grouped_calls(duplicate_groups, ask_permission)
        
        if not self.args.quiet:
            self.display_manager.display_recent_calls_summary(recent_spans, self.config.minutes_back)
        
        # Export results
        self._handle_exports(duplicate_groups)
        
        if not self.args.quiet:
            print("✅ Analysis complete!")
    
    def _handle_exports(self, duplicate_groups):
        """Handle all export operations"""
        if not duplicate_groups:
            return
        
        exported_files = []
        
        if self.args.export_csv:
            file_path = self.exporter.export_grouped_calls_to_csv(duplicate_groups)
            exported_files.append(file_path)
        
        if self.args.export_excel:
            file_path = self.exporter.export_to_excel(duplicate_groups)
            exported_files.append(file_path)
        
        if self.args.export_json:
            file_path = self.exporter.export_efficiency_report(duplicate_groups, self.analysis_results)
            exported_files.append(file_path)
        
        if self.args.export_markdown:
            file_path = self.report_generator.generate_markdown_report(duplicate_groups, self.analysis_results)
            exported_files.append(file_path)
        
        if exported_files and not self.args.quiet:
            print(f"\n📁 Exported {len(exported_files)} files:")
            for file_path in exported_files:
                print(f"   • {file_path}")


def main():
    """Main CLI entry point"""
    parser = create_parser()
    args = parser.parse_args()
    
    try:
        # Create configuration
        config = get_config_from_args(args)
        
        # Run analysis
        analyzer = CLIAnalyzer(config, args)
        analyzer.run_analysis()
        
    except KeyboardInterrupt:
        print("\n❌ Analysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        if not args.quiet:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
