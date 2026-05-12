"""
Compares build_intervals and build_intervals_with_groupby on the real input data
to verify both approaches produce identical results.

Usage:
    python3 scripts/compare_approaches.py <input.csv>
"""

import csv
import sys
import os
from itertools import groupby

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from health_report import resolve_unknowns, build_intervals, build_intervals_with_groupby


def main(input_path):
    with open(input_path) as f:
        rows = [
            {
                'timestamp': int(r['timestamp']),
                'service_id': int(r['service_id']),
                'status': r['status'],
            }
            for r in csv.DictReader(f)
        ]

    rows.sort(key=lambda r: (r['service_id'], r['timestamp']))

    result1, result2 = [], []
    for service_id, group in groupby(rows, key=lambda r: r['service_id']):
        pings = resolve_unknowns(list(group))
        result1.extend(build_intervals(pings))
        result2.extend(build_intervals_with_groupby(pings))

    if result1 == result2:
        print(f"Both approaches match. Total intervals: {len(result1)}")
    else:
        print("Mismatch found!")
        for i, (a, b) in enumerate(zip(result1, result2)):
            if a != b:
                print(f"  Row {i}: {a} != {b}")


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(f'Usage: python3 {sys.argv[0]} <input.csv>')
        sys.exit(1)
    main(sys.argv[1])
