from pprint import pprint

from data.dummy_data import SAMPLE_RECIPE
from workflow.orchestrator import run_pipeline


def print_report(report: dict) -> None:
    validation = report["validation"]
    cost = report.get("cost", {})
    finance = report.get("finance", {})
    store = report.get("store", {})

    print("=== FINAL REPORT ===")
    print(f"Recipe: {report['recipe_name']}")
    print(f"Validation: {'PASS' if validation['validation_passed'] else 'FAIL'}")

    if cost:
        print(f"Cost: INR {cost['total_cost']:.2f} per batch")
        print(f"Cost Per Unit: INR {cost['cost_per_unit']:.2f}")

    if finance:
        print(
            f"Finance: {finance['decision']} "
            f"({finance['reason']})"
        )

    if store:
        print(
            f"Store Readiness: {store['readiness_score']}% "
            f"(missing: {', '.join(store['missing_equipment']) or 'none'})"
        )

    print(f"Final Decision: {report['final_decision']}")
    print("\n=== STRUCTURED OUTPUT ===")
    pprint(report)


def main() -> None:
    report = run_pipeline(SAMPLE_RECIPE)
    print_report(report)


if __name__ == "__main__":
    main()
