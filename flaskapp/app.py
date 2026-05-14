import csv
import sys
import json
import logging
import time
from datetime import datetime, timezone
from flask import Flask, render_template


class JSONFormatter(logging.Formatter):
    """Formats log records as JSON for machine-readable structured logging."""

    def format(self, record):
        return json.dumps({
            'timestamp': int(time.time()),
            'level': record.levelname,
            'message': record.getMessage(),
        })


handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logging.basicConfig(level=logging.INFO, handlers=[handler])
logger = logging.getLogger(__name__)

app = Flask(__name__)


def fmt(ts):
    """Converts a Unix timestamp to a human-readable UTC datetime string."""
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')


def duration(seconds):
    """Converts a duration in seconds to a human-readable string like '2d 3h 4m 5s'."""
    d, r = divmod(int(seconds), 86400)
    h, r = divmod(r, 3600)
    m, s = divmod(r, 60)
    parts = []
    if d:
        parts.append(f'{d}d')
    if h:
        parts.append(f'{h}h')
    if m:
        parts.append(f'{m}m')
    parts.append(f'{s}s')
    return ' '.join(parts)


def load_intervals(path):
    """Reads the output CSV and returns intervals grouped by service_id."""
    services = {}
    with open(path, newline='') as f:
        for row in csv.DictReader(f):
            sid = int(row['service_id'])
            if sid not in services:
                services[sid] = []
            services[sid].append({
                'start_time': int(row['start_time']),
                'end_time': int(row['end_time']),
                'status': row['status'],
            })
    logger.info('Loaded %d services from %s', len(services), path)
    return services


def compute_segments(services):
    """Converts intervals into proportional segments for rendering on a timeline.

    Each segment carries its position (left %), width (%), status, formatted times, and duration.
    Also computes UP% per service.
    """
    all_starts = [i['start_time'] for s in services.values() for i in s]
    all_ends = [i['end_time'] for s in services.values() for i in s if i['end_time'] != -1]
    t_min = min(all_starts)
    t_max = max(all_ends) if all_ends else max(all_starts)
    total = t_max - t_min

    result = {}
    for sid, intervals in sorted(services.items()):
        segments = []
        up_time = 0
        total_time = 0
        for interval in intervals:
            start = interval['start_time']
            end = interval['end_time'] if interval['end_time'] != -1 else t_max
            unknown_end = interval['end_time'] == -1
            span = end - start
            total_time += span
            if interval['status'] == 'UP':
                up_time += span
            segments.append({
                'left': (start - t_min) / total * 100,
                'width': (end - start) / total * 100,
                'status': interval['status'],
                'start_fmt': fmt(start),
                'end_fmt': 'unknown' if unknown_end else fmt(end),
                'duration': duration(span),
            })
        up_pct = round(up_time / total_time * 100, 1) if total_time else 0
        result[sid] = {'segments': segments, 'up_pct': up_pct}

    return result


@app.route('/')
def index():
    """Renders the health timeline page."""
    services = load_intervals(app.config['OUTPUT_CSV'])
    segments = compute_segments(services)
    return render_template('index.html', segments=segments)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(f'Usage: python3 {sys.argv[0]} <output.csv>')
        sys.exit(1)
    app.config['OUTPUT_CSV'] = sys.argv[1]
    app.run(debug=True, use_reloader=False, port=5001)
