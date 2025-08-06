# Phoenix LLM Analyzer

A modular, extensible tool for analyzing and comparing LLM model efficiency using Phoenix tracing data.

## 🚀 Features

### Core Functionality
- **Phoenix Integration**: Connect to Phoenix Docker instances
- **LLM Call Analysis**: Extract detailed metrics from traced calls
- **Model Comparison**: Group calls by identical start times (playground comparisons)
- **OpenAI Analysis**: Automated efficiency analysis using GPT models
- **Multiple Export Formats**: CSV, Excel, JSON, Markdown

### Key Improvements Over Original Script
- **Class-based Architecture**: Modular, maintainable code
- **Configuration Management**: Easy setup with presets
- **Command Line Interface**: Run from terminal with options
- **Data Export**: Save results in multiple formats
- **Type Hints**: Better code documentation and IDE support
- **Error Handling**: Robust error management
- **Extensible Design**: Easy to add new features

## 📦 Installation

```bash
# Install dependencies
pip install -r requirements_analyzer.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your OPENAI_API_KEY
```

## 🎯 Usage

### Basic Usage
```bash
# Run with default settings (15 minutes back)
python phoenix_analyzer.py

# Or use the CLI for more options
python cli.py
```

### CLI Options
```bash
# Look back 30 minutes
python cli.py --minutes-back 30

# Use development config (5 minutes, fewer displays)
python cli.py --config dev

# Auto-analyze without prompts
python cli.py --auto-analyze

# Export to multiple formats
python cli.py --export-csv --export-excel --export-markdown

# Custom Phoenix endpoint
python cli.py --endpoint http://localhost:7006

# Quiet mode (minimal output)
python cli.py --quiet --export-json
```

### Programmatic Usage
```python
from config import PhoenixConfig
from phoenix_analyzer import PhoenixAnalyzer

# Custom configuration
config = PhoenixConfig(
    endpoint="http://localhost:6006",
    minutes_back=30,
    project_name="my_project"
)

# Run analysis
analyzer = PhoenixAnalyzer(config)
analyzer.run_analysis()
```

## 🔧 Configuration

### Environment Variables
```bash
OPENAI_API_KEY=your_openai_api_key_here
```

### Configuration Presets
- **Development**: `--config dev` (5 minutes, minimal display)
- **Production**: `--config prod` (60 minutes, comprehensive)
- **Extended**: `--config extended` (120 minutes, detailed analysis)

## 📊 Export Formats

### CSV Export
- Structured data for spreadsheet analysis
- Contains all token metrics and timing data

### Excel Export
- Multiple sheets: Summary and Detailed Data
- Formatted for business reporting

### JSON Export
- Complete data structure with metadata
- Includes OpenAI analysis results
- Machine-readable format

### Markdown Export
- Human-readable reports
- Tables and formatted analysis
- Great for documentation

## 🏗️ Architecture

### Core Classes
- **PhoenixAnalyzer**: Main orchestrator
- **PhoenixClient**: Phoenix connection management
- **SpanAnalyzer**: Data processing and grouping
- **EfficiencyAnalyzer**: OpenAI-powered analysis
- **DisplayManager**: Output formatting
- **DataExporter**: Multi-format exports

### Data Flow
1. Connect to Phoenix → 2. Fetch spans → 3. Filter LLM calls → 
4. Group by time → 5. Analyze efficiency → 6. Display/Export results

## 🔄 Extensibility

### Adding New Export Formats
```python
class MyCustomExporter:
    def export_to_custom_format(self, data):
        # Your custom export logic
        pass
```

### Custom Analysis
```python
class MyCustomAnalyzer:
    def analyze_performance(self, spans):
        # Your custom analysis logic
        pass
```

### Configuration Extensions
```python
@dataclass
class ExtendedConfig(PhoenixConfig):
    my_custom_setting: str = "default_value"
```

## 🎛️ Advanced Features

### Batch Processing
```bash
# Process multiple time windows
for i in {5,15,30,60}; do
    python cli.py --minutes-back $i --export-csv --quiet
done
```

### Automated Reporting
```bash
# Daily analysis with auto-export
python cli.py --config prod --auto-analyze --export-markdown --quiet
```

### Integration with CI/CD
```bash
# Use in automated pipelines
python cli.py --quiet --export-json --output-dir ./reports
```

## 📈 Example Output

```
✅ Successfully connected to Phoenix Docker instance
✅ Found 23 spans in playground project
🎯 Found 8 LLM spans
🕐 Looking for calls from the past 15 minutes
📊 Found 6 recent LLM calls
⚠️  Found 2 time groups with multiple calls!

🔄 CALLS WITH IDENTICAL START TIMES
Group #1 - Model Comparison Detected
├─ Call 1: gpt-4o (156 tokens, 2.8s)
├─ Call 2: gpt-3.5-turbo (203 tokens, 1.9s)
└─ Call 3: gpt-4o-mini (189 tokens, 2.1s)

🤖 OpenAI Analysis: gpt-4o-mini offers best cost/performance ratio...

📁 Exported 3 files:
   • exports/grouped_calls_20250806_143022.csv
   • exports/efficiency_report_20250806_143022.json
   • exports/analysis_report_20250806_143022.md
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details
