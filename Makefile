.PHONY: help run server

help:
	@echo "make server  - RPC TCP server on localhost:8000"
	@echo "make run     - REPL"

run:
	PYTHONPATH=src python3 -m REPL

server:
	PYTHONPATH=src python3 -m server
