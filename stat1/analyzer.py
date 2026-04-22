import argparse
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any


LOG_PATTERN = re.compile(
    r"^(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+"
    r"(?P<level>[A-Z]+)\s+"
    r"\[(?P<service>[^\]]+)\]\s+"
    r"(?P<body>.+)$"
)

KV_PATTERN = re.compile(r'(\w+)=(".*?"|\S+)')
NUMERIC_PATTERN = re.compile(r"^-?\d+(?:\.\d+)?$")


@dataclass
class LogRecord:
    timestamp: str
    level: str
    service: str
    message: str
    fields: dict[str, Any]
    raw: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "level": self.level,
            "service": self.service,
            "message": self.message,
            "fields": self.fields,
            "raw": self.raw,
        }


def coerce_value(value: str) -> Any:
    if value.startswith('"') and value.endswith('"'):
        value = value[1:-1]

    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if NUMERIC_PATTERN.match(value):
        if "." in value:
            return float(value)
        return int(value)
    return value


def split_body(body: str) -> tuple[str, dict[str, Any]]:
    matches = list(KV_PATTERN.finditer(body))
    if not matches:
        return body.strip(), {}

    first_match_start = matches[0].start()
    message = body[:first_match_start].strip()
    fields: dict[str, Any] = {}
    for match in matches:
        key = match.group(1)
        value = coerce_value(match.group(2))
        fields[key] = value

    return message, fields


def parse_log_line(line: str) -> tuple[LogRecord | None, str | None]:
    stripped = line.strip()
    if not stripped:
        return None, None

    match = LOG_PATTERN.match(stripped)
    if not match:
        return None, stripped

    message, fields = split_body(match.group("body"))
    return (
        LogRecord(
            timestamp=match.group("timestamp"),
            level=match.group("level"),
            service=match.group("service"),
            message=message,
            fields=fields,
            raw=stripped,
        ),
        None,
    )


def parse_logs(path: Path) -> tuple[list[LogRecord], list[str]]:
    return parse_log_text(path.read_text(encoding="utf-8"))


def parse_log_text(text: str) -> tuple[list[LogRecord], list[str]]:
    records: list[LogRecord] = []
    failed_lines: list[str] = []

    for line in text.splitlines():
        record, failed = parse_log_line(line)
        if record:
            records.append(record)
        elif failed:
            failed_lines.append(failed)

    return records, failed_lines


def extract_metrics(records: list[LogRecord], failed_lines: list[str]) -> dict[str, Any]:
    levels = Counter(record.level for record in records)
    services = Counter(record.service for record in records)
    message_counts = Counter(record.message for record in records)

    response_times = [
        record.fields["responseTimeMs"]
        for record in records
        if isinstance(record.fields.get("responseTimeMs"), (int, float))
    ]
    db_query_times = [
        record.fields["queryTimeMs"]
        for record in records
        if isinstance(record.fields.get("queryTimeMs"), (int, float))
    ]

    login_failures = [
        record for record in records
        if "login failed" in record.message.lower()
        or record.fields.get("reason") == "INVALID_PASSWORD"
    ]
    exceptions = [
        record for record in records
        if "exception" in record.message.lower() or "exception" in record.fields
    ]
    slow_requests = [
        record
        for record in records
        if isinstance(record.fields.get("responseTimeMs"), (int, float))
        and record.fields["responseTimeMs"] >= 1000
    ]
    high_db_latency = [
        record
        for record in records
        if isinstance(record.fields.get("queryTimeMs"), (int, float))
        and record.fields["queryTimeMs"] >= 500
    ]

    timeline = sorted(records, key=lambda record: record.timestamp)
    duration_seconds = None
    if len(timeline) >= 2:
        start = datetime.strptime(timeline[0].timestamp, "%Y-%m-%d %H:%M:%S")
        end = datetime.strptime(timeline[-1].timestamp, "%Y-%m-%d %H:%M:%S")
        duration_seconds = int((end - start).total_seconds())

    users_with_failed_logins = Counter(
        str(record.fields.get("userId", "UNKNOWN")) for record in login_failures
    )
    failure_reasons = Counter(
        str(record.fields["reason"])
        for record in records
        if record.fields.get("reason")
    )
    error_records = [record for record in records if record.level == "ERROR"]

    metrics = {
        "total_records": len(records),
        "failed_to_parse": len(failed_lines),
        "levels": dict(levels),
        "services": dict(services),
        "top_messages": [
            {"message": message, "count": count}
            for message, count in message_counts.most_common(5)
        ],
        "time_window_seconds": duration_seconds,
        "response_time_ms": summarize_numbers(response_times),
        "db_query_time_ms": summarize_numbers(db_query_times),
        "login_failures": {
            "count": len(login_failures),
            "users": dict(users_with_failed_logins.most_common(5)),
        },
        "failure_reasons": [
            {"reason": reason, "count": count}
            for reason, count in failure_reasons.most_common(5)
        ],
        "exceptions": {
            "count": len(exceptions),
            "by_service": counter_by_service(exceptions),
        },
        "slow_requests": {
            "count": len(slow_requests),
            "threshold_ms": 1000,
            "by_service": counter_by_service(slow_requests),
        },
        "high_db_latency": {
            "count": len(high_db_latency),
            "threshold_ms": 500,
            "by_service": counter_by_service(high_db_latency),
        },
        "issue_signals": build_issue_signals(
            records=records,
            failed_lines=failed_lines,
            login_failures=login_failures,
            exceptions=exceptions,
            slow_requests=slow_requests,
            high_db_latency=high_db_latency,
            levels=levels,
            services=services,
        ),
    }
    metrics["dashboard"] = build_dashboard_summary(metrics, records, error_records)
    return metrics


