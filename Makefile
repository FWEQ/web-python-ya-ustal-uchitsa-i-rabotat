.PHONY: help run server rpc test

help:
	@echo "make server  - RPC TCP server on localhost:8001"
	@echo "make run     - local REPL"
	@echo "make rpc     - REPL through RpcClient"
	@echo "make test    - MBT + branch coverage report"

run:
	PYTHONPATH=src python3 -m REPL

server:
	PYTHONPATH=src python3 -m server

rpc:
	PYTHONPATH=src python3 -m REPL rpc

test:
	PYTHONPATH=src python3 -m coverage run --branch \
		-m unittest discover -s tests -v
	python3 -m coverage report -m | tee coverage.txt
