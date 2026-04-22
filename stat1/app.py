from pathlib import Path

from flask import Flask, render_template, request

from analyzer import compare_metrics, extract_metrics, parse_log_text, render_report


app = Flask(__name__)


def analyze_text(text: str) -> dict:
    records, failed_lines = parse_log_text(text)
    metrics = extract_metrics(records, failed_lines)
    return {
        "metrics": metrics,
        "report": render_report(metrics),
        "record_count": len(records),
        "failed_lines": failed_lines[:5],
    }


@app.route("/", methods=["GET", "POST"])
def index():
    analysis = None
    comparison = None
    error_message = None
    source_name = None
    comparison_sources = None

    if request.method == "POST":
        uploaded_file = request.files.get("logfile")
        baseline_file = request.files.get("baseline_log")
        candidate_file = request.files.get("candidate_log")
        sample_requested = request.form.get("use_sample") == "1"
        comparison_requested = request.form.get("compare_mode") == "1"
        comparison_sample_requested = request.form.get("use_comparison_sample") == "1"

        if comparison_requested and comparison_sample_requested:
            baseline_path = Path("sample_baseline.log")
            candidate_path = Path("sample.log")
            baseline_analysis = analyze_text(baseline_path.read_text(encoding="utf-8"))
            candidate_analysis = analyze_text(candidate_path.read_text(encoding="utf-8"))
            comparison = {
                "baseline": baseline_analysis,
                "candidate": candidate_analysis,
                "diff": compare_metrics(
                    baseline_analysis["metrics"],
                    candidate_analysis["metrics"],
                ),
            }
            comparison_sources = {
                "baseline": baseline_path.name,
                "candidate": candidate_path.name,
            }
        elif comparison_requested:
            baseline_text = ""
            candidate_text = ""
            if baseline_file and baseline_file.filename:
                baseline_text = baseline_file.read().decode("utf-8", errors="replace")
            if candidate_file and candidate_file.filename:
                candidate_text = candidate_file.read().decode("utf-8", errors="replace")

            if baseline_text.strip() and candidate_text.strip():
                baseline_analysis = analyze_text(baseline_text)
                candidate_analysis = analyze_text(candidate_text)
                comparison = {
                    "baseline": baseline_analysis,
                    "candidate": candidate_analysis,
                    "diff": compare_metrics(
                        baseline_analysis["metrics"],
                        candidate_analysis["metrics"],
                    ),
                }
                comparison_sources = {
                    "baseline": baseline_file.filename,
                    "candidate": candidate_file.filename,
                }
            else:
                error_message = "Upload both a baseline log and a candidate log to compare them."
        elif uploaded_file and uploaded_file.filename:
            text = uploaded_file.read().decode("utf-8", errors="replace")
            source_name = uploaded_file.filename
            analysis = analyze_text(text)
        elif sample_requested:
            sample_path = Path("sample.log")
            source_name = sample_path.name
            analysis = analyze_text(sample_path.read_text(encoding="utf-8"))
        else:
            error_message = "Upload a log file, or switch to comparison mode with two files."

    return render_template(
        "index.html",
        analysis=analysis,
        comparison=comparison,
        error_message=error_message,
        source_name=source_name,
        comparison_sources=comparison_sources,
    )


if __name__ == "__main__":
    app.run(debug=True)
