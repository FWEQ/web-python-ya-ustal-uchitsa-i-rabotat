#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
export PYTHONPATH=src

usage() {
	echo "usage: $0 [repl|server]"
	echo "  repl    interactive menu (default)"
	echo "  server  RPC server on localhost:8000"
}

case "${1:-repl}" in
	repl)
		exec python3 -m REPL
		;;
	server)
		exec python3 -m server
		;;
	-h|--help|help)
		usage
		;;
	*)
		usage >&2
		exit 1
		;;
esac
