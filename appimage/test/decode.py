# Helpers to decode screenshots of the coordinate-coded test image.
import subprocess

def load(path):
    data = subprocess.run(['convert', path, '-depth', '8', 'ppm:-'], capture_output=True, check=True).stdout
    parts = data.split(b'\n', 3)
    w, h = map(int, parts[1].split())
    return w, h, parts[3]

def px(img, x, y):
    w, h, d = img
    i = (y * w + x) * 3
    return d[i], d[i + 1], d[i + 2]

def dec(img, x, y):
    r, g, b = px(img, x, y)
    return (r | ((b >> 4) << 8), g | ((b & 15) << 8))

def run(img, coords, axis, W, H):
    """Longest run of screen pixels along a line that decode to a consistent
    image line (constant other-coordinate, non-decreasing coordinate)."""
    best = (0, 0)
    start = None
    prev = None
    for i, (x, y) in enumerate(coords):
        ix, iy = dec(img, x, y)
        ok = (0 <= ix < W) and (0 <= iy < H)
        if ok and prev is not None and start is not None:
            pix, piy = prev
            if axis == 0:
                ok = (iy == piy) and (0 <= ix - pix <= 64)
            else:
                ok = (ix == pix) and (0 <= iy - piy <= 64)
        if ok and start is None:
            start = i
        elif not ok:
            if start is not None and i - start > best[1] - best[0]:
                best = (start, i)
            start = i if (0 <= ix < W and 0 <= iy < H) else None
        prev = (ix, iy)
    if start is not None and len(coords) - start > best[1] - best[0]:
        best = (start, len(coords))
    return coords[best[0]], coords[best[1] - 1]
