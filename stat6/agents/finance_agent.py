from llm import run_llm


def review_financials(cost_output: dict, max_cost_allowed: float, target_selling_price: float) -> dict:
    total_cost = cost_output["total_cost"]
    margin_value = round(target_selling_price - total_cost, 2)
    margin_percent = round((margin_value / target_selling_price) * 100, 2)

    approved = total_cost <= max_cost_allowed
    reason = (
        "within margin threshold"
        if approved
        else "margin too low"
    )
    decision = "APPROVED" if approved else "REJECTED"

    prompt = f"""
You are a finance approval agent.
Decide whether the recipe should be approved based on cost and margin.

Cost output:
{cost_output}

Max allowed batch cost: {max_cost_allowed}
Target selling price: {target_selling_price}
Margin value: {margin_value}
Margin percent: {margin_percent}
"""
    llm_summary = run_llm(prompt)

    return {
        "decision": decision,
        "approved": approved,
        "reason": reason,
        "margin_impact": {
            "target_selling_price": round(target_selling_price, 2),
            "margin_value": margin_value,
            "margin_percent": margin_percent,
        },
        "llm_summary": llm_summary,
    }
