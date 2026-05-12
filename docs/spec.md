# Specification

## Input

- CSV file with fields: `timestamp`, `service_id`, `response_time`, `status`
- `timestamp` is a Unix timestamp
- `service_id` is an integer
- `status` is one of `UP`, `DOWN`, or `UNKNOWN`

## Output

- CSV file with fields: `service_id`, `start_time`, `end_time`, `status`
- Sorted by `service_id` first, then by `start_time`
- `status` is either `UP` or `DOWN`
- `end_time` is `-1` for the last known interval of a service
- Response times are ignored

## UNKNOWN resolution

- `UNKNOWN` followed by `UP` is treated as `UP`
- `UNKNOWN` followed by `DOWN` is treated as `DOWN`
- A trailing `UNKNOWN` with no following ping does not affect any interval

## Intervals

- An interval represents a continuous period during which a service held the same status
- A new interval begins each time the status changes
- The `end_time` of an interval equals the `start_time` of the next interval
