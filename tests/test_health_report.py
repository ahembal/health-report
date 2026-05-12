import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from health_report import (
    resolve_unknowns,
    resolve_unknowns_reversed,
    build_intervals,
    build_intervals_with_groupby,
    validate_status,
)


class TestResolveUnknowns(unittest.TestCase):
    """Tests for resolve_unknowns — forward pass implementation."""

    def test_unknown_followed_by_up(self):
        pings = [
            {'timestamp': 1, 'status': 'UP'},
            {'timestamp': 2, 'status': 'UNKNOWN'},
            {'timestamp': 3, 'status': 'UP'},
        ]
        result = resolve_unknowns(pings)
        self.assertEqual(result[1]['status'], 'UP')

    def test_unknown_followed_by_down(self):
        pings = [
            {'timestamp': 1, 'status': 'UP'},
            {'timestamp': 2, 'status': 'UNKNOWN'},
            {'timestamp': 3, 'status': 'DOWN'},
        ]
        result = resolve_unknowns(pings)
        self.assertEqual(result[1]['status'], 'DOWN')

    def test_trailing_unknown_is_dropped(self):
        pings = [
            {'timestamp': 1, 'status': 'UP'},
            {'timestamp': 2, 'status': 'UNKNOWN'},
        ]
        result = resolve_unknowns(pings)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['status'], 'UP')

    def test_consecutive_unknowns(self):
        pings = [
            {'timestamp': 1, 'status': 'UP'},
            {'timestamp': 2, 'status': 'UNKNOWN'},
            {'timestamp': 3, 'status': 'UNKNOWN'},
            {'timestamp': 4, 'status': 'DOWN'},
        ]
        result = resolve_unknowns(pings)
        self.assertEqual(result[1]['status'], 'DOWN')
        self.assertEqual(result[2]['status'], 'DOWN')


class TestResolveUnknownsReversed(unittest.TestCase):
    """Tests for resolve_unknowns_reversed — single reverse pass implementation."""

    def test_unknown_followed_by_up(self):
        pings = [
            {'timestamp': 1, 'status': 'UP'},
            {'timestamp': 2, 'status': 'UNKNOWN'},
            {'timestamp': 3, 'status': 'UP'},
        ]
        result = resolve_unknowns_reversed(pings)
        self.assertEqual(result[1]['status'], 'UP')

    def test_unknown_followed_by_down(self):
        pings = [
            {'timestamp': 1, 'status': 'UP'},
            {'timestamp': 2, 'status': 'UNKNOWN'},
            {'timestamp': 3, 'status': 'DOWN'},
        ]
        result = resolve_unknowns_reversed(pings)
        self.assertEqual(result[1]['status'], 'DOWN')

    def test_trailing_unknown_is_dropped(self):
        pings = [
            {'timestamp': 1, 'status': 'UP'},
            {'timestamp': 2, 'status': 'UNKNOWN'},
        ]
        result = resolve_unknowns_reversed(pings)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['status'], 'UP')


class TestBuildIntervals(unittest.TestCase):
    """Tests for build_intervals — explicit loop implementation."""

    def test_last_interval_has_minus_one_end_time(self):
        pings = [
            {'timestamp': 1, 'status': 'UP'},
            {'timestamp': 2, 'status': 'UP'},
        ]
        result = build_intervals(pings)
        self.assertEqual(result[-1]['end_time'], -1)

    def test_consecutive_same_status_collapsed(self):
        pings = [
            {'timestamp': 1, 'status': 'UP'},
            {'timestamp': 2, 'status': 'UP'},
            {'timestamp': 3, 'status': 'UP'},
        ]
        result = build_intervals(pings)
        self.assertEqual(len(result), 1)

    def test_end_time_equals_next_start_time(self):
        pings = [
            {'timestamp': 1, 'status': 'UP'},
            {'timestamp': 2, 'status': 'DOWN'},
        ]
        result = build_intervals(pings)
        self.assertEqual(result[0]['end_time'], result[1]['start_time'])

    def test_status_change_creates_new_interval(self):
        pings = [
            {'timestamp': 1, 'status': 'UP'},
            {'timestamp': 2, 'status': 'DOWN'},
            {'timestamp': 3, 'status': 'UP'},
        ]
        result = build_intervals(pings)
        self.assertEqual(len(result), 3)


class TestBuildIntervalsWithGroupby(unittest.TestCase):
    """Tests for build_intervals_with_groupby — itertools.groupby implementation."""

    def test_last_interval_has_minus_one_end_time(self):
        pings = [
            {'timestamp': 1, 'status': 'UP'},
            {'timestamp': 2, 'status': 'UP'},
        ]
        result = build_intervals_with_groupby(pings)
        self.assertEqual(result[-1]['end_time'], -1)

    def test_consecutive_same_status_collapsed(self):
        pings = [
            {'timestamp': 1, 'status': 'UP'},
            {'timestamp': 2, 'status': 'UP'},
            {'timestamp': 3, 'status': 'UP'},
        ]
        result = build_intervals_with_groupby(pings)
        self.assertEqual(len(result), 1)

    def test_end_time_equals_next_start_time(self):
        pings = [
            {'timestamp': 1, 'status': 'UP'},
            {'timestamp': 2, 'status': 'DOWN'},
        ]
        result = build_intervals_with_groupby(pings)
        self.assertEqual(result[0]['end_time'], result[1]['start_time'])

    def test_status_change_creates_new_interval(self):
        pings = [
            {'timestamp': 1, 'status': 'UP'},
            {'timestamp': 2, 'status': 'DOWN'},
            {'timestamp': 3, 'status': 'UP'},
        ]
        result = build_intervals_with_groupby(pings)
        self.assertEqual(len(result), 3)


class TestValidateStatus(unittest.TestCase):
    """Tests for validate_status — invalid status handling strategies."""

    def test_valid_status_returned_unchanged(self):
        row = {'timestamp': 1, 'service_id': 1, 'status': 'UP'}
        self.assertEqual(validate_status(row, 'skip'), row)

    def test_invalid_status_skip_returns_none(self):
        row = {'timestamp': 1, 'service_id': 1, 'status': '3'}
        result = validate_status(row, 'skip')
        self.assertIsNone(result)

    def test_invalid_status_unknown_returns_unknown(self):
        row = {'timestamp': 1, 'service_id': 1, 'status': '3'}
        result = validate_status(row, 'unknown')
        self.assertEqual(result['status'], 'UNKNOWN')


class TestSpecSample(unittest.TestCase):
    """End-to-end test using the exact sample from the task specification."""

    def test_spec_sample(self):
        pings = [
            {'timestamp': 1766478924, 'status': 'UP'},
            {'timestamp': 1767131604, 'status': 'UP'},
            {'timestamp': 1767340434, 'status': 'UNKNOWN'},
            {'timestamp': 1768280666, 'status': 'UP'},
        ]
        resolved = resolve_unknowns(pings)
        intervals = build_intervals(resolved)
        self.assertEqual(len(intervals), 1)
        self.assertEqual(intervals[0]['start_time'], 1766478924)
        self.assertEqual(intervals[0]['end_time'], -1)
        self.assertEqual(intervals[0]['status'], 'UP')


if __name__ == '__main__':
    unittest.main()
