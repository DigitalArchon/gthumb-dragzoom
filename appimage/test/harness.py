# Helpers for driving gThumb on an X server (Xvfb) and decoding screenshots.
#
# The test image's pixel colours encode their own coordinates (make_image.py),
# so a screenshot tells exactly which image pixel every screen pixel shows.
import ctypes, math, os, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from decode import load, dec, run, px

W, H = 1600, 1000                      # test image size
BG = (17, 17, 17)                      # viewer background
SHADED_ROWS = 4                        # top rows tinted by the header bar shadow
OUT = 'out'
APP = os.environ['GTHUMB']                    # the program to test
results = []

# --- X helpers -------------------------------------------------------------

_x11 = ctypes.cdll.LoadLibrary('libX11.so.6')
_x11.XOpenDisplay.restype = ctypes.c_void_p
_x11.XInternAtom.restype = ctypes.c_ulong
_x11.XInternAtom.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int]
_x11.XGetSelectionOwner.restype = ctypes.c_ulong
_x11.XGetSelectionOwner.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
_x11.XSetSelectionOwner.argtypes = [ctypes.c_void_p, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong]
_x11.XDefaultRootWindow.restype = ctypes.c_ulong
_x11.XDefaultRootWindow.argtypes = [ctypes.c_void_p]
_x11.XCreateSimpleWindow.restype = ctypes.c_ulong
_x11.XCreateSimpleWindow.argtypes = [ctypes.c_void_p, ctypes.c_ulong] + [ctypes.c_int] * 4 + [ctypes.c_uint, ctypes.c_ulong, ctypes.c_ulong]
_x11.XFlush.argtypes = [ctypes.c_void_p]
_dpy = None
_own_window = None

def display():
    global _dpy
    if _dpy is None:
        _dpy = _x11.XOpenDisplay(None)
    return _dpy

def _xdnd_selection():
    return _x11.XInternAtom(display(), b'XdndSelection', 0)

def reset_file_drag():
    """Take the XdndSelection, which gThumb keeps after a drag ends."""
    global _own_window
    if _own_window is None:
        _own_window = _x11.XCreateSimpleWindow(display(), _x11.XDefaultRootWindow(display()), 0, 0, 1, 1, 0, 0, 0)
    _x11.XSetSelectionOwner(display(), _xdnd_selection(), _own_window, 0)
    _x11.XFlush(display())

def file_drag_active():
    """True if a file drag started since reset_file_drag ()."""
    owner = _x11.XGetSelectionOwner(display(), _xdnd_selection())
    return owner not in (0, _own_window)

class XFixesCursorImage(ctypes.Structure):
    _fields_ = [('x', ctypes.c_short), ('y', ctypes.c_short),
                ('width', ctypes.c_ushort), ('height', ctypes.c_ushort),
                ('xhot', ctypes.c_ushort), ('yhot', ctypes.c_ushort),
                ('cursor_serial', ctypes.c_ulong), ('pixels', ctypes.c_void_p),
                ('atom', ctypes.c_ulong), ('name', ctypes.c_char_p)]

try:
    _xfixes = ctypes.cdll.LoadLibrary('libXfixes.so.3')
    _xfixes.XFixesGetCursorImage.restype = ctypes.POINTER(XFixesCursorImage)
    _xfixes.XFixesGetCursorImage.argtypes = [ctypes.c_void_p]
except OSError:
    _xfixes = None

def cursor_name():
    if _xfixes is None:
        return None
    img = _xfixes.XFixesGetCursorImage(display())
    if not img or not img.contents.name:
        return None
    return img.contents.name.decode()

def sh(*a):
    return subprocess.run(a, capture_output=True, text=True).stdout.strip()

# --- gThumb ----------------------------------------------------------------

def settings(drag_to_zoom):
    os.makedirs(os.path.expanduser('~/.config/glib-2.0/settings'), exist_ok=True)
    with open(os.path.expanduser('~/.config/glib-2.0/settings/keyfile'), 'w') as f:
        f.write("[org/gnome/gthumb/viewers/images]\ndrag-to-zoom=%s\nzoom-type='maximize'\n"
                % ('true' if drag_to_zoom else 'false'))

def gsettings_set(key, value):
    env = dict(os.environ)
    if os.environ.get('TEST_SCHEMA_DIR'):
        env['GSETTINGS_SCHEMA_DIR'] = os.environ['TEST_SCHEMA_DIR']
    subprocess.run(['gsettings', 'set', 'org.gnome.gthumb.viewers.images', key, value], check=True, env=env)

