# How It Works

## Overview

The program reads a CSV file of health check pings, resolves ambiguous `UNKNOWN` statuses, and outputs the time intervals during which each service was `UP` or `DOWN`.

## Step 1 — Load and sort

All rows are read into memory and sorted by `service_id` first, then by `timestamp`. This ensures that pings for each service are processed in chronological order.

## Step 2 — Resolve UNKNOWNs

An `UNKNOWN` ping does not represent an independent state. It is resolved by looking at what comes after it:

- `UNKNOWN` followed by `UP` → treated as `UP`
- `UNKNOWN` followed by `DOWN` → treated as `DOWN`

Each `UNKNOWN` ping inherits the status of the next non-`UNKNOWN` ping. If an `UNKNOWN` has nothing after it (i.e. it is the last ping for a service), it is dropped — it does not create or close any interval.

Two implementations are provided and selectable via `--resolve`:

- **`forward`** (`resolve_unknowns`) — forward pass: iterates left to right, each UNKNOWN looks ahead for the next known status.
- **`reversed`** (`resolve_unknowns_reversed`) — single reverse pass: iterates right to left, carrying the last known status backward. Simpler and more efficient.

## Step 3 — Build intervals

After resolution, pings are walked chronologically. Each time the status changes, a new interval is recorded:

- `start_time` is the timestamp of the first ping in that status period.
- `end_time` is the timestamp of the ping that caused the status change (i.e. the start of the next interval).
- The last interval always gets `end_time = -1`, meaning the service was still in that state at the time of the last recorded ping.

Two implementations are provided and selectable via `--interval`:

- **`loop`** (`build_intervals`) — walks pings one by one, tracking the current status and start time explicitly.
- **`groupby`** (`build_intervals_with_groupby`) — uses `itertools.groupby` to group consecutive same-status pings, then looks ahead to the next group for `end_time`.

## Step 4 — Write output

The resulting intervals are written to a CSV file, sorted by `service_id` then `start_time`.

## Example

Given these pings for service 1 (already sorted by timestamp):

| timestamp | status |
|---|---|
| 1767400524 | UP |
| 1767558032 | DOWN |
| 1767951572 | UP |
| 1768184811 | UP |
| 1768760587 | UP |
| 1768789071 | UP |

The output intervals are:

| start_time | end_time | status |
|---|---|---|
| 1767400524 | 1767558032 | UP |
| 1767558032 | 1767951572 | DOWN |
| 1767951572 | -1 | UP |

Consecutive pings with the same status are collapsed into a single interval.
