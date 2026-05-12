"""
Generates three output CSV files using different invalid status strategies.

Usage:
    python3 scripts/generate_outputs.py <input.csv>
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from health_report import CSVReader, process


def main(input_path):
    output_dir = os.path.dirname(input_path)

    strategies = [
        ('skip',    os.path.join(output_dir, 'output_skip.csv')),
        ('unknown', os.path.join(output_dir, 'output_unknown.csv')),
    ]

    for strategy, output_path in strategies:
        print(f'--- Strategy: {strategy} ---')
        process(CSVReader(input_path), output_path, on_invalid=strategy)
        print(f'Written to {output_path}')
        print()


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(f'Usage: python3 {sys.argv[0]} <input.csv>')
        sys.exit(1)
    main(sys.argv[1])
