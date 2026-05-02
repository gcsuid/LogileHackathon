from llm import run_llm


def assess_store_readiness(recipe: dict, store_data: dict) -> dict:
    required_equipment = set(recipe.get("equipment", []))
    available_equipment = set(store_data.get("equipment", []))
    missing_equipment = sorted(required_equipment - available_equipment)

    if required_equipment:
        readiness_score = int(
            ((len(required_equipment) - len(missing_equipment)) / len(required_equipment)) * 100
        )
    else:
        readiness_score = 100

    prompt = f"""
You are a store readiness agent.
Assess if the store can execute this recipe with current equipment.

Recipe:
{recipe}

Store:
{store_data}

Missing equipment:
{missing_equipment}

Readiness score:
{readiness_score}
"""
    llm_summary = run_llm(prompt)

    return {
        "store_name": store_data.get("store_name", "Unknown Store"),
        "readiness_score": readiness_score,
        "missing_equipment": missing_equipment,
        "llm_summary": llm_summary,
    }
