def _join_or_none(items: list[str]) -> str:
    return ", ".join(items) if items else "none"


def build_issue_summary(report: dict) -> dict:
    validation = report.get("validation") or {}
    finance = report.get("finance") or {}
    store = report.get("store") or {}

    if not validation.get("validation_passed", False):
        missing = validation.get("missing_fields", [])
        inconsistencies = validation.get("inconsistencies", [])
        blockers = missing + inconsistencies
        return {
            "status": "Rejected",
            "issue": "Recipe validation failed.",
            "why": _join_or_none(blockers),
            "solution": "Add the missing recipe data and fix invalid quantities, units, or preparation steps.",
        }

    if finance and not finance.get("approved", False):
        margin = finance.get("margin_impact", {})
        return {
            "status": "Rejected",
            "issue": "Recipe cost does not meet the finance threshold.",
            "why": (
                f"Batch cost is INR {report['cost']['total_cost']:.2f}; "
                f"margin is {margin.get('margin_percent', 0):.2f}%."
            ),
            "solution": "Reduce premium ingredient quantities, renegotiate ingredient pricing, or raise the selling price.",
        }

    missing_equipment = store.get("missing_equipment", [])
    if missing_equipment:
        return {
            "status": "Needs Changes",
            "issue": "Store is missing required equipment.",
            "why": f"Unavailable equipment: {_join_or_none(missing_equipment)}.",
            "solution": "Use approved substitutions, move the recipe to a capable store, or add the missing equipment.",
        }

    return {
        "status": "Ready",
        "issue": "No blocking issue.",
        "why": "Validation, finance, and store readiness checks passed.",
        "solution": "No action needed.",
    }


def build_minimal_report(report: dict) -> dict:
    cost = report.get("cost") or {}
    finance = report.get("finance") or {}
    store = report.get("store") or {}

    return {
        "recipe_name": report.get("recipe_name", "Unknown Recipe"),
        "final_decision": report.get("final_decision", "UNKNOWN"),
        "cost": cost.get("total_cost"),
        "cost_per_unit": cost.get("cost_per_unit"),
        "finance_decision": finance.get("decision"),
        "store_readiness": store.get("readiness_score"),
        "issue_summary": build_issue_summary(report),
    }
