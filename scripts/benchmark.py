"""
Benchmarks all combinations of UNKNOWN resolution and interval building strategies.

Compares:
  - resolve_unknowns (forward pass, O(n²) worst case) vs
    resolve_unknowns_reversed (single reverse pass, O(n))

  - build_intervals (explicit loop) vs
    build_intervals_with_groupby (itertools.groupby)

Usage:
    python3 scripts/benchmark.py <input.csv>
"""

import csv
import sys
import os
import time
from itertools import groupby

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from health_report import (
    resolve_unknowns,
    resolve_unknowns_reversed,
    build_intervals,
    build_intervals_with_groupby,
    VALID_STATUSES,
)


def load(path):
    with open(path, newline='') as f:
        rows = [
            {
                'timestamp': int(row['timestamp']),
                'service_id': int(row['service_id']),
                'status': row['status'],
            }
            for row in csv.DictReader(f)
            if row['status'] in VALID_STATUSES
        ]
    rows.sort(key=lambda r: (r['service_id'], r['timestamp']))
    return rows


def get_service_groups(rows):
    return [list(group) for _, group in groupby(rows, key=lambda r: r['service_id'])]


def benchmark(resolve_fn, interval_fn, groups, runs=10):
    start = time.perf_counter()
    for _ in range(runs):
        for pings in groups:
            resolved = resolve_fn(pings)
            interval_fn(resolved)
    return (time.perf_counter() - start) / runs


def main(input_path):
    rows = load(input_path)
    groups = get_service_groups(rows)

    print(f'Services: {len(groups)}, Total pings: {sum(len(g) for g in groups)}')
    print()

    combinations = [
        ('forward  + loop   ', resolve_unknowns,          build_intervals),
        ('forward  + groupby', resolve_unknowns,          build_intervals_with_groupby),
        ('reversed + loop   ', resolve_unknowns_reversed, build_intervals),
        ('reversed + groupby', resolve_unknowns_reversed, build_intervals_with_groupby),
    ]

    results = []
    for label, resolve_fn, interval_fn in combinations:
        t = benchmark(resolve_fn, interval_fn, groups)
        results.append((label, t))
        print(f'{label}: {t * 1000:.2f} ms')

    fastest = min(results, key=lambda x: x[1])
    slowest = max(results, key=lambda x: x[1])
    print()
    print(f'Fastest: {fastest[0].strip()} ({fastest[1] * 1000:.2f} ms)')
    print(f'Slowest: {slowest[0].strip()} ({slowest[1] * 1000:.2f} ms)')
    ratio = slowest[1] / fastest[1]
    print(f'Ratio: {ratio:.2f}x')
    print()
    print('Note: a pandas bfill() approach would outperform all of the above')
    print('on large datasets by replacing Python loops with numpy array operations.')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(f'Usage: python3 {sys.argv[0]} <input.csv>')
        sys.exit(1)
    main(sys.argv[1])
