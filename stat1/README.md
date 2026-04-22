# LogScope

LogScope is a Python + Flask log analysis dashboard built for hackathon-style incident analysis. It parses semi-structured application logs, converts them into structured records, extracts KPIs, and presents both single-file analysis and baseline-vs-candidate comparison in a browser UI.

## Current Features

- Dynamic log parsing using the format `timestamp level [service] message key=value ...`
- Structured extraction of:
  - timestamp
  - log level
  - service/component
  - message
  - key-value fields
- KPI generation for:
  - total logs
  - error rate
  - top failing components
  - failure reasons
  - slow requests
  - DB latency
  - repeated login failures
  - malformed log lines
- Dashboard output for single-file analysis
- Comparison mode for:
  - baseline vs candidate logs
  - error-rate delta
  - error-count delta
  - latency regression
  - worsened services
  - new failure reasons
  - service footprint changes

## Project Files

- [analyzer.py](/abs/path/C:/Users/KIIT/Desktop/personal_project/logileHackathon/stat1/analyzer.py): parsing, metrics, dashboard summaries, comparison logic
- [app.py](/abs/path/C:/Users/KIIT/Desktop/personal_project/logileHackathon/stat1/app.py): Flask app and upload flow
- [templates/index.html](/abs/path/C:/Users/KIIT/Desktop/personal_project/logileHackathon/stat1/templates/index.html): dashboard UI
- [sample.log](/abs/path/C:/Users/KIIT/Desktop/personal_project/logileHackathon/stat1/sample.log): candidate/demo log
- [sample_baseline.log](/abs/path/C:/Users/KIIT/Desktop/personal_project/logileHackathon/stat1/sample_baseline.log): baseline/demo log for comparison mode
- [hackathon_logs - Challenge 1.txt](/abs/path/C:/Users/KIIT/Desktop/personal_project/logileHackathon/stat1/hackathon_logs%20-%20Challenge%201.txt): larger hackathon log file you added for testing
- [next.md](/abs/path/C:/Users/KIIT/Desktop/personal_project/logileHackathon/stat1/next.md): planned next-step features

## Requirements

- Python 3.13+
- Flask

Flask is already available in the current environment.

## Run the Web App

```powershell
python app.py
```

Then open:

```text
http://127.0.0.1:5000
```

## Dashboard Modes

### 1. Single-File Analysis

Use this when you want to inspect one log file and generate a dashboard with:

- total logs
- error rate
- top failing components
- common failure reasons
- anomalies
- detailed report

In the UI:

- upload one `.log` or `.txt` file in the `Single-file analysis` section
- click `Analyze File`
- or click `Load Sample`

### 2. Comparison Mode

Use this when you want to compare one log file against another.

Recommended meaning:

- `Baseline log`: older / stable / before deploy log
- `Candidate log`: newer / changed / after deploy log

The comparison dashboard shows:

- what changed summary
- error-rate delta
- error-count delta
- response-time p95 delta
- DB query p95 delta
- worsened services
- new failure reasons
- added or removed services

In the UI:

- upload a file in `Baseline log`
- upload a file in `Candidate log`
- click `Compare Files`

For a demo:

- click `Load Comparison Sample`

## Run the CLI

You can still run the analyzer directly:

```powershell
python analyzer.py sample.log
```

Optional custom outputs:

```powershell
python analyzer.py sample.log --json-out out\structured.json --report-out out\report.txt
```

## Generated Outputs

- `structured_logs.json`: parsed records plus computed metrics
- `analysis_report.txt`: text summary report

## Suggested Demo Flow

1. Start the Flask app with `python app.py`
2. Show single-file analysis using the hackathon log file
3. Switch to comparison mode
4. Compare `sample_baseline.log` with `sample.log`
5. Walk through the regression summary and “What Changed” panel

## Notes

- The parser is designed for semi-structured application logs that follow the timestamp / level / service / message / key-value pattern.
- Malformed lines are tracked and reported instead of crashing the analysis.
- Comparison mode currently compares derived metrics, not raw line-by-line diffs.
