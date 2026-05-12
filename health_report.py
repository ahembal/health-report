import argparse
import csv
from itertools import groupby

VALID_STATUSES = {'UP', 'DOWN', 'UNKNOWN'}


def validate_status(row, on_invalid):
    """Returns the row with a valid status, or None if it should be skipped.

    on_invalid='skip'    — skip the row and print a warning
    on_invalid='unknown' — treat the invalid status as UNKNOWN
    """
    if row['status'] in VALID_STATUSES:
        return row
    if on_invalid == 'skip':
        print(f"Warning: skipping row with invalid status '{row['status']}' "
              f"(service_id={row['service_id']}, timestamp={row['timestamp']})")
        return None
    if on_invalid == 'unknown':
        print(f"Warning: treating invalid status '{row['status']}' as UNKNOWN "
              f"(service_id={row['service_id']}, timestamp={row['timestamp']})")
        return {**row, 'status': 'UNKNOWN'}
    raise ValueError(f"Invalid status '{row['status']}' at timestamp {row['timestamp']}")


class CSVReader:
    """Reads ping data from a CSV file."""

    def __init__(self, path):
        self.path = path

    def read(self):
        """Returns a list of ping dicts with timestamp, service_id, and status."""
        with open(self.path, newline='') as f:
            return [
                {
                    'timestamp': int(row['timestamp']),
                    'service_id': int(row['service_id']),
                    'status': row['status'],
                }
                for row in csv.DictReader(f)
            ]


class DBReader:
    """Reads ping data from a relational database via a DB-API 2.0 connection."""

    def __init__(self, connection):
        self.connection = connection

    def read(self):
        """Returns a list of ping dicts with timestamp, service_id, and status."""
        cursor = self.connection.cursor()
        cursor.execute("SELECT timestamp, service_id, status FROM pings")
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]


def resolve_unknowns(pings):
    """Resolves UNKNOWN statuses by inheriting the next known status. Trailing UNKNOWNs are dropped."""
    statuses = [p['status'] for p in pings]
    n = len(statuses)

    # Each UNKNOWN inherits the next known status
    for i in range(n):
        if statuses[i] == 'UNKNOWN':
            for j in range(i + 1, n):
                if statuses[j] != 'UNKNOWN':
                    statuses[i] = statuses[j]
                    break

    # Trailing UNKNOWNs (nothing after them) are dropped
    return [
        {**ping, 'status': status}
        for ping, status in zip(pings, statuses)
        if status != 'UNKNOWN'
    ]


def resolve_unknowns_reversed(pings):
    """Resolves UNKNOWN statuses by inheriting the next known status. Trailing UNKNOWNs are dropped."""
    updated_pings = []
    known_status = None
    for ping in reversed(pings):
        if ping['status'] != 'UNKNOWN':
            known_status = ping['status']
        if known_status is not None:
            updated_pings.append({**ping, 'status': known_status})
    return list(reversed(updated_pings))


def build_intervals(pings):
    """Converts a chronologically sorted list of pings into status intervals."""
    intervals = []
    if not pings:
        return intervals

    current_status = pings[0]['status']
    current_start = pings[0]['timestamp']

    for ping in pings[1:]:
        if ping['status'] != current_status:
            intervals.append({
                'start_time': current_start,
                'end_time': ping['timestamp'],
                'status': current_status,
            })
            current_status = ping['status']
            current_start = ping['timestamp']

    intervals.append({
        'start_time': current_start,
        'end_time': -1,
        'status': current_status,
    })

    return intervals


def build_intervals_with_groupby(pings):
    """Alternative implementation of build_intervals using itertools.groupby.
    groupby gives us consecutive groups of pings with the same status,
    so we can directly build intervals from these groups."""
    intervals = [(status, list(g)) for status, g in groupby(pings, key=lambda p: p['status'])]
    result = []
    for i, (status, group_pings) in enumerate(intervals):
        next_interval = intervals[i + 1] if i + 1 < len(intervals) else None
        end_time = next_interval[1][0]['timestamp'] if next_interval else -1
        result.append({
            'start_time': group_pings[0]['timestamp'],
            'end_time': end_time,
            'status': status,
        })
    return result


def process(reader, output_path, on_invalid='skip', resolve_strategy='reversed', interval_strategy='groupby'):
    """Reads pings via the injected reader, computes intervals, and writes them to a CSV file.

    The reader can be any object with a read() method — CSVReader, DBReader, or any other source.
    This is dependency injection: the data source is passed in rather than hardcoded.

    resolve_strategy: 'forward' uses resolve_unknowns, 'reversed' uses resolve_unknowns_reversed
    interval_strategy: 'loop' uses build_intervals, 'groupby' uses build_intervals_with_groupby
    """
    resolve_fn = resolve_unknowns_reversed if resolve_strategy == 'reversed' else resolve_unknowns
    interval_fn = build_intervals_with_groupby if interval_strategy == 'groupby' else build_intervals

    rows = reader.read()

    rows = [r for r in (validate_status(row, on_invalid) for row in rows) if r is not None]
    rows.sort(key=lambda r: (r['service_id'], r['timestamp']))

    output_rows = []
    for service_id, service_group in groupby(rows, key=lambda r: r['service_id']):
        pings = resolve_fn(list(service_group))
        for interval in interval_fn(pings):
            output_rows.append({
                'service_id': service_id,
                'start_time': interval['start_time'],
                'end_time': interval['end_time'],
                'status': interval['status'],
            })

    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['service_id', 'start_time', 'end_time', 'status'])
        writer.writeheader()
        writer.writerows(output_rows)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process health check pings into status intervals.')
    parser.add_argument('input',   help='Input CSV file')
    parser.add_argument('output',  help='Output CSV file')
    parser.add_argument('--on-invalid',  choices=['skip', 'unknown'], default='skip',     help='How to handle invalid statuses (default: skip)')
    parser.add_argument('--resolve',     choices=['forward', 'reversed'], default='reversed', help='UNKNOWN resolution strategy (default: reversed)')
    parser.add_argument('--interval',    choices=['loop', 'groupby'], default='groupby',  help='Interval building strategy (default: groupby)')

    args = parser.parse_args()
    process(CSVReader(args.input), args.output, on_invalid=args.on_invalid, resolve_strategy=args.resolve, interval_strategy=args.interval)
