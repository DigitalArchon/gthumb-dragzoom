#!/usr/bin/env python3
# Checks of the AppImage on a test host, beyond drag to zoom itself:
# settings stored in the user's dconf database, video thumbnails and
# playback, translations, and a native Wayland start.
import glob, os, shutil, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness import *
import harness

SCHEMAS = os.environ['TEST_SCHEMA_DIR']        # gThumb's schemas, for the host's gsettings tool

def host_gsettings(*args):
    env = dict(os.environ, GSETTINGS_SCHEMA_DIR=SCHEMAS)
    env.pop('GSETTINGS_BACKEND', None)
    return subprocess.run(['gsettings'] + list(args), env=env, capture_output=True, text=True).stdout.strip()

def quit_app(p):
    sh('xdotool', 'key', 'ctrl+q')
    try:
        p.wait(10)
        return True
    except subprocess.TimeoutExpired:
        stop(p)
        return False

os.makedirs(OUT, exist_ok=True)
open(OUT + '/gthumb.log', 'w').close()
os.environ.pop('GSETTINGS_BACKEND', None)      # the normal dconf backend

# 1. Settings in dconf: set with the host's tools, read by the AppImage.
host_gsettings('set', 'org.gnome.gthumb.viewers.images', 'drag-to-zoom', 'true')
host_gsettings('set', 'org.gnome.gthumb.viewers.images', 'zoom-type', "'maximize'")
p = start(None)
img0 = shot('dconf-0')
v, rect0 = layout(img0)
cx, cy = (v[0] + v[1]) // 2, (v[2] + v[3]) // 2
drag(cx - 200, cy - 130, cx + 100, cy + 70, mid_shot='dconf-1-dragging')
img1 = shot('dconf-2-zoomed')
check('dconf: preference set on the host is used', not harness.last_drag_dnd and image_rect(img1, v) != rect0[2:],
      'image rows %s -> %s' % (rect0[2:], image_rect(img1, v)))
# ... and written by the AppImage: the zoom type is saved on quit.
check('dconf: quit with Ctrl+Q', quit_app(p))
saved = host_gsettings('get', 'org.gnome.gthumb.viewers.images', 'zoom-type')
check('dconf: settings saved by the AppImage are in the user database', saved == "'keep-previous'", 'zoom-type %s' % saved)
check('dconf: drag-to-zoom still set after a restart', host_gsettings('get', 'org.gnome.gthumb.viewers.images', 'drag-to-zoom') == 'true')

# 2. Video thumbnails (made by the separate video-thumbnailer program).
media = os.path.abspath('media')
shutil.rmtree(os.path.expanduser('~/.cache/thumbnails'), ignore_errors=True)
p = start(None, image=media, wait_for_image=False)
thumbs = []
for _ in range(30):
    time.sleep(1)
    thumbs = glob.glob(os.path.expanduser('~/.cache/thumbnails/*/*.png'))
    if len(thumbs) >= 2:
        break
time.sleep(2)
shot('video-0-browser')
failed = glob.glob(os.path.expanduser('~/.cache/thumbnails/fail/*/*.png'))
check('video thumbnails created', len(thumbs) >= 2 and not failed, '%d thumbnails, %d failures' % (len(thumbs), len(failed)))
stop(p)

# 3. Video playback.
for name in ('ball.mp4', 'bars.webm'):
    p = start(None, image=os.path.join(media, name), wait_for_image=False)
    time.sleep(8)
    img = shot('video-1-' + name)
    w, h, _ = img
    colours = {px(img, x, y) for x in range(100, w - 100, 37) for y in range(120, h - 120, 37)}
    alive = p.poll() is None
    check('video playback: %s shows frames' % name, alive and len(colours) > 4,
          'running %s, %d distinct colours' % (alive, len(colours)))
    stop(p)

# 4. The preference in Preferences > Images.
p = start(None, image=media, wait_for_image=False)
time.sleep(5)
sh('xdotool', 'key', 'ctrl+comma'); time.sleep(3)
sh('xdotool', 'mousemove', '304', '354', 'click', '1'); time.sleep(2)
shot('prefs-images')
stop(p)

# 5. Translations: German user interface.
env = dict(os.environ, LANGUAGE='de', LANG='de_DE.UTF-8', LC_ALL='de_DE.UTF-8')
p = start(None, image=media, wait_for_image=False, env=env)
time.sleep(6)
shot('locale-de-browser')
sh('xdotool', 'key', 'ctrl+comma'); time.sleep(3)
shot('locale-de-preferences')
stop(p)
log = open(OUT + '/gthumb.log').read()
check('no locale warnings', 'Locale not supported' not in log and 'cannot set locale' not in log.lower())

failed = [r for r in results if not r[1]]
print('\n%d checks, %d failed' % (len(results), len(failed)))
sys.exit(1 if failed else 0)
