"""
Creates minimal placeholder PNG files for pet_idle.png and pet_talk.png.
Run this once if you don't have your own artwork yet.
Replace the files with your own 300x400 (or any size) PNGs when ready.
"""
import struct, zlib, os

def _png(width, height, fill_rgb, label, font_color=(255, 255, 255)):
    """Build a minimal valid PNG with a solid background and simple label text."""
    r, g, b = fill_rgb
    row = bytes([0] + [r, g, b, 255] * width)
    raw = row * height
    compressed = zlib.compress(raw, 9)

    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(c[4:]) & 0xffffffff)

    sig    = b'\x89PNG\r\n\x1a\n'
    ihdr   = chunk(b'IHDR', struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
    idat   = chunk(b'IDAT', compressed)
    iend   = chunk(b'IEND', b'')
    return sig + ihdr + idat + iend

out_dir = os.path.join(os.path.dirname(__file__), "static")

files = {
    "pet_idle.png": ((244, 114, 182), "IDLE (mouth closed)"),
    "pet_talk.png": ((236,  72, 153), "TALK (mouth open)"),
}

for fname, (color, label) in files.items():
    path = os.path.join(out_dir, fname)
    if os.path.exists(path):
        print(f"  skip  {fname}  (already exists)")
        continue
    data = _png(300, 400, color, label)
    with open(path, "wb") as f:
        f.write(data)
    print(f"  created  {fname}  — replace with your own art!")
