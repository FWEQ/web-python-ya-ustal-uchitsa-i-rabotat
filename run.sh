#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
export PYTHONPATH=src

case "${1:-repl}" in
	repl)
		exec python3 -m REPL
		;;
	server)
		exec python3 -m server
		;;
	*)
		echo "usage: $0 [repl|server]" >&2
		exit 1
		;;
esac
