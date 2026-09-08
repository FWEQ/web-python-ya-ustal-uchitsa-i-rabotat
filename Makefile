.PHONY: help run server rpc

help:
	@echo "make server  - RPC TCP server on localhost:8001"
	@echo "make run     - local REPL"
	@echo "make rpc     - REPL through RpcClient"

run:
	PYTHONPATH=src python3 -m REPL

server:
	PYTHONPATH=src python3 -m server

rpc:
	PYTHONPATH=src python3 -m REPL rpc
