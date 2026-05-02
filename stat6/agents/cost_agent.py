from llm import run_llm


def estimate_cost(recipe: dict, ingredient_prices: dict) -> dict:
    total_cost = 0.0
    missing_prices = []
    line_items = []

    for ingredient in recipe.get("ingredients", []):
        name = ingredient["name"]
        quantity = ingredient["quantity"]
        unit = ingredient["unit"]
        price_per_unit = ingredient_prices.get(name)

        if price_per_unit is None:
            missing_prices.append(name)
            continue

        item_cost = quantity * price_per_unit
        total_cost += item_cost
        line_items.append(
            {
                "ingredient": name,
                "quantity": quantity,
                "unit": unit,
                "price_per_unit": price_per_unit,
                "item_cost": round(item_cost, 2),
            }
        )

    yield_count = max(recipe.get("yield", 1), 1)
    cost_per_unit = total_cost / yield_count

    cost_reduction_hints = []
    if "cream" in [item["ingredient"] for item in line_items]:
        cost_reduction_hints.append("Use less cream or replace part with milk.")
    if total_cost > 200:
        cost_reduction_hints.append("Reduce premium ingredient quantities slightly.")
    if not cost_reduction_hints:
        cost_reduction_hints.append("Current cost is reasonable; optimize vendor pricing.")

    prompt = f"""
You are a cost analysis agent for a recipe approval workflow.
Summarize the cost position and suggest simple ways to reduce cost.

Recipe:
{recipe}

Line items:
{line_items}

Total cost: {round(total_cost, 2)}
Cost per unit: {round(cost_per_unit, 2)}
Missing prices: {missing_prices}
"""
    llm_summary = run_llm(prompt)

    return {
        "line_items": line_items,
        "missing_prices": missing_prices,
        "total_cost": round(total_cost, 2),
        "cost_per_unit": round(cost_per_unit, 2),
        "suggestions_to_reduce_cost": cost_reduction_hints,
        "llm_summary": llm_summary,
    }


def apply_simple_cost_reduction(recipe: dict) -> dict:
    adjusted_recipe = {
        **recipe,
        "ingredients": [ingredient.copy() for ingredient in recipe.get("ingredients", [])],
    }

    for ingredient in adjusted_recipe["ingredients"]:
        if ingredient["name"] in {"cream", "cheese"}:
            ingredient["quantity"] = round(ingredient["quantity"] * 0.85, 2)

    return adjusted_recipe