def start(drag_to_zoom=True, image='test.png', wait_for_image=True, env=None):
    """Start gThumb on image (a file or a folder).  drag_to_zoom=None
    leaves the settings as they are."""
    if drag_to_zoom is not None:
        settings(drag_to_zoom)
    p = subprocess.Popen([APP, os.path.abspath(image)], stdout=open(OUT + '/gthumb.log', 'a'),
                         stderr=subprocess.STDOUT, env=env)
    wid = ''
    for _ in range(150):
        time.sleep(0.2)
        wid = sh('xdotool', 'search', '--onlyvisible', '--class', 'gthumb').split('\n')[0]
        if wid:
            break
    sh('xdotool', 'windowmove', wid, '0', '0')
    sh('xdotool', 'windowsize', wid, '1400', '1000')
    sh('xdotool', 'mousemove', '1399', '999')
    # Wait for the image to be shown.
    for _ in range(30 if wait_for_image else 0):
        time.sleep(1)
        img = shot('start')
        if px(img, 105, 60) == BG and px(img, 105, 500) != BG:
            break
    time.sleep(2)
    return p

def stop(p):
    p.terminate()
    try:
        p.wait(5)
    except subprocess.TimeoutExpired:
        p.kill()
    subprocess.run(['pkill', '-x', 'gthumb'])
    time.sleep(1)

def shot(name):
    path = '%s/%s.png' % (OUT, name)
    sh('import', '-window', 'root', path)
    return load(path)

def probe_column(v):
    """A column clear of the overlay controls (bottom centre, top right)."""
    return v[0] + 300

def probe_row(v):
    """A row clear of the overlay controls (next/previous arrows at mid
    height, top right indicators)."""
    return v[2] + 200

def layout(img):
    """Viewer and on-screen image bounds (inclusive), for a wide image that
    fits the viewer: it fills the width, with background bands above and
    below."""
    w, h, _ = img
    cx = 105
    ys = [y for y in range(h) if px(img, cx, y) == BG]
    vy1, vy2 = min(ys), max(ys)
    t = next(y for y in range(vy1, vy2) if px(img, cx, y) != BG)
    b = next(y for y in range(vy2, vy1, -1) if px(img, cx, y) != BG)
    xs = [x for x in range(w) if px(img, x, vy1 + 2) == BG]
    vx1, vx2 = min(xs), max(xs)
    return (vx1, vx2, vy1, vy2), (vx1, vx2, t, b)

def image_rect(img, v):
    vx1, vx2, vy1, vy2 = v
    cx = probe_column(v)
    t = next((y for y in range(vy1, vy2) if px(img, cx, y) != BG), None)
    b = next((y for y in range(vy2, vy1, -1) if px(img, cx, y) != BG), None)
    return t, b

last_drag_dnd = False
last_drag_cursor = None