def summarize_numbers(values: list[int | float]) -> dict[str, float] | None:
    if not values:
        return None

    sorted_values = sorted(float(value) for value in values)
    index_95 = max(0, min(len(sorted_values) - 1, round(0.95 * (len(sorted_values) - 1))))
    return {
        "count": len(sorted_values),
        "avg": round(mean(sorted_values), 2),
        "min": round(sorted_values[0], 2),
        "max": round(sorted_values[-1], 2),
        "p95": round(sorted_values[index_95], 2),
    }


def counter_by_service(records: list[LogRecord]) -> dict[str, int]:
    return dict(Counter(record.service for record in records).most_common())


def build_issue_signals(
    records: list[LogRecord],
    failed_lines: list[str],
    login_failures: list[LogRecord],
    exceptions: list[LogRecord],
    slow_requests: list[LogRecord],
    high_db_latency: list[LogRecord],
    levels: Counter,
    services: Counter,
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []

    if failed_lines:
        issues.append(
            {
                "severity": "medium",
                "title": "Some log lines could not be parsed",
                "detail": f"{len(failed_lines)} lines do not match the expected pattern.",
            }
        )

    if levels.get("ERROR", 0):
        issues.append(
            {
                "severity": "high",
                "title": "Application errors detected",
                "detail": f"{levels['ERROR']} ERROR log(s) observed across {len(counter_by_service(exceptions)) or 1} service(s).",
            }
        )

    if len(login_failures) >= 3:
        top_user, attempts = Counter(
            str(record.fields.get("userId", "UNKNOWN")) for record in login_failures
        ).most_common(1)[0]
        issues.append(
            {
                "severity": "high",
                "title": "Repeated login failures",
                "detail": f"{len(login_failures)} failed login attempts detected; highest volume user is {top_user} with {attempts} failures.",
            }
        )

    if slow_requests:
        busiest_service, count = Counter(
            record.service for record in slow_requests
        ).most_common(1)[0]
        issues.append(
            {
                "severity": "medium",
                "title": "Slow request latency",
                "detail": f"{len(slow_requests)} request(s) exceeded 1000 ms; {busiest_service} accounts for {count}.",
            }
        )

    if high_db_latency:
        issues.append(
            {
                "severity": "medium",
                "title": "Database latency is elevated",
                "detail": f"{len(high_db_latency)} query event(s) exceeded 500 ms.",
            }
        )

    if records:
        noisiest_service, count = services.most_common(1)[0]
        if count >= max(3, round(len(records) * 0.3)):
            issues.append(
                {
                    "severity": "low",
                    "title": "One service dominates the logs",
                    "detail": f"{noisiest_service} produced {count} of {len(records)} parsed events.",
                }
            )

    return issues


def build_dashboard_summary(
    metrics: dict[str, Any],
    records: list[LogRecord],
    error_records: list[LogRecord],
) -> dict[str, Any]:
    total_records = metrics["total_records"]
    error_rate = round((len(error_records) / total_records) * 100, 2) if total_records else 0.0

    top_failing_components = [
        {"service": service, "errors": count}
        for service, count in Counter(record.service for record in error_records).most_common(5)
    ]

    minute_buckets = Counter(record.timestamp[11:16] for record in error_records)
    spike_minute = None
    if minute_buckets:
        minute, count = minute_buckets.most_common(1)[0]
        if count >= 2:
            spike_minute = {
                "time": minute,
                "error_count": count,
                "label": f"Spike in errors at {minute}",
            }

    suspicious_users = Counter(
        str(record.fields.get("userId", "UNKNOWN"))
        for record in records
        if record.message.lower() == "login failed"
    )
    suspicious_activity = None
    if suspicious_users:
        user_id, count = suspicious_users.most_common(1)[0]
        if count >= 2:
            suspicious_activity = {
                "user_id": user_id,
                "attempts": count,
                "label": f"Suspicious activity detected for {user_id}",
            }

    anomalies: list[str] = []
    if spike_minute:
        anomalies.append(spike_minute["label"])
    if suspicious_activity:
        anomalies.append(suspicious_activity["label"])
    if metrics["failed_to_parse"]:
        anomalies.append(f"{metrics['failed_to_parse']} malformed log line(s) detected")

    return {
        "total_logs": total_records,
        "error_rate": error_rate,
        "top_failing_components": top_failing_components,
        "common_failure_reasons": metrics["failure_reasons"],
        "anomalies": anomalies,
        "spike_minute": spike_minute,
        "suspicious_activity": suspicious_activity,
    }


def compare_metrics(baseline: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    baseline_errors = baseline["levels"].get("ERROR", 0)
    candidate_errors = candidate["levels"].get("ERROR", 0)
    baseline_error_rate = baseline["dashboard"]["error_rate"]
    candidate_error_rate = candidate["dashboard"]["error_rate"]

    latency_delta = compare_numeric_summary(
        baseline.get("response_time_ms"),
        candidate.get("response_time_ms"),
        "p95",
    )
    db_latency_delta = compare_numeric_summary(
        baseline.get("db_query_time_ms"),
        candidate.get("db_query_time_ms"),
        "p95",
    )

    baseline_failure_reasons = {
        item["reason"]: item["count"] for item in baseline.get("failure_reasons", [])
    }
    candidate_failure_reasons = {
        item["reason"]: item["count"] for item in candidate.get("failure_reasons", [])
    }

    baseline_service_errors = {
        item["service"]: item["errors"]
        for item in baseline["dashboard"].get("top_failing_components", [])
    }
    candidate_service_errors = {
        item["service"]: item["errors"]
        for item in candidate["dashboard"].get("top_failing_components", [])
    }

    worsened_services = []
    for service in sorted(set(baseline_service_errors) | set(candidate_service_errors)):
        delta = candidate_service_errors.get(service, 0) - baseline_service_errors.get(service, 0)
        if delta > 0:
            worsened_services.append(
                {
                    "service": service,
                    "baseline_errors": baseline_service_errors.get(service, 0),
                    "candidate_errors": candidate_service_errors.get(service, 0),
                    "delta": delta,
                }
            )

    new_failure_reasons = [
        {
            "reason": reason,
            "count": candidate_failure_reasons[reason],
        }
        for reason in sorted(candidate_failure_reasons)
        if reason not in baseline_failure_reasons
    ]
    removed_failure_reasons = [
        {
            "reason": reason,
            "count": baseline_failure_reasons[reason],
        }
        for reason in sorted(baseline_failure_reasons)
        if reason not in candidate_failure_reasons
    ]

    added_services = sorted(set(candidate["services"]) - set(baseline["services"]))
    removed_services = sorted(set(baseline["services"]) - set(candidate["services"]))

    summary = build_comparison_summary(
        baseline=baseline,
        candidate=candidate,
        worsened_services=worsened_services,
        new_failure_reasons=new_failure_reasons,
        latency_delta=latency_delta,
        db_latency_delta=db_latency_delta,
    )

    return {
        "baseline": {
            "total_logs": baseline["dashboard"]["total_logs"],
            "error_rate": baseline_error_rate,
            "error_count": baseline_errors,
            "slow_requests": baseline["slow_requests"]["count"],
            "db_latency_events": baseline["high_db_latency"]["count"],
        },
        "candidate": {
            "total_logs": candidate["dashboard"]["total_logs"],
            "error_rate": candidate_error_rate,
            "error_count": candidate_errors,
            "slow_requests": candidate["slow_requests"]["count"],
            "db_latency_events": candidate["high_db_latency"]["count"],
        },
        "deltas": {
            "error_count": candidate_errors - baseline_errors,
            "error_rate": round(candidate_error_rate - baseline_error_rate, 2),
            "slow_requests": candidate["slow_requests"]["count"] - baseline["slow_requests"]["count"],
            "db_latency_events": candidate["high_db_latency"]["count"] - baseline["high_db_latency"]["count"],
            "response_time_p95_ms": latency_delta,
            "db_query_p95_ms": db_latency_delta,
        },
        "worsened_services": worsened_services,
        "new_failure_reasons": new_failure_reasons,
        "removed_failure_reasons": removed_failure_reasons,
        "added_services": added_services,
        "removed_services": removed_services,
        "summary": summary,
    }


def compare_numeric_summary(
    baseline: dict[str, Any] | None,
    candidate: dict[str, Any] | None,
    field: str,
) -> dict[str, Any] | None:
    if not baseline or not candidate:
        return None
    if field not in baseline or field not in candidate:
        return None
    baseline_value = baseline[field]
    candidate_value = candidate[field]
    return {
        "baseline": baseline_value,
        "candidate": candidate_value,
        "delta": round(candidate_value - baseline_value, 2),
    }


def build_comparison_summary(
    baseline: dict[str, Any],
    candidate: dict[str, Any],
    worsened_services: list[dict[str, Any]],
    new_failure_reasons: list[dict[str, Any]],
    latency_delta: dict[str, Any] | None,
    db_latency_delta: dict[str, Any] | None,
) -> list[str]:
    lines: list[str] = []
    error_rate_delta = round(
        candidate["dashboard"]["error_rate"] - baseline["dashboard"]["error_rate"],
        2,
    )
    if error_rate_delta > 0:
        lines.append(
            f"Error rate increased by {error_rate_delta:.2f} percentage points."
        )
    elif error_rate_delta < 0:
        lines.append(
            f"Error rate improved by {abs(error_rate_delta):.2f} percentage points."
        )
    else:
        lines.append("Error rate is unchanged between both files.")

    if worsened_services:
        worst_service = max(worsened_services, key=lambda item: item["delta"])
        lines.append(
            f"{worst_service['service']} shows the sharpest regression with +{worst_service['delta']} errors."
        )

    if new_failure_reasons:
        lines.append(
            f"New failure reason detected: {new_failure_reasons[0]['reason']}."
        )

    if latency_delta and latency_delta["delta"] > 0:
        lines.append(
            f"API response p95 worsened by {latency_delta['delta']} ms."
        )
    if db_latency_delta and db_latency_delta["delta"] > 0:
        lines.append(
            f"DB query p95 worsened by {db_latency_delta['delta']} ms."
        )

    return lines


def render_report(metrics: dict[str, Any]) -> str:
    lines = [
        "Log Analysis Report",
        "===================",
        f"Parsed records: {metrics['total_records']}",
        f"Failed to parse: {metrics['failed_to_parse']}",
        f"Time window (seconds): {metrics['time_window_seconds']}",
        "",
        "Log levels:",
    ]

    for level, count in sorted(metrics["levels"].items()):
        lines.append(f"- {level}: {count}")

    lines.extend(["", "Top services:"])
    for service, count in sorted(
        metrics["services"].items(), key=lambda item: item[1], reverse=True
    ):
        lines.append(f"- {service}: {count}")

    lines.extend(["", "KPI summary:"])
    lines.append(format_numeric_summary("Response time (ms)", metrics["response_time_ms"]))
    lines.append(format_numeric_summary("DB query time (ms)", metrics["db_query_time_ms"]))
    lines.append(f"- Login failures: {metrics['login_failures']['count']}")
    lines.append(f"- Exceptions: {metrics['exceptions']['count']}")
    lines.append(f"- Slow requests: {metrics['slow_requests']['count']}")
    lines.append(f"- High DB latency events: {metrics['high_db_latency']['count']}")

    lines.extend(["", "Issues:"])
    if metrics["issue_signals"]:
        for issue in metrics["issue_signals"]:
            lines.append(
                f"- [{issue['severity'].upper()}] {issue['title']}: {issue['detail']}"
            )
    else:
        lines.append("- No significant issue signals were detected.")

    return "\n".join(lines)


def format_numeric_summary(label: str, summary: dict[str, Any] | None) -> str:
    if not summary:
        return f"- {label}: no data"
    return (
        f"- {label}: count={summary['count']}, avg={summary['avg']}, "
        f"min={summary['min']}, max={summary['max']}, p95={summary['p95']}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze application logs.")
    parser.add_argument("input", type=Path, help="Path to the input log file")
    parser.add_argument(
        "--json-out",
        type=Path,
        default=Path("structured_logs.json"),
        help="Path for structured JSON output",
    )
    parser.add_argument(
        "--report-out",
        type=Path,
        default=Path("analysis_report.txt"),
        help="Path for the text report output",
    )
    args = parser.parse_args()

    records, failed_lines = parse_logs(args.input)
    metrics = extract_metrics(records, failed_lines)

    structured_output = {
        "records": [record.as_dict() for record in records],
        "failed_lines": failed_lines,
        "metrics": metrics,
    }

    args.json_out.write_text(
        json.dumps(structured_output, indent=2),
        encoding="utf-8",
    )
    args.report_out.write_text(render_report(metrics), encoding="utf-8")

    print(f"Structured JSON written to {args.json_out}")
    print(f"Text report written to {args.report_out}")
    print()
    print(render_report(metrics))


if __name__ == "__main__":
    main()
