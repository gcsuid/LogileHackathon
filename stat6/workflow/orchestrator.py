from agents.cost_agent import apply_simple_cost_reduction, estimate_cost
from agents.finance_agent import review_financials
from agents.store_agent import assess_store_readiness
from agents.validation_agent import validate_recipe
from data.dummy_data import (
    INGREDIENT_PRICES,
    MAX_BATCH_COST_ALLOWED,
    STORE_EQUIPMENT,
    TARGET_SELLING_PRICE,
)


def _final_decision(validation: dict, finance: dict | None, store: dict | None) -> str:
    if not validation["validation_passed"]:
        return "REJECTED"

    if finance and not finance["approved"]:
        return "REJECTED"

    if store and store["missing_equipment"]:
        return "NEEDS CHANGES"

    return "READY"


def run_pipeline(recipe: dict) -> dict:
    validation_output = validate_recipe(recipe)
    result = {
        "recipe_name": recipe.get("name", "Unknown Recipe"),
        "validation": validation_output,
        "cost": None,
        "finance": None,
        "store": None,
        "final_decision": "REJECTED",
    }

    if not validation_output["validation_passed"]:
        result["final_decision"] = "REJECTED"
        return result

    cost_output = estimate_cost(recipe, INGREDIENT_PRICES)
    finance_output = review_financials(
        cost_output,
        MAX_BATCH_COST_ALLOWED,
        TARGET_SELLING_PRICE,
    )

    retry_used = False
    if not finance_output["approved"]:
        retry_recipe = apply_simple_cost_reduction(recipe)
        retry_cost_output = estimate_cost(retry_recipe, INGREDIENT_PRICES)
        retry_finance_output = review_financials(
            retry_cost_output,
            MAX_BATCH_COST_ALLOWED,
            TARGET_SELLING_PRICE,
        )

        if retry_finance_output["approved"] or retry_cost_output["total_cost"] < cost_output["total_cost"]:
            cost_output = retry_cost_output
            finance_output = retry_finance_output
            retry_used = True

    store_output = assess_store_readiness(recipe, STORE_EQUIPMENT)

    result["cost"] = cost_output
    result["finance"] = finance_output
    result["store"] = store_output
    result["retry_used"] = retry_used
    result["final_decision"] = _final_decision(
        validation_output,
        finance_output,
        store_output,
    )

    if result["final_decision"] == "REJECTED" and validation_output["validation_passed"]:
        if finance_output["approved"] and store_output["missing_equipment"]:
            result["final_decision"] = "NEEDS CHANGES"

    return result
