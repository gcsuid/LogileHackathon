# CLI Recipe Validation MVP

This project is a command-line MVP for validating retail recipes with two specialized validation agents. It uses the Hugging Face hosted inference API for intelligent decision-making. There are no local models, no database, and no web server; all data is kept in Python dictionaries while the CLI process runs.

## What It Solves

Recipe approval usually needs several checks before a recipe can be sent to production:

- **Completeness Check**: Is the recipe complete with all required fields?
- **Cost & Margin Check**: Is the recipe cost acceptable for the target margin?
- **Equipment Check**: Does the store have the required equipment?

This CLI picks a recipe dataset, runs the validation agents, and prints one structured JSON output.

## Project Architecture

The system has **2 main agents** (down from 3 after optimization):

1. **Completeness Agent** - Deterministic local validation (no LLM needed)
2. **Cost & Margin Agent** - Uses LLM for cost optimization suggestions
3. **Equipment Agent** - Uses LLM for feasibility and workaround suggestions

### Why 2 Agents Use LLM and 1 Doesn't

**Completeness Agent**: Uses pure Python validation because:
- Required fields check is deterministic (field exists or doesn't)
- Type validation is deterministic (is it a list? is batch_size > 0?)
- No subjective judgment needed
- No need for LLM call

**Cost & Margin Agent**: Uses LLM because:
- Cost calculation is local (sum ingredients), but suggesting cost-saving alternatives requires creativity
- LLM provides intelligent suggestions like "reduce high-cost ingredients" or "negotiate supplier pricing"
- Provides 2 alternatives for the human reviewer

**Equipment Agent**: Uses LLM because:
- Equipment availability check is local (in STORE_EQUIPMENT dict), but suggesting workarounds requires context
- LLM can suggest "borrow equipment" or "use different store location"
- Provides practical alternatives when equipment is missing

## Implemented Agents

### Agent 1 - Completeness Check (Local Only)

Validates that a recipe has all required fields using Python only:

- `name` - Recipe name (must not be empty)
- `ingredients` - List of ingredient objects
- `batch_size` - Numeric batch size > 0
- `equipment` - List of required equipment

**Return shape**:
```json
{
  "valid": true,
  "missing": [],
  "issues": []
}
```

**Example output if valid**: All checks pass, recipe is complete.

---

### Agent 2 - Cost & Margin Check (Uses LLM)

**Step 1: Local Cost Calculation**
- Sums ingredient costs using flexible cost formats
- Supports: `cost`, `total_cost`, `quantity * unit_cost`, `quantity * price`
- Compares against target margin to get approval

**Supported ingredient cost formats**:
- `{ "name": "flour", "cost": 20 }` ← direct cost
- `{ "name": "flour", "total_cost": 20 }` ← alternative direct cost key
- `{ "name": "flour", "quantity": 2, "unit_cost": 10 }` ← calculated cost
- `{ "name": "flour", "quantity": 2, "price": 10 }` ← alternative price key

**Step 2: LLM-Based Alternatives**
- Sends to Hugging Face: `"Given total_cost=$X and target_margin=Y%, suggest 2 alternatives to lower costs or raise margins."`
- LLM returns creative cost-saving suggestions
- Falls back to hardcoded suggestions if LLM fails or returns invalid format

**Return shape**:
```json
{
  "approved": true,
  "total_cost": 132.5,
  "alternatives": [
    "Reduce high-cost ingredient quantities.",
    "Increase target price or negotiate supplier pricing."
  ]
}
```

---

### Agent 3 - Equipment Check (Uses LLM)

**Step 1: Local Equipment Check**
- Checks recipe equipment against hardcoded store inventory

**Store Equipment Dictionary**:
```python
STORE_EQUIPMENT = {
    "mixer": 1,      # 1 available
    "oven": 2,       # 2 available
    "cooling_rack": 0  # 0 available (not in stock)
}
```

**Step 2: LLM-Based Workarounds**
- Sends to Hugging Face: `"Recipe needs {equipment}. Store has {STORE_EQUIPMENT}. Is it feasible? Suggest workarounds if missing."`
- LLM suggests practical alternatives like borrowing or using another store
- Falls back to hardcoded suggestions if LLM fails

**Return shape**:
```json
{
  "ready": true,
  "missing": [],
  "workarounds": []
}
```

or if equipment is missing:

```json
{
  "ready": false,
  "missing": ["cooling_rack"],
  "workarounds": [
    "Borrow or rent missing equipment before scheduling production.",
    "Move the production run to a store with available equipment."
  ]
}
```

---

## How the LLM Integration Works

### Hugging Face Hosted Inference API

The system uses **Hugging Face Hosted Inference API** (not local models):
- Model: `mistralai/Mistral-7B-Instruct-v0.3` (configurable via `.env`)
- Endpoint: `https://api-inference.huggingface.co/models/{HF_MODEL}`
- Authentication: ****** via `HF_TOKEN` environment variable

### LLM Call Flow (in `llm.py`)

1. **Prompt Sanitization**: 
   - Ensures prompt is not empty
   - Truncates to 6000 characters max
   - Redacts token from logs
   
2. **API Request**:
   - Sends JSON payload with `inputs`, `parameters`, `options`
   - Sets max_new_tokens (220), temperature (0.1), wait_for_model (true)
   - 20-second timeout
   
3. **Response Handling**:
   - Extracts `generated_text` from response
   - Handles both list and dict response formats
   - Sanitizes Unicode characters (INR symbols, smart quotes, dashes, bullets)
   - Converts to ASCII to prevent encoding issues

4. **Error Handling**:
   - Returns empty string on network error, HTTP error, or timeout
   - Agents have fallback suggestions if LLM returns empty

### JSON Extraction (in `main.py`)

Each agent sends a prompt requesting JSON output:
```
Return JSON only with keys: ...
```

The `_extract_json()` function:
- Searches for `{...}` pattern using regex
- Parses and validates as dict
- Returns empty dict if parsing fails
- Agents use `.get()` for safe field access

### Why This Design?

- **Simplicity**: Uses hosted API (no local GPU needed)
- **Reliability**: Falls back gracefully when LLM fails
- **Cost-effective**: Only calls LLM for subjective decisions
- **Transparency**: LLM output is always included in final result

---

## In-Memory Storage

The CLI keeps validated recipes in the output JSON. There is no persistent database.

**Store Equipment** is intentionally hardcoded as:
```python
STORE_EQUIPMENT = {"mixer": 1, "oven": 2, "cooling_rack": 0}
```

---

## Sample Dataset

The project includes 10 sample recipes in `sample_data.py`. They cover different outcomes:

- Valid recipes that can be approved
- Recipes that fail equipment readiness (missing `cooling_rack`)
- Recipes that need cost review
- A recipe with missing required data (name=None)

By default, the CLI picks one sample recipe randomly and prints the validation output.

---

## Run The CLI

**Pick one sample recipe randomly and show output**:
```bash
python main.py
```

**List all 10 sample datasets**:
```bash
python main.py --list
```

**Run a specific sample by 1-based index**:
```bash
python main.py --index 2
```

---

## Example Output

```json
{
  "recipe_id": "generated-uuid",
  "status": "approved",
  "agents": {
    "completeness": {
      "valid": true,
      "missing": [],
      "issues": []
    },
    "cost_margin": {
      "approved": true,
      "total_cost": 132.5,
      "alternatives": [
        "Reduce high-cost ingredient quantities.",
        "Increase target price or negotiate supplier pricing."
      ]
    },
    "equipment": {
      "ready": true,
      "missing": [],
      "workarounds": []
    }
  },
  "recipe": {
    "name": "Vanilla Muffin",
    "ingredients": [
      { "name": "flour", "quantity": 1.5, "unit_cost": 25 },
      { "name": "vanilla", "cost": 35 },
      { "name": "butter", "quantity": 1, "unit_cost": 60 }
    ],
    "batch_size": 12,
    "equipment": ["mixer", "oven"],
    "target_margin": 30,
    "target_price": 240,
    "status": "approved",
    "total_cost": 132.5
  }
}
```

### Status Values

- `"approved"` - All validations passed
- `"needs_cost_review"` - Completeness OK, but cost exceeds margin
- `"needs_equipment"` - Completeness OK, cost OK, but equipment missing
- `"rejected"` - Recipe is incomplete or has validation issues

---

## Setup

### Requirements

- Python 3.13+
- Hugging Face token for API access

### Install

```bash
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file in the project root or stat6 directory:

```env
HF_TOKEN=your_hugging_face_api_token_here
HF_MODEL=mistralai/Mistral-7B-Instruct-v0.3
HF_TIMEOUT_SECONDS=20
```

Or set environment variables directly:
```bash
export HF_TOKEN=...
export HF_MODEL=mistralai/Mistral-7B-Instruct-v0.3
```

---

## Files

```
stat6/
├── main.py              # CLI entry point, agents, orchestration
├── llm.py               # Hugging Face API integration
├── sample_data.py       # 10 sample recipes for testing
├── requirements.txt     # Python dependencies
└── readme.md            # This file
```

---

## Key Optimizations (Recent Cleanup)

1. **Removed redundant LLM call**: Completeness check is now deterministic local validation (33% fewer LLM calls)
2. **Removed unused `recipes` dictionary**: Was never queried or used
3. **Optimized copy operations**: Changed from `deepcopy` to shallow `.copy()` since recipes aren't modified
4. **Extracted helper function**: `_merge_with_deduplication()` consolidates duplicate logic
5. **Removed unused output fields**: Eliminated `sample_dataset_count` from JSON

These changes reduced code complexity while maintaining full functionality.

---

## Notes

- The CLI is stateless - each validation run is independent
- LLM responses are validated and sanitized for safety
- No data persistence between runs
- Equipment inventory is global and hardcoded (not per-recipe)
