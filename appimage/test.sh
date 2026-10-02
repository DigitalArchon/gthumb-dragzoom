#!/bin/bash
# Tests the AppImage in OUTPUT_DIR (default ./dist) with podman, on
# Ubuntu 24.04 (the Linux Mint 22 base) and CachyOS.
#
#   appimage/test.sh [OUTPUT_DIR]
#
# Full logs: OUTPUT_DIR/test-results/<host>.log, screenshots next to them.
set -u

REPO=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
OUT=$(cd "${1:-$PWD/dist}" && pwd)
mkdir -p "$OUT"/test-results
status=0
for host in ubuntu2404 cachyos; do
	podman build -q -t gthumb-appimage-test-$host -f "$REPO"/appimage/test-hosts/Containerfile.$host \
		"$REPO"/appimage/test-hosts > /dev/null || exit 1
	podman run --rm --userns=keep-id -v "$REPO:/repo:ro" -v "$OUT:/out" gthumb-appimage-test-$host \
		/repo/appimage/test/run_tests.sh > "$OUT"/test-results/$host.log 2>&1
	result=$?
	grep -E '^(Testing|== |PASS native|FAIL|SKIP|[0-9]+ checks)' "$OUT"/test-results/$host.log
	if [ $result = 0 ]; then echo "$host: all tests passed"; else echo "$host: FAILED"; status=1; fi
done
exit $status
