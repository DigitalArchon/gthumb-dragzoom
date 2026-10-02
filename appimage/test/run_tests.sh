#!/bin/bash
# Runs all the tests against the AppImage in /out, inside a test-host
# container (see appimage/test.sh).  The repository is mounted read-only
# at /repo; screenshots and logs go to /out/test-results/<host>.
HOST=$(. /etc/os-release; echo "$ID${VERSION_ID:+-$VERSION_ID}")
RESULTS=/out/test-results/$HOST
export GTHUMB=$(ls /out/*.AppImage | head -1)
export APPIMAGE_EXTRACT_AND_RUN=1          # containers have no FUSE

rm -rf /tmp/test && cp -r /repo/appimage/test /tmp/test && cd /tmp/test
python3 make_image.py 1600 1000 test.png
# gThumb's schemas, for the tests' own gsettings calls.
mkdir -p /tmp/extracted && (cd /tmp/extracted && "$GTHUMB" --appimage-extract > /dev/null 2>&1)
export TEST_SCHEMA_DIR=$(dirname "$(find /tmp/extracted -name gschemas.compiled | head -1)")
echo "Testing $(basename "$GTHUMB") on $(. /etc/os-release; echo $PRETTY_NAME), glibc $(ldd --version | head -1 | grep -o '[0-9.]*$')"

status=0
Xvfb :99 -screen 0 1400x1000x24 > /dev/null 2>&1 &
sleep 1
echo "== Drag to zoom"
DISPLAY=:99 HOME=/tmp/home1 GSETTINGS_BACKEND=keyfile dbus-run-session -- python3 functional_test.py || status=1
mv out out-functional
echo "== Settings, video, translations"
DISPLAY=:99 HOME=/tmp/home2 dbus-run-session -- python3 real_world_test.py || status=1
mv out out-real-world
echo "== Wayland"
./wayland_test.sh || status=1
mv out out-wayland

rm -rf "$RESULTS" && mkdir -p "$RESULTS" && cp -r out-* "$RESULTS"/
echo "Screenshots and logs: test-results/$HOST"
exit $status
