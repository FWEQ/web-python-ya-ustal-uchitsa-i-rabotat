#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
export PYTHONPATH=src

usage() {
	echo "usage: $0 [repl|server|rpc]"
	echo "  repl    local menu (default)"
	echo "  server  RPC server"
	echo "  rpc     REPL through RpcClient"
}

case "${1:-repl}" in
	repl)
		exec python3 -m REPL
		;;
	server)
		exec python3 -m server
		;;
	rpc|client)
		exec python3 -m REPL rpc
		;;
	-h|--help|help)
		usage
		;;
	*)
		usage >&2
		exit 1
		;;
esac
