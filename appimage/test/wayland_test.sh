#!/bin/bash
# Native Wayland start of $GTHUMB on a headless Weston compositor.
export HOME=/tmp/home-wayland; mkdir -p $HOME
export XDG_RUNTIME_DIR=/tmp/xdg-wayland; mkdir -p -m 700 $XDG_RUNTIME_DIR
mkdir -p out
weston --backend=headless --socket=wayland-test --width=1400 --height=1000 > out/weston.log 2>&1 &
sleep 3
unset DISPLAY
export WAYLAND_DISPLAY=wayland-test WAYLAND_DEBUG=client
dbus-run-session -- bash -c "timeout 25 '$GTHUMB' '$PWD/test.png' > out/wayland.log 2>&1; echo exit=\$? >> out/wayland.log"
if grep -q "xdg_toplevel" out/wayland.log && grep -q "wl_surface.*commit" out/wayland.log && grep -q "exit=124" out/wayland.log; then
	echo "PASS native Wayland: window created and drawn, still running after 25 s"
else
	echo "FAIL native Wayland start"; grep -v "^\[" out/wayland.log | tail -20
	exit 1
fi
