# Streaming Module

The streaming module serves lightweight synthetic event data over HTTP using only the Python standard library.

## Start

Run the server from the repo root:

```bash
python3 streaming_generator.py
```

Default address:

```text
http://127.0.0.1:8882
```

Optional environment overrides:

```bash
STREAMING_HOST=127.0.0.1 STREAMING_PORT=8882 STREAMING_RATE=1 python3 streaming_generator.py
```

Available environment variables:

- `STREAMING_HOST`: bind host, default `127.0.0.1`
- `STREAMING_PORT`: bind port, default `8882`
- `STREAMING_RATE`: events per second, default `1`
- `STREAMING_SCHEMA`: schema file path, default `schema.json`

## Stop

If the server is running in the foreground, stop it with:

```bash
Ctrl+C
```

If it is running in the background, find and stop it with:

```bash
ps -ef | grep streaming_generator.py
kill <pid>
```

For a force stop only if needed:

```bash
kill -9 <pid>
```

## Graceful Shutdown

The server shuts down gracefully when it receives `Ctrl+C` in the foreground process.
Existing client connections are interrupted, the Python process exits, and the port is released so the server can be started again on the same port.

For background runs, prefer `kill <pid>` or `SIGTERM` before using `kill -9`.
That gives the process a normal termination path instead of a hard stop.

## Endpoints

Health check:

```bash
curl http://127.0.0.1:8882/health
```

List streaming datasets and paths:

```bash
curl http://127.0.0.1:8882/datasets
```

Stream all datasets in round-robin order:

```bash
curl -N http://127.0.0.1:8882/events
```

Stream only 5 events from the combined stream:

```bash
curl -N "http://127.0.0.1:8882/events?limit=5"
```

Stream 1 event per second explicitly:

```bash
curl -N "http://127.0.0.1:8882/events?rate=1"
```

Stream a specific dataset:

```bash
curl -N http://127.0.0.1:8882/events/marketing_events
```

Stream a limited number of events from one dataset:

```bash
curl -N "http://127.0.0.1:8882/events/credit_events?limit=3"
```

## Dataset Paths

- `/events/bank_transactions`
- `/events/customer_behavior_events`
- `/events/loan_events`
- `/events/insurance_events`
- `/events/credit_events`
- `/events/marketing_events`
- `/events/customer_profile_updates`

## Response Format

Streaming responses are newline-delimited JSON (`application/x-ndjson`).
Each line is a complete event envelope with:

- `dataset`
- `topic`
- `emitted_at`
- `sequence`
- `payload`