def drag(x1, y1, x2, y2, mods=None, mid_shot=None):
    global last_drag_dnd, last_drag_cursor
    sh('xdotool', 'mousemove', str(x1), str(y1))
    time.sleep(0.3)
    last_drag_cursor = cursor_name()
    reset_file_drag()
    if mods:
        sh('xdotool', 'keydown', mods)
    sh('xdotool', 'mousedown', '1')
    steps = 10
    for i in range(1, steps + 1):
        sh('xdotool', 'mousemove', str(x1 + (x2 - x1) * i // steps), str(y1 + (y2 - y1) * i // steps))
        time.sleep(0.03)
    time.sleep(0.4)
    last_drag_dnd = file_drag_active()
    img = shot(mid_shot) if mid_shot else None
    if last_drag_dnd:
        # Cancel the file drag: dropping the file on gThumb itself would
        # reload it.
        sh('xdotool', 'key', 'Escape')
        time.sleep(0.5)
    sh('xdotool', 'mouseup', '1')
    if mods:
        sh('xdotool', 'keyup', mods)
    time.sleep(2.5)                    # also lets the overlay controls hide
    return img

def check(name, cond, detail=''):
    results.append((name, cond, detail))
    print(('PASS' if cond else 'FAIL'), name, ('- ' + detail) if detail else '', flush=True)

def lum(img, x, y):
    return sum(px(img, x, y))

def edge_check(name, img, v, axis, lo, z2):
    """The zoomed selection, starting at image coordinate lo, must span the
    viewer exactly along axis: every screen pixel on the centre line must
    show the image pixel predicted by lo + (i + 0.5) / z2, allowing a 1
    screen pixel shift at pixel boundaries."""
    vx1, vx2, vy1, vy2 = v
    if axis == 0:
        line = [(x, probe_row(v)) for x in range(vx1, vx2 + 1)]
        first = 0
    else:
        line = [(probe_column(v), y) for y in range(vy1, vy2 + 1)]
        first = SHADED_ROWS
    vals = [dec(img, *p)[axis] for p in line]
    exp = [math.floor(lo + (i + 0.5) / z2) for i in range(len(line))]
    bad = [i for i in range(first, len(vals)) if vals[i] not in exp[max(i - 1, 0):i + 2]]
    # Largest offset, in screen pixels, between where an image pixel is
    # shown and where it should be.
    worst = 0
    for i in bad:
        js = [j for j in range(len(exp)) if exp[j] == vals[i]]
        if js:
            worst = max(worst, min(abs(j - i) for j in js))
    check('%s: selection %s fills the window exactly' % (name, 'width' if axis == 0 else 'height'), not bad,
          'edges show image px %d..%d (expected %d..%d), %d/%d screen px off by more than 1 px (worst %d px)'
          % (vals[first], vals[-1], exp[first], exp[-1], len(bad), len(vals) - first, worst))

def zoom_scenario(name, fx1, fy1, fx2, fy2):
    """Drag over a selection given as fractions of the on-screen image."""
    p = start(True)
    img0 = shot(name + '-0-before')
    v, (l, r, t, b) = layout(img0)
    vx1, vx2, vy1, vy2 = v
    vw, vh = vx2 - vx1 + 1, vy2 - vy1 + 1
    z = (r - l + 1) / W
    sx1 = l + int((r - l) * fx1); sx2 = l + int((r - l) * fx2)
    sy1 = t + int((b - t) * fy1); sy2 = t + int((b - t) * fy2)
    # Selected area in image pixels, as gThumb computes it.
    X1, X2 = (sx1 - l) / z, (sx2 - l) / z
    Y1, Y2 = (sy1 - t) / z, (sy2 - t) / z
    z2 = min(vw / (X2 - X1), vh / (Y2 - Y1))
    width_limited = vw / (X2 - X1) <= vh / (Y2 - Y1)
    print('   viewer %dx%d, fit zoom %.4f, selection x %.2f..%.2f y %.2f..%.2f -> zoom %.3f (%s-limited)'
          % (vw, vh, z, X1, X2, Y1, Y2, z2, 'width' if width_limited else 'height'))
    imgd = drag(sx1, sy1, sx2, sy2, mid_shot=name + '-1-dragging')
    cursor_check(name + ': crosshair cursor over a fitting image', last_drag_cursor == 'crosshair')
    check(name + ': plain drag does not drag the file', not last_drag_dnd)
    out_pt = (r - 3, t + 3) if fx2 < 0.9 else (l + 3, b - 3)
    in_pt = ((sx1 + sx2) // 2, (sy1 + sy2) // 2)
    check(name + ': selection overlay drawn while dragging',
          lum(imgd, *out_pt) < lum(img0, *out_pt) * 0.7 and lum(imgd, *in_pt) == lum(img0, *in_pt),
          'outside %d->%d, inside %d->%d' % (lum(img0, *out_pt), lum(imgd, *out_pt), lum(img0, *in_pt), lum(imgd, *in_pt)))
    img1 = shot(name + '-2-zoomed')
    cy, cx = (vy1 + vy2) // 2, (vx1 + vx2) // 2
    (ax, _), (bx, _) = [dec(img1, *q) for q in run(img1, [(x, probe_row(v)) for x in range(vx1, vx2 + 1)], 0, W, H)]
    (_, ay), (_, by_) = [dec(img1, *q) for q in run(img1, [(probe_column(v), y) for y in range(vy1 + SHADED_ROWS, vy2 + 1)], 1, W, H)]
    print('   visible image px: x %d..%d  y %d..%d' % (ax, bx, ay, by_))
    if width_limited:
        # The selection spans the window, so its centre at the window
        # centre means X1 at the window's left edge, even if it touches
        # the image edge.
        edge_check(name, img1, v, 0, X1, z2)
        check(name + ': selection height fully visible', ay <= math.floor(Y1) + 1 and by_ >= math.ceil(Y2) - 1,
              'y %d..%d contains %.1f..%.1f' % (ay, by_, Y1, Y2))
    else:
        edge_check(name, img1, v, 1, Y1, z2)
        check(name + ': selection width fully visible', ax <= math.floor(X1) and bx >= math.ceil(X2) - 1,
              'x %d..%d contains %.1f..%.1f' % (ax, bx, X1, X2))
    return p, img1, v, z2

def cursor_check(name, cond):
    if last_drag_cursor is None:
        print('SKIP', name, '- cursor name not available', flush=True)
    else:
        check(name, cond, 'cursor %s' % last_drag_cursor)
