.PHONY: run server

run:
	PYTHONPATH=src python3 -m REPL

server:
	PYTHONPATH=src python3 -m server
