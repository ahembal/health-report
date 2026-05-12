# Health Report

Processes health check ping data and produces time intervals during which services were UP or DOWN.

## Requirements

Python 3.6 or higher. No external dependencies.

## Usage

```bash
python3 health_report.py <input.csv> <output.csv>
```

**Optional arguments:**

| Argument | Options | Default | Description |
|---|---|---|---|
| `--on-invalid` | `skip`, `unknown` | `skip` | How to handle invalid statuses |
| `--resolve` | `forward`, `reversed` | `reversed` | UNKNOWN resolution strategy |
| `--interval` | `loop`, `groupby` | `groupby` | Interval building strategy |

**Example:**

```bash
python3 health_report.py data/input.csv data/output.csv --on-invalid unknown --resolve forward
```

## Input format

CSV file with the following fields:

| Field | Description |
|---|---|
| `timestamp` | Unix timestamp of the ping |
| `service_id` | Integer ID of the service |
| `response_time` | Response time in milliseconds (ignored in output) |
| `status` | `UP`, `DOWN`, or `UNKNOWN` |

## Output format

CSV file sorted by `service_id` then `start_time`:

| Field | Description |
|---|---|
| `service_id` | Integer ID of the service |
| `start_time` | Unix timestamp when this status period began |
| `end_time` | Unix timestamp when this status period ended, or `-1` if it is the last known state |
| `status` | `UP` or `DOWN` |

## Running the tests

```bash
python3 -m unittest discover -s tests
```
