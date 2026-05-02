from llm import run_llm


def validate_recipe(recipe: dict) -> dict:
    required_fields = ["name", "ingredients", "steps", "equipment", "yield"]
    missing_fields = [field for field in required_fields if not recipe.get(field)]

    inconsistencies = []
    ingredients = recipe.get("ingredients", [])

    if not ingredients:
        inconsistencies.append("Recipe has no ingredients.")

    for ingredient in ingredients:
        if not ingredient.get("name"):
            inconsistencies.append("An ingredient is missing a name.")
        if ingredient.get("quantity", 0) <= 0:
            inconsistencies.append(
                f"Ingredient '{ingredient.get('name', 'unknown')}' has invalid quantity."
            )
        if not ingredient.get("unit"):
            inconsistencies.append(
                f"Ingredient '{ingredient.get('name', 'unknown')}' is missing a unit."
            )

    if len(recipe.get("steps", [])) < 2:
        inconsistencies.append("Recipe should have at least two preparation steps.")

    prompt = f"""
You are a recipe validation agent for a retail workflow.
Review the recipe below and provide a short validation summary.

Recipe:
{recipe}

Missing fields:
{missing_fields}

Detected inconsistencies:
{inconsistencies}
"""
    llm_summary = run_llm(prompt)

    return {
        "missing_fields": missing_fields,
        "inconsistencies": inconsistencies,
        "validation_passed": not missing_fields and not inconsistencies,
        "llm_summary": llm_summary,
    }
