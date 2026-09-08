# web-python

Practice 1: in-memory data access layer for Entity, Query
and Feedback. Records are tuples. Stage 2 adds RPC over
TCP (little-endian header + XML body).

## Layout

- `src/` — application code
- `run.sh` — start the REPL or the RPC server
- `Makefile` — `make run` and `make server`

## Requirements

- Python 3.10+
- [Scapy](https://scapy.net/) (`pip install scapy`)

## Run

Start the server, then the REPL in another terminal:

```bash
./run.sh server
./run.sh
```

or

```bash
make server
make run
```

In the menu: `14` or `demo` runs all functions.

RPC listens on `localhost:8000`. Client requests are
appended to `journal.log`.
