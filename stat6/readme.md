# Retail Recipe Approval System

This project simulates an agentic workflow for approving a retail recipe using multiple Python agents and a local Ollama-backed LLM.

The workflow covers:
- recipe validation
- cost analysis
- finance approval
- store readiness assessment
- final decisioning through a central orchestrator

## Tech Stack

- Python
- `langchain_community.llms.Ollama`
- Local Ollama model: `llama3`
- No external APIs

## Project Structure

```text
stat6/
├── main.py
├── llm.py
├── requirements.txt
├── readme.md
├── agents/
│   ├── __init__.py
│   ├── validation_agent.py
│   ├── cost_agent.py
│   ├── finance_agent.py
│   └── store_agent.py
├── data/
│   ├── __init__.py
│   └── dummy_data.py
└── workflow/
    ├── __init__.py
    └── orchestrator.py
```

## How It Works

### 1. Validation Agent
Checks whether the recipe has:
- required fields
- valid ingredient quantities
- basic structural consistency

### 2. Cost Agent
Calculates:
- total batch cost
- cost per unit
- basic cost reduction suggestions

### 3. Finance Agent
Reviews:
- whether the recipe stays within the allowed batch cost
- expected margin impact
- approval or rejection

### 4. Store Readiness Agent
Checks whether the target store has the required equipment and returns a readiness score.

### 5. Orchestrator
Runs the agents in sequence:
1. Validation
2. Costing
3. Finance
4. Store readiness

It then combines the outputs into one final decision:
- `READY`
- `NEEDS CHANGES`
- `REJECTED`

## Dummy Data

The sample data in `data/dummy_data.py` includes:
- one sample recipe
- mock ingredient prices
- mock store equipment availability
- finance thresholds

## LLM Behavior

Each agent calls `run_llm()` from `llm.py`, which uses:

```python
Ollama(model="qwen2.5:0.5b  ")
```

The code also includes a fast fallback path. If Ollama is not running or is too slow to respond, the system still completes using deterministic local logic and returns a fallback summary string instead of failing.

## Setup

Install dependencies:

```bash
pip install -r requirements.txt
```

Make sure Ollama is installed locally and that the `qwen2.5:0.5b  ` model is available.

Example:

```bash
ollama pull llama3
ollama serve
```

## Run

```bash
python main.py
```

## Example Output

```text
=== FINAL REPORT ===
Recipe: Spicy Paneer Wrap
Validation: PASS
Cost: INR 666.20 per batch
Cost Per Unit: INR 66.62
Finance: REJECTED (margin too low)
Store Readiness: 80% (missing: grill)
Final Decision: REJECTED
```

## Bonus Logic

If finance rejects the recipe, the orchestrator attempts one simple retry by slightly reducing premium ingredient quantities and re-running cost and finance checks.

## Notes

- The project uses functions instead of classes to keep the implementation simple.
- All data is mocked locally.
- No external services are used.
- The current dummy recipe is intentionally configured to demonstrate a rejection path in finance and a missing equipment path in store readiness.

