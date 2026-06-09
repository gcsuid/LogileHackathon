# LogileHackathon - Log Analysis & Recipe Validation

This repository contains two independent but complementary projects for operational excellence:

1. **stat1**: LogScope - A log analysis dashboard for incident investigation and performance monitoring
2. **stat6**: Recipe Validation CLI - An agentic system for validating retail recipes using LLM

Both projects are designed as MVPs (Minimum Viable Products) with no persistent storage, focusing on rapid analysis and decision-making.

---

## Project 1: stat1 - LogScope (Log Analysis Dashboard)

### What It Does

LogScope is a Python + Flask web application that analyzes application logs to identify issues and track performance metrics.

**Key Features**:
- **Dynamic Log Parsing**: Converts semi-structured logs into structured records
- **Single-File Analysis**: Dashboard with KPIs (error rate, top failures, slow requests, DB latency)
- **Baseline Comparison**: Compare before-and-after logs to detect regressions
- **Anomaly Detection**: Identifies unusual patterns and failures

### How It Works

1. **Log Parsing**
   - Format: `timestamp level [service] message key=value ...`
   - Extracts: timestamp, log level, service, message, key-value fields
   - Handles malformed lines gracefully

2. **Metrics Extraction**
   - Total logs counted
   - Error rate (ERROR/WARNING ratio)
   - Top failing components/services
   - Common failure reasons
   - Slow request detection (queries > threshold)
   - DB latency analysis
   - Repeated login failures
   - Malformed line tracking

3. **Comparison Mode**
   - Baseline: older/stable/before-deploy log
   - Candidate: newer/changed/after-deploy log
   - Computes deltas for:
     - Error rate change
     - Error count change
     - Response time regression (p95)
     - DB query latency regression
     - Worsened services
     - New failure reasons
     - Service footprint changes

### Run LogScope

**Start the web server**:
```bash
cd stat1
python app.py
```

Then open: `http://127.0.0.1:5000`

**CLI mode** (direct log analysis):
```bash
python analyzer.py sample.log
python analyzer.py sample.log --json-out out/structured.json --report-out out/report.txt
```

### Files

```
stat1/
├── app.py                    # Flask web application
├── analyzer.py               # Log parsing and metrics engine
├── templates/index.html      # Web UI dashboard
├── sample.log                # Sample candidate log
├── sample_baseline.log       # Sample baseline log
├── README.md                 # Project documentation
└── requirements.txt          # Python dependencies
```

---

## Project 2: stat6 - Recipe Validation CLI

### What It Does

Recipe Validation CLI is a command-line agentic system that validates retail recipes before production using specialized agents backed by LLM decision-making.

**Three validation checks**:
1. **Completeness Agent**: Validates required fields (deterministic, no LLM)
2. **Cost & Margin Agent**: Checks if cost fits margin target + suggests optimizations (LLM-powered)
3. **Equipment Agent**: Verifies store has required equipment + suggests workarounds (LLM-powered)

### How It Works

**Agent Architecture**:
- Uses Hugging Face Hosted Inference API (no local model)
- Model: Mistral-7B (configurable)
- 2 agents use LLM for creative suggestions, 1 uses pure Python logic

**Workflow**:
```
Recipe Input
    ↓
[Completeness Agent] → Check required fields (local)
    ↓
[Cost Agent] → Calculate cost + get LLM suggestions
    ↓
[Equipment Agent] → Check availability + get LLM workarounds
    ↓
Final Status: approved / needs_cost_review / needs_equipment / rejected
    ↓
JSON Output
```

**Why This Design**:
- Completeness is deterministic → no LLM needed
- Cost suggestions require creativity → LLM adds value
- Equipment workarounds are contextual → LLM adds value
- Fallbacks ensure robustness if LLM fails

### Run the CLI

```bash
cd stat6

# List all samples
python main.py --list

# Run random sample
python main.py

# Run specific sample
python main.py --index 2
```

### Files

```
stat6/
├── main.py                   # CLI orchestration and agents
├── llm.py                    # Hugging Face API integration
├── sample_data.py            # 10 test recipes
├── requirements.txt          # Python dependencies
└── readme.md                 # Detailed documentation
```

---

## Installation & Setup

### Requirements

- Python 3.13+
- Flask (for stat1)
- python-dotenv (for stat6)
- Hugging Face API token (for stat6)

