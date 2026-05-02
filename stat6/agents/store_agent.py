from llm import run_llm


def _pick_substitute(
    equipment_name: str,
    available_equipment: set,
    equipment_catalog: dict,
    substitution_map: dict,
) -> dict | None:
    candidates = substitution_map.get(equipment_name, [])
    valid_candidates = []

    for candidate in candidates:
        if candidate not in available_equipment:
            continue

        candidate_meta = equipment_catalog.get(candidate, {})
        valid_candidates.append(
            {
                "equipment": candidate,
                "display_name": candidate_meta.get("display_name", candidate),
                "daily_operating_cost": candidate_meta.get("daily_operating_cost", float("inf")),
                "capabilities": candidate_meta.get("capabilities", []),
            }
        )

    if not valid_candidates:
        return None

    return min(valid_candidates, key=lambda item: item["daily_operating_cost"])


def assess_store_readiness(
    recipe: dict,
    store_data: dict,
    equipment_catalog: dict,
    substitution_map: dict,
    inventory_data: dict,
) -> dict:
    required_equipment = set(recipe.get("equipment", []))
    declared_equipment = set(store_data.get("equipment", []))
    store_name = store_data.get("store_name", "Unknown Store")
    inventory_snapshot = inventory_data.get(store_name, {})

    available_equipment = {
        equipment_name
        for equipment_name, equipment_state in inventory_snapshot.items()
        if equipment_state.get("available")
    }

    if not available_equipment:
        available_equipment = declared_equipment

    substitutions = []
    unresolved_missing = []

    for equipment_name in sorted(required_equipment):
        if equipment_name in available_equipment:
            continue

        substitute = _pick_substitute(
            equipment_name,
            available_equipment,
            equipment_catalog,
            substitution_map,
        )

        if substitute:
            substitutions.append(
                {
                    "required_equipment": equipment_name,
                    "substitute_equipment": substitute["equipment"],
                    "substitute_display_name": substitute["display_name"],
                    "daily_operating_cost": substitute["daily_operating_cost"],
                    "reason": "primary equipment unavailable; using cheapest compatible available substitute",
                }
            )
            continue

        unresolved_missing.append(equipment_name)

    resolved_count = len(required_equipment) - len(unresolved_missing)
    readiness_score = 100 if not required_equipment else int((resolved_count / len(required_equipment)) * 100)

    prompt = f"""
You are a store readiness agent.
Assess if the store can execute this recipe with current equipment and approved substitutions.

Recipe:
{recipe}

Store:
{store_data}

Inventory snapshot:
{inventory_snapshot}

Resolved substitutions:
{substitutions}

Unresolved missing equipment:
{unresolved_missing}

Readiness score:
{readiness_score}
"""
    llm_summary = run_llm(prompt)

    return {
        "store_name": store_name,
        "readiness_score": readiness_score,
        "missing_equipment": unresolved_missing,
        "substitutions": substitutions,
        "inventory_checked": bool(inventory_snapshot),
        "llm_summary": llm_summary,
    }
