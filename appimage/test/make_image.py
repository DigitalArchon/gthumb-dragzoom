# Writes a PNG (no colour/gamma chunks) whose pixel colours encode their
# own coordinates: R = x & 255, G = y & 255, B = (x >> 8) << 4 | (y >> 8)
import struct, sys, zlib
w, h = int(sys.argv[1]), int(sys.argv[2])
raw = bytearray()
for y in range(h):
    raw.append(0)
    for x in range(w):
        raw += bytes((x & 255, y & 255, ((x >> 8) << 4) | (y >> 8)))
def chunk(t, d):
    return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
with open(sys.argv[3], 'wb') as f:
    f.write(b'\x89PNG\r\n\x1a\n')
    f.write(chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)))
    f.write(chunk(b'IDAT', zlib.compress(bytes(raw), 9)))
    f.write(chunk(b'IEND', b''))
