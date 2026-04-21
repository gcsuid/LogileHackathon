from pathlib import Path

from flask import Flask, render_template, request

from analyzer import extract_metrics, parse_log_text, render_report


app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def index():
    analysis = None
    error_message = None
    source_name = None

    if request.method == "POST":
        uploaded_file = request.files.get("logfile")
        sample_requested = request.form.get("use_sample") == "1"

        if uploaded_file and uploaded_file.filename:
            text = uploaded_file.read().decode("utf-8", errors="replace")
            source_name = uploaded_file.filename
        elif sample_requested:
            sample_path = Path("sample.log")
            text = sample_path.read_text(encoding="utf-8")
            source_name = sample_path.name
        else:
            text = ""

        if text.strip():
            records, failed_lines = parse_log_text(text)
            metrics = extract_metrics(records, failed_lines)
            analysis = {
                "metrics": metrics,
                "report": render_report(metrics),
                "record_count": len(records),
                "failed_lines": failed_lines[:5],
            }
        else:
            error_message = "Upload a log file or load the sample log."

    return render_template(
        "index.html",
        analysis=analysis,
        error_message=error_message,
        source_name=source_name,
    )


if __name__ == "__main__":
    app.run(debug=True)
