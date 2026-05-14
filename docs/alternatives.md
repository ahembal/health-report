# Alternative Approaches

## UNKNOWN Resolution

### Forward pass — `resolve_unknowns`

Iterates left to right. For each UNKNOWN, scans ahead to find the next known status.

- **Complexity**: O(n²) in the worst case — consecutive UNKNOWNs each trigger a separate scan.
- **Clarity**: The look-ahead intent is explicit and easy to follow.

### Reverse pass — `resolve_unknowns_reversed` (default)

Iterates right to left, carrying the last known status backward.

- **Complexity**: O(n) — single pass, no inner loop.
- **Benchmark result**: ~14% faster than the forward pass on the real dataset (191 ms vs 222 ms).

### Pandas bfill — not implemented (no external dependency)

```python
df['status'] = df['status'].replace('UNKNOWN', None).bfill()
```

`bfill()` (backward fill) propagates the next valid value backward across the column in a single vectorised operation via numpy. No Python-level loops — operates on the entire array at once.

This would significantly outperform both Python implementations on very large datasets. Not included to keep the solution dependency-free, but would be the preferred approach in a production setting with pandas already in the stack.

## Interval Building

### Explicit loop — `build_intervals`

Walks pings one by one, tracking current status and start time explicitly. Clear and straightforward.

### groupby — `build_intervals_with_groupby` (default)

Uses `itertools.groupby` to group consecutive same-status pings, then looks ahead to the next group for `end_time`.

- **Benchmark result**: Marginally faster (~1%) — difference is negligible in practice.
- **Style**: More functional and idiomatic Python.

## Memory — Why we load all data at once

True streaming (line by line) is not possible for this problem because UNKNOWN resolution requires looking ahead. A ping's resolved status depends on what comes after it — so we must buffer at minimum all pings per service before processing.

The current approach loads all rows into memory, which is acceptable for this dataset (236k rows, ~30MB). For significantly larger datasets, a streaming approach would be possible per-service — reading one service's pings at a time — but this would require the input data to be pre-sorted by service_id and timestamp, or stored in a database where per-service queries are cheap.

## Benchmark Results

Run on the full dataset (236,604 pings, 6 services):

| Strategy | Time |
|---|---|
| forward + loop | 221.94 ms |
| forward + groupby | 222.09 ms |
| reversed + loop | 194.11 ms |
| reversed + groupby | 191.81 ms |

**reversed + groupby** is the fastest combination and is used as the default.