### Install Dependencies

**For stat1 (log analysis)**:
```bash
cd stat1
pip install -r requirements.txt
```

**For stat6 (recipe validation)**:
```bash
cd stat6
pip install -r requirements.txt
```

### Configure Environment

Create `.env` file in repository root:
```env
HF_TOKEN=your_hugging_face_token_here
HF_MODEL=mistralai/Mistral-7B-Instruct-v0.3
HF_TIMEOUT_SECONDS=20
```

Or set environment variables:
```bash
export HF_TOKEN=your_token
export HF_MODEL=mistralai/Mistral-7B-Instruct-v0.3
```

---

## Code Quality & Optimization

### Recent Cleanup (stat6)

Removed redundant code and optimized performance:

1. **Removed unused `recipes` dictionary** - Was never queried or used (memory waste)
2. **Removed redundant LLM call from completeness_agent** - Now uses pure Python (33% fewer LLM calls)
3. **Optimized copy operations** - Changed from `deepcopy` to shallow `.copy()` (faster)
4. **Extracted helper function** - Consolidated duplicate merge logic
5. **Removed unused imports** - Cleaned up `copy` module
6. **Removed unused output fields** - Eliminated `sample_dataset_count` noise

### Cleanup (stat1)

1. **Removed unused `defaultdict` import** - Code was only using `Counter`
2. **Removed unused files** - Deleted large test files and generated reports
3. **Code is deterministic and robust** - Handles malformed logs gracefully

---

## Project Structure

```
LogileHackathon/
├── stat1/                    # Log Analysis Dashboard
│   ├── app.py
│   ├── analyzer.py
│   ├── templates/
│   │   └── index.html
│   ├── sample.log
│   ├── sample_baseline.log
│   ├── README.md
│   └── requirements.txt
│
├── stat6/                    # Recipe Validation CLI
│   ├── main.py
│   ├── llm.py
│   ├── sample_data.py
│   ├── readme.md
│   └── requirements.txt
│
├── README.md                 # This file
└── .gitignore
```

---

## Design Philosophy

Both projects follow these principles:

1. **No Persistent Storage**: All data is in-memory (dictionaries) or output to stdout
2. **Minimal Dependencies**: Uses standard library + Flask/LLM APIs
3. **Stateless CLI**: Each run is independent, no state carried between invocations
4. **Graceful Degradation**: Falls back to defaults if LLM or parsing fails
5. **Clear JSON Output**: Results are JSON for easy integration with other tools

---

## Future Enhancements

**stat1 - LogScope**:
- Database backend for log storage
- Real-time log ingestion via API
- Advanced anomaly detection (ML-based)
- Alert rules and notifications
- Multi-tenant support

**stat6 - Recipe Validation**:
- Persistent recipe database
- REST API for validation
- Recipe version control
- Production deployment workflow
- Cost tracking over time
- Equipment management dashboard

---

## Usage Examples

### Example 1: Analyze Production Logs

```bash
cd stat1
python app.py
# Open http://localhost:5000
# Upload production.log → get KPI dashboard
# Upload baseline.log and after_deploy.log → compare regressions
```

### Example 2: Validate New Recipe

```bash
cd stat6
python main.py --index 5
# Output: JSON with completeness/cost/equipment validation
# Status: "approved" or specific issue
```

### Example 3: Validate All Samples

```bash
cd stat6
python main.py --list
# Shows all 10 recipes
# Run each with python main.py --index 1-10
```

---

## Documentation

- **stat1**: See [stat1/README.md](./stat1/README.md) for detailed log analysis documentation
- **stat6**: See [stat6/readme.md](./stat6/readme.md) for detailed recipe validation and LLM architecture

---

## License

This project is part of a hackathon challenge.

---

## Quick Start Checklist

- [ ] Install Python 3.13+
- [ ] Clone repository
- [ ] Set up `.env` with HF_TOKEN
- [ ] Install stat1: `cd stat1 && pip install -r requirements.txt`
- [ ] Install stat6: `cd stat6 && pip install -r requirements.txt`
- [ ] Try stat1: `cd stat1 && python app.py` then open http://localhost:5000
- [ ] Try stat6: `cd stat6 && python main.py --list` then `python main.py --index 1`
