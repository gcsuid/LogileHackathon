import argparse
import copy
import json
import random
import re
import uuid
from typing import Any

from llm import call_hf_inference
from sample_data import SAMPLE_RECIPES


recipes: dict[str, dict[str, Any]] = {}

STORE_EQUIPMENT = {"mixer": 1, "oven": 2, "cooling_rack": 0}
DEFAULT_TARGET_MARGIN = 30.0


def _extract_json(text: str) -> dict[str, Any]:
    if not text:
        return {}

    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        return {}

    try:
        parsed = json.loads(match.group(0))
    except json.JSONDecodeError:
        return {}

    return parsed if isinstance(parsed, dict) else {}


def _ingredient_cost(ingredient: dict[str, Any]) -> float:
    for key in ("total_cost", "cost"):
        value = ingredient.get(key)
        if isinstance(value, int | float):
            return float(value)

    quantity = ingredient.get("quantity", 1)
    unit_cost = ingredient.get("unit_cost", ingredient.get("price", 0))

    if not isinstance(quantity, int | float):
        quantity = 1
    if not isinstance(unit_cost, int | float):
        unit_cost = 0

    return float(quantity) * float(unit_cost)


def completeness_agent(recipe: dict[str, Any]) -> dict[str, Any]:
    required_fields = ["name", "ingredients", "batch_size", "equipment"]
    missing = [field for field in required_fields if not recipe.get(field)]
    issues = []

    if recipe.get("ingredients") and not isinstance(recipe["ingredients"], list):
        issues.append("ingredients must be a list")
    if recipe.get("equipment") and not isinstance(recipe["equipment"], list):
        issues.append("equipment must be a list")
    if recipe.get("batch_size") is not None and recipe["batch_size"] <= 0:
        issues.append("batch_size must be greater than zero")

    prompt = f"""
Validate recipe has name, ingredients, batch_size, equipment.
Return JSON only with keys: valid, missing, issues.

Recipe:
{json.dumps(recipe)}

Detected missing fields:
{json.dumps(missing)}

Detected issues:
{json.dumps(issues)}
"""
    hf_result = _extract_json(call_hf_inference(prompt))
    hf_missing = hf_result.get("missing")
    hf_issues = hf_result.get("issues")
    returned_missing = list(dict.fromkeys(missing + (hf_missing if isinstance(hf_missing, list) else [])))
    returned_issues = list(dict.fromkeys(issues + (hf_issues if isinstance(hf_issues, list) else [])))

    return {
        "valid": not returned_missing and not returned_issues and bool(hf_result.get("valid", True)),
        "missing": returned_missing,
        "issues": returned_issues,
    }


def cost_margin_agent(recipe: dict[str, Any], target_margin: float) -> dict[str, Any]:
    total_cost = round(sum(_ingredient_cost(item) for item in recipe.get("ingredients", [])), 2)
    target_price = float(recipe.get("target_price", total_cost * 2 or 1))
    max_cost_for_margin = target_price * (1 - target_margin / 100)
    approved = total_cost <= max_cost_for_margin

    # 1. Removed probability from the AI prompt
    prompt = f"""
Given total_cost=${total_cost} and target_margin={target_margin}%, suggest 2 alternatives to lower costs or raise margins.
Return JSON only with keys: alternatives.
"""
    hf_result = _extract_json(call_hf_inference(prompt))

    alternatives = hf_result.get("alternatives")
    if not isinstance(alternatives, list):
        alternatives = [
            "Reduce high-cost ingredient quantities.",
            "Increase target price or negotiate supplier pricing.",
        ]

    # 2. Removed probability from the returned dictionary
    return {
        "approved": approved,
        "total_cost": total_cost,
        "alternatives": alternatives[:2],
    }

def equipment_agent(recipe: dict[str, Any]) -> dict[str, Any]:
    required = recipe.get("equipment", [])
    missing = [item for item in required if STORE_EQUIPMENT.get(item, 0) <= 0]

    prompt = f"""
Recipe needs {required}. Store has {STORE_EQUIPMENT}. Is it feasible? Suggest workarounds if missing.
Return JSON only with keys: ready, missing, workarounds.
"""
    hf_result = _extract_json(call_hf_inference(prompt))
    hf_missing = hf_result.get("missing")
    returned_missing = list(dict.fromkeys(missing + (hf_missing if isinstance(hf_missing, list) else [])))

    workarounds = hf_result.get("workarounds")
    if not isinstance(workarounds, list):
        workarounds = [
            "Borrow or rent missing equipment before scheduling production.",
            "Move the production run to a store with available equipment.",
        ] if returned_missing else []

    return {
        "ready": not returned_missing and bool(hf_result.get("ready", True)),
        "missing": returned_missing,
        "workarounds": workarounds,
    }


def _status(completeness: dict[str, Any], cost: dict[str, Any], equipment: dict[str, Any]) -> str:
    if not completeness["valid"]:
        return "rejected"
    if not cost["approved"]:
        return "needs_cost_review"
    if not equipment["ready"]:
        return "needs_equipment"
    return "approved"


def run_recipe_validation(recipe: dict[str, Any]) -> dict[str, Any]:
    recipe_id = str(uuid.uuid4())
    target_margin = float(recipe.get("target_margin", DEFAULT_TARGET_MARGIN))

    completeness = completeness_agent(recipe)
    cost = cost_margin_agent(recipe, target_margin)
    equipment = equipment_agent(recipe)
    status = _status(completeness, cost, equipment)

    stored_recipe = {
        **recipe,
        "status": status,
        "total_cost": cost["total_cost"],
    }
    recipes[recipe_id] = stored_recipe

    return {
        "recipe_id": recipe_id,
        "status": status,
        "agents": {
            "completeness": completeness,
            "cost_margin": cost,
            "equipment": equipment,
        },
        "recipe": stored_recipe,
        "sample_dataset_count": len(SAMPLE_RECIPES),
    }


def pick_sample(index: int | None = None) -> dict[str, Any]:
    if index is None:
        return copy.deepcopy(random.choice(SAMPLE_RECIPES))

    if index < 1 or index > len(SAMPLE_RECIPES):
        raise ValueError(f"Sample index must be between 1 and {len(SAMPLE_RECIPES)}.")

    return copy.deepcopy(SAMPLE_RECIPES[index - 1])


def list_samples() -> None:
    print("Available sample datasets:")
    for index, recipe in enumerate(SAMPLE_RECIPES, start=1):
        print(f"{index}. {recipe.get('name') or '<missing name>'}")


def main() -> None:
    parser = argparse.ArgumentParser(description="CLI recipe validation MVP")
    parser.add_argument("--list", action="store_true", help="List all sample recipe datasets.")
    parser.add_argument("--index", type=int, help="Validate a specific sample by 1-based index.")
    args = parser.parse_args()

    if args.list:
        list_samples()
        return

    selected_recipe = pick_sample(args.index)
    result = run_recipe_validation(selected_recipe)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
