#!/usr/bin/env python3
# Functional test of drag to zoom in gThumb 4, on an X server (Xvfb).
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness import *
import harness

os.makedirs(OUT, exist_ok=True)
open(OUT + '/gthumb.log', 'w').close()

# 1. Wide selection in the middle (width-limited).
p, img1, v, z2 = zoom_scenario('wide', 0.30, 0.35, 0.55, 0.50)
# 2. While zoomed, a plain drag must pan instead of selecting.
cx, cy = (v[0] + v[1]) // 2, (v[2] + v[3]) // 2
before = dec(img1, cx, cy)
drag(cx, cy, cx - 300, cy - 100, mid_shot='wide-3-pan-dragging')
check('zoomed: no crosshair cursor', harness.last_drag_cursor != 'crosshair', 'cursor %s' % (harness.last_drag_cursor or 'default'))
img2 = shot('wide-4-panned')
after = dec(img2, cx, cy)
moved = (after[0] - before[0], after[1] - before[1])
check('zoomed: drag pans the image', abs(moved[0] - 300 / z2) <= 2 and abs(moved[1] - 100 / z2) <= 2,
      'centre pixel %s -> %s, moved %s, expected (%.1f, %.1f)' % (before, after, moved, 300 / z2, 100 / z2))
stop(p)

# 3. Tall selection in the middle (height-limited).
p, _, _, _ = zoom_scenario('tall', 0.45, 0.30, 0.52, 0.62)
stop(p)

# 4. Small selection: deep zoom (about 900%) with fractional offsets, where
#    any rounding to whole image pixels would show as a large error.
p, _, _, _ = zoom_scenario('deep', 0.413, 0.407, 0.481, 0.503)
stop(p)

# 5. Selection touching the image corner: scrolling is clamped there, the
#    selection can't be centred but must still fill and be fully visible.
p, _, _, _ = zoom_scenario('corner', 0.0, 0.0, 0.12, 0.10)
stop(p)

# 6. Narrow selection at the left edge: centring it would scroll past the
#    image edge, so the view is clamped; the selection must still fit.
p, _, _, _ = zoom_scenario('left-edge', 0.0, 0.30, 0.03, 0.62)
stop(p)

# 7. A click without dragging must not zoom.
p = start(True)
img0 = shot('click-0')
v, rect0 = layout(img0)
cx, cy = (v[0] + v[1]) // 2, (v[2] + v[3]) // 2
sh('xdotool', 'mousemove', str(cx), str(cy), 'click', '1'); time.sleep(2.5)
img1 = shot('click-1')
check('click without drag does not zoom', image_rect(img1, v) == rect0[2:], 'image rows %s' % (image_rect(img1, v),))
# 8. Ctrl+drag must not select or zoom: it drags the file instead.
imgd = drag(cx - 200, cy - 130, cx + 100, cy + 70, mods='ctrl', mid_shot='ctrl-1-dragging')
check('ctrl+drag drags the file', harness.last_drag_dnd)
check('ctrl+drag draws no selection', lum(imgd, rect0[1] - 3, rect0[2] + 3) == lum(img0, rect0[1] - 3, rect0[2] + 3))
img2 = shot('ctrl-2-after')
check('ctrl+drag does not zoom', image_rect(img2, v) == rect0[2:], 'image rows %s' % (image_rect(img2, v),))
# 9. Drag to zoom still works after the file was dragged.
drag(cx - 200, cy - 130, cx + 100, cy + 70)
img3 = shot('ctrl-3-drag-after-file-drag')
check('after a file drag, drag still zooms', not harness.last_drag_dnd and image_rect(img3, v) != rect0[2:],
      'file drag %s, image rows %s' % (harness.last_drag_dnd, image_rect(img3, v)))
stop(p)

# 10. Default setting (drag the file): a drag must not zoom or select.
p = start(False)
img0 = shot('default-0')
v, rect0 = layout(img0)
cx, cy = (v[0] + v[1]) // 2, (v[2] + v[3]) // 2
imgd = drag(cx - 200, cy - 130, cx + 100, cy + 70, mid_shot='default-1-dragging')
check('default mode: no crosshair cursor', harness.last_drag_cursor != 'crosshair', 'cursor %s' % (harness.last_drag_cursor or 'default'))
check('default mode: drag drags the file', harness.last_drag_dnd)
check('default mode: drag draws no selection', lum(imgd, rect0[1] - 3, rect0[2] + 3) == lum(img0, rect0[1] - 3, rect0[2] + 3))
img1 = shot('default-2-after')
check('default mode: drag does not zoom', image_rect(img1, v) == rect0[2:], 'image rows %s' % (image_rect(img1, v),))
# 11. Turning the preference on applies immediately, without a restart.
gsettings_set('drag-to-zoom', 'true'); time.sleep(1)
imgd = drag(cx - 200, cy - 130, cx + 100, cy + 70, mid_shot='live-1-dragging')
check('preference applies live: drag does not drag the file', not harness.last_drag_dnd)
img2 = shot('live-2-after')
t2, b2 = image_rect(img2, v)
check('preference applies live: drag zooms', (t2, b2) != rect0[2:], 'image rows %s -> %s' % (rect0[2:], (t2, b2)))
stop(p)

failed = [r for r in results if not r[1]]
print('\n%d checks, %d failed' % (len(results), len(failed)))
sys.exit(1 if failed else 0)
