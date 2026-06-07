# CLI Recipe Validation MVP

This project is a command-line MVP for validating retail recipes with three lightweight agents. It uses the Hugging Face hosted inference API only. There are no local models, no database, and no web server; all data is kept in Python dictionaries while the CLI process runs.

## What It Solves

Recipe approval usually needs several checks before a recipe can be sent to production:

- is the recipe complete?
- is the recipe cost acceptable for the target margin?
- does the store have the required equipment?

This CLI picks a recipe dataset, runs the three validation agents, and prints one structured JSON output.

## Implemented Agents

### Agent 1 - Completeness Check

Validates that a recipe has:

- `name`
- `ingredients`
- `batch_size`
- `equipment`

Return shape:

```json
{
  "valid": true,
  "missing": [],
  "issues": []
}
```

### Agent 2 - Cost & Margin Check

Calculates total cost from the ingredient list using a simple sum.

Supported ingredient cost formats:

- `{ "name": "flour", "cost": 20 }`
- `{ "name": "flour", "total_cost": 20 }`
- `{ "name": "flour", "quantity": 2, "unit_cost": 10 }`
- `{ "name": "flour", "quantity": 2, "price": 10 }`

The agent compares total cost against the target margin, then asks Hugging Face:

```text
Given total_cost=$X and target_margin=Y%, predict approval probability and suggest 2 alternatives
```

### Agent 3 - Equipment Check

Checks recipe equipment against this hardcoded store equipment dictionary:

```python
STORE_EQUIPMENT = {"mixer": 1, "oven": 2, "cooling_rack": 0}
```

The agent asks Hugging Face:

```text
Recipe needs {equipment}. Store has {available}. Is it feasible? Suggest workarounds if missing
```

## In-Memory Storage

The CLI keeps data in these module-level dictionaries in `main.py`:

```python
recipes = {}
production_runs = {}
users = {}
```

There is no equipment table. Equipment is intentionally hardcoded as `STORE_EQUIPMENT`.

## Sample Dataset

The project includes 10 sample recipes in `sample_data.py`. They cover different outcomes:

- valid recipes that can be approved
- recipes that fail equipment readiness because `cooling_rack` is unavailable
- recipes that need cost review
- a recipe with missing required data

By default, the CLI picks one sample recipe randomly and prints the validation output.

## Run The CLI

Pick one sample recipe randomly and show output:

```bash
python main.py
```

List all 10 sample datasets:

```bash
python main.py --list
```

Run a specific sample by 1-based index:

```bash
python main.py --index 2
```

## Example Output

```json
{
  "recipe_id": "generated-id",
  "status": "approved",
  "agents": {
    "completeness": {
      "valid": true,
      "missing": [],
      "issues": []
    },
    "cost_margin": {
      "approved": true,
      "probability": 85,
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
  },
  "sample_dataset_count": 10
}
```

## Current Files

```text
stat6/
|-- main.py
|-- llm.py
|-- sample_data.py
|-- requirements.txt
|-- readme.md
|-- agents/
|-- data/
|-- workflow/
`-- reporting.py
```

The CLI entry point is `main.py`.
