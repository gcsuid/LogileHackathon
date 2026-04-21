# Log Analysis Tool

Small Python CLI for hackathon-style log analysis.

## What It Does

- Parses application logs dynamically using the pattern `timestamp level [service] message key=value ...`
- Converts logs into structured JSON
- Extracts KPIs such as level counts, service distribution, latency metrics, login failures, and exceptions
- Generates a concise issue-oriented report

## CLI Run

```powershell
python analyzer.py sample.log
```

Optional outputs:

```powershell
python analyzer.py sample.log --json-out out\structured.json --report-out out\report.txt
```

## Output Files

- `structured_logs.json`: parsed records plus metrics
- `analysis_report.txt`: concise text summary

## Web Interface

```powershell
python app.py
```

Then open `http://127.0.0.1:5000` in your browser, upload a `.log` or `.txt` file, and the dashboard will render:

- Total logs
- Error rate
- Top failing components
- Common failure reasons
- Anomalies and report output

## Sample Input

The repository includes `sample.log` for validation.
