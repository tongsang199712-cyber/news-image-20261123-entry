#!/usr/bin/env python3
"""news-image-20261123: sum up Monday 23 November 2026's world news in one
image. Pure Python 3.13 standard library: draws a newspaper front page with
a bitmap font (font.bin, built from DejaVu Sans Bold) and writes a PNG with
its own encoder (zlib). No network, no randomness, no clock: two runs write
identical bytes.

Run:  mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
"""
import math
import os
import struct
import zlib

W, H = 1024, 1024

PAPER = (246, 241, 231)
INK = (26, 26, 26)
NAVY = (16, 38, 74)
NAVY_DARK = (11, 28, 56)
RED = (179, 32, 44)
GOLD = (201, 162, 39)
GOLD_LT = (232, 196, 90)
BLUE = (37, 99, 235)
TEAL = (14, 122, 107)
SKY = (168, 204, 232)
SKY_LT = (205, 226, 242)
SEA = (23, 68, 120)
SEA_DK = (16, 48, 88)
GREY = (90, 100, 112)
GREY_DK = (52, 58, 66)
ORANGE = (245, 158, 11)
YELLOW = (253, 224, 71)
WHITE = (255, 255, 255)
CREAM = (252, 248, 240)


# ---------------------------------------------------------------- font
def load_font(path):
    with open(path, "rb") as f:
        data = f.read()
    assert data[:5] == b"MFNT1"
    (n,) = struct.unpack(">H", data[5:7])
    pos = 7
    glyphs = {}
    for _ in range(n):
        code, adv, x0, y0, w, h = struct.unpack(">BBbbBB", data[pos:pos + 6])
        pos += 6
        row_bytes = (w + 7) // 8
        bits = data[pos:pos + row_bytes * h]
        pos += row_bytes * h
        glyphs[code] = (adv, x0, y0, w, h, bits)
    return glyphs


FONT = load_font(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "font.bin"))


def text_width(text, scale):
    total = 0
    for ch in text:
        g = FONT.get(ord(ch))
        if g is None:
            continue
        total += g[0] * scale
    return total


def wrap_text(text, scale, max_w):
    lines, cur = [], ""
    for word in text.split(" "):
        trial = word if not cur else cur + " " + word
        if text_width(trial, scale) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(w * h * 3)
        self.fill_rect(0, 0, w, h, bg)

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = c

    def fill_rect(self, x, y, w, h, c):
        x0, y0 = max(0, int(x)), max(0, int(y))
        x1, y1 = min(self.w, int(x + w)), min(self.h, int(y + h))
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                self.px[i], self.px[i + 1], self.px[i + 2] = c
                i += 3

    def hline(self, x, y, w, c):
        self.fill_rect(x, y, w, 1, c)

    def circle(self, cx, cy, r, c):
        r = int(r)
        for yy in range(cy - r, cy + r + 1):
            dy = yy - cy
            dx = int((r * r - dy * dy) ** 0.5)
            self.fill_rect(cx - dx, yy, dx * 2 + 1, 1, c)

    def disc(self, cx, cy, r, c):
        self.circle(cx, cy, r, c)

    def ring(self, cx, cy, r, t, c):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                d2 = (xx - cx) ** 2 + (yy - cy) ** 2
                if (r - t) ** 2 <= d2 <= r * r:
                    self.set(xx, yy, c)

    def line(self, x0, y0, x1, y1, c, t=1):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err, x, y = dx - dy, x0, y0
        half = t // 2
        while True:
            self.fill_rect(x - half, y - half, t, t, c)
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy

    def polygon(self, pts, c):
        # scanline fill
        ys = [p[1] for p in pts]
        for yy in range(int(min(ys)), int(max(ys)) + 1):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= yy < y1) or (y1 <= yy < y0):
                    xs.append(x0 + (yy - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                self.fill_rect(int(xs[i]), yy, int(xs[i + 1]) - int(xs[i]) + 1, 1, c)

    def arc_points(self, cx, cy, r, a0, a1, steps=24):
        import math
        pts = []
        for i in range(steps + 1):
            a = a0 + (a1 - a0) * i / steps
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        return pts

    def star(self, cx, cy, r_out, r_in, points, c, rot=-90):
        import math
        pts = []
        for i in range(points * 2):
            r = r_out if i % 2 == 0 else r_in
            a = math.radians(rot + i * 180 / points)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        self.polygon(pts, c)

    def text(self, x, y, s, scale, c, align="left"):
        """Draw text; y is the top of the 44px em cell (baseline at y+34*scale)."""
        if align == "center":
            x = x - text_width(s, scale) / 2
        elif align == "right":
            x = x - text_width(s, scale)
        cx = x
        for ch in s:
            g = FONT.get(ord(ch))
            if g is None:
                continue
            adv, gx0, gy0, w, h, bits = g
            row_bytes = (w + 7) // 8
            for gy in range(h):
                for gx in range(w):
                    if bits[gy * row_bytes + gx // 8] & (0x80 >> (gx % 8)):
                        dx0 = int(cx + (gx0 + gx) * scale)
                        dx1 = int(cx + (gx0 + gx + 1) * scale)
                        dy0 = int(y + (gy0 + gy) * scale)
                        dy1 = int(y + (gy0 + gy + 1) * scale)
                        if dx1 <= dx0:
                            dx1 = dx0 + 1
                        if dy1 <= dy0:
                            dy1 = dy0 + 1
                        self.fill_rect(dx0, dy0, dx1 - dx0, dy1 - dy0, c)
            cx += adv * scale
        return cx

    def png_bytes(self):
        raw = bytearray()
        for yy in range(self.h):
            raw.append(0)
            raw += self.px[yy * self.w * 3:(yy + 1) * self.w * 3]
        import binascii

        def chunk(tag, data):
            return (struct.pack(">I", len(data)) + tag + data +
                    struct.pack(">I", binascii.crc32(tag + data) & 0xFFFFFFFF))

        ihdr = struct.pack(">IIBBBBB", self.w, self.h, 8, 2, 0, 0, 0)
        return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) +
                chunk(b"IDAT", zlib.compress(bytes(raw), 6)) +
                chunk(b"IEND", b""))


# ---------------------------------------------------------------- artwork
def draw_lead_scene(cv, x, y, w, h):
    """Benghazi harbour: sky, sea, a grey warship, explosion, drones."""
    # sky bands
    cv.fill_rect(x, y, w, h * 0.42, SKY_LT)
    cv.fill_rect(x, y + h * 0.42, w, h * 0.16, SKY)
    # sea
    cv.fill_rect(x, y + h * 0.58, w, h * 0.42, SEA)
    cv.fill_rect(x, y + h * 0.58, w, 4, SEA_DK)
    for k in range(4):
        wy = y + int(h * (0.66 + 0.08 * k))
        cv.fill_rect(x + 18 + k * 31, wy, 90 - k * 12, 3, (120, 170, 210))
    # distant shoreline
    cv.fill_rect(x, y + int(h * 0.52), w, int(h * 0.06), (148, 164, 150))
    cv.fill_rect(x + 30, y + int(h * 0.44), 26, int(h * 0.08), (120, 128, 122))
    cv.fill_rect(x + 66, y + int(h * 0.47), 18, int(h * 0.05), (120, 128, 122))
    # warship hull
    hx, hy = x + 40, y + int(h * 0.60)
    cv.polygon([(hx, hy), (hx + 250, hy), (hx + 285, hy + 34),
                (hx + 265, hy + 52), (hx + 18, hy + 52)], GREY_DK)
    cv.fill_rect(hx + 8, hy + 34, 262, 6, (30, 34, 40))
    # superstructure + funnel + mast
    cv.fill_rect(hx + 96, hy - 34, 78, 34, GREY)
    cv.fill_rect(hx + 190, hy - 26, 26, 26, GREY_DK)
    cv.line(hx + 60, hy, hx + 60, hy - 62, GREY_DK, 5)
    cv.line(hx + 60, hy - 62, hx + 78, hy - 48, GREY_DK, 4)
    cv.fill_rect(hx + 112, hy - 46, 46, 5, WHITE)
    # flag
    cv.polygon([(hx + 60, hy - 62), (hx + 88, hy - 56), (hx + 60, hy - 50)],
               (255, 213, 0))
    cv.polygon([(hx + 60, hy - 56), (hx + 88, hy - 56), (hx + 60, hy - 50)],
               (0, 87, 184))
    # explosion above the stern
    ex, ey = hx + 236, hy - 58
    cv.star(ex, ey, 74, 30, 9, ORANGE)
    cv.star(ex, ey, 48, 20, 9, YELLOW)
    cv.circle(ex, ey, 20, (255, 240, 170))
    # smoke
    for sx, sy, sr in [(ex - 52, ey - 46, 22), (ex - 18, ey - 66, 26),
                       (ex + 22, ey - 58, 20), (ex + 56, ey - 34, 16)]:
        cv.circle(sx, sy, sr, (70, 74, 80))
    # naval drones in the sky
    for dx, dy in [(x + 52, y + 44), (x + 118, y + 26), (x + 196, y + 52)]:
        cv.line(dx - 16, dy + 14, dx, dy, (60, 60, 60), 2)
        cv.circle(dx, dy, 7, (30, 30, 30))
        cv.line(dx - 10, dy - 4, dx + 10, dy - 4, (30, 30, 30), 3)
    # caption strip
    cv.fill_rect(x, y + h - 34, w, 34, NAVY_DARK)
    cv.text(x + 14, y + h - 32, "BENGHAZI, LIBYA", 0.85, GOLD_LT)


def icon_strikes(cv, cx, cy, r):
    cv.disc(cx, cy, r, (44, 52, 62))
    cv.fill_rect(cx - 34, cy + 2, 26, 34, (120, 128, 138))
    cv.fill_rect(cx - 4, cy - 12, 26, 48, (150, 158, 168))
    cv.fill_rect(cx + 24, cy + 12, 16, 24, (120, 128, 138))
    for bx in (cx - 28, cx - 16, cx + 4, cx + 14):
        cv.fill_rect(bx, cy + 12, 6, 6, (255, 220, 120))
    cv.polygon([(cx - 30, cy + 2), (cx - 18, cy - 26), (cx - 8, cy + 2)],
               ORANGE)
    cv.polygon([(cx + 2, cy - 12), (cx + 12, cy - 34), (cx + 22, cy - 12)],
               YELLOW)
    cv.circle(cx - 22, cy - 34, 9, (90, 96, 104))
    cv.circle(cx + 8, cy - 42, 11, (90, 96, 104))


def icon_eu(cv, cx, cy, r):
    import math
    cv.disc(cx, cy, r, (0, 51, 153))
    for i in range(12):
        a = math.radians(i * 30 - 90)
        cv.star(cx + int(30 * math.cos(a)), cy + int(30 * math.sin(a)),
                7, 3, 5, GOLD)


def icon_capitol(cv, cx, cy, r):
    cv.disc(cx, cy, r, NAVY)
    # dome
    pts = cv.arc_points(cx, cy + 6, 26, math.pi, 2 * math.pi, 20)
    cv.polygon(pts + [(cx + 26, cy + 6), (cx - 26, cy + 6)], WHITE)
    cv.fill_rect(cx - 30, cy + 6, 60, 6, WHITE)
    cv.fill_rect(cx - 34, cy + 12, 68, 5, WHITE)
    for dx in (-24, -8, 8, 24):
        cv.fill_rect(cx + dx - 3, cy + 17, 6, 20, WHITE)
    cv.fill_rect(cx - 38, cy + 37, 76, 5, WHITE)
    cv.line(cx, cy - 20, cx, cy - 34, WHITE, 3)
    cv.polygon([(cx, cy - 34), (cx + 14, cy - 30), (cx, cy - 26)], RED)


def icon_climate(cv, cx, cy, r):
    cv.disc(cx, cy, r, TEAL)
    cv.circle(cx, cy, 30, (64, 140, 220))
    cv.circle(cx - 12, cy - 8, 10, (46, 160, 90))
    cv.circle(cx + 10, cy + 10, 12, (46, 160, 90))
    cv.circle(cx + 14, cy - 14, 6, (46, 160, 90))
    cv.line(cx - 26, cy - 26, cx - 6, cy - 6, RED, 5)
    cv.line(cx - 6, cy - 6, cx + 8, cy + 2, RED, 5)
    cv.line(cx + 8, cy + 2, cx + 26, cy + 22, RED, 5)


# ---------------------------------------------------------------- layout
def draw():
    import math  # noqa: F401  (kept for icon helpers)
    cv = Canvas(W, H, PAPER)

    # ---- masthead
    cv.fill_rect(0, 0, W, 140, NAVY)
    cv.fill_rect(0, 140, W, 5, GOLD)
    cv.text(512, 8, "THE WORLD IN ONE DAY", 2.0, WHITE, align="center")
    cv.text(512, 82, "MONDAY 23 NOVEMBER 2026", 1.25, GOLD_LT,
            align="center")

    # ---- lead story
    draw_lead_scene(cv, 24, 168, 340, 272)
    tx = 388
    cv.text(tx, 164, "UKRAINE - THE SEA WAR", 1.0, RED)
    cv.fill_rect(tx, 206, 120, 4, RED)
    cv.text(tx, 212, "UKRAINIAN DRONES", 1.6, NAVY)
    cv.text(tx, 264, "STRIKE RUSSIAN", 1.6, NAVY)
    cv.text(tx, 316, "WARSHIP OFF LIBYA", 1.6, NAVY)
    summary = ("Seven naval drones hit the corvette Merkury at Benghazi, "
               "Libya.")
    yy = 384
    for line in wrap_text(summary, 1.0, 612):
        cv.text(tx, yy, line, 1.0, INK)
        yy += 30

    rows = [
        ("RUSSIA STRIKES KYIV REGION",
         "Dymer attack kills 11; a drone hits a Kharkiv kindergarten; "
         "153 drones in one night.",
         icon_strikes),
        ("EU'S 22nd SANCTIONS PACKAGE",
         "Von der Leyen proposes cutting 60 banks from SWIFT, plus "
         "crypto and sport curbs.",
         icon_eu),
        ("DEMOCRATS WIN 258 HOUSE SEATS",
         "Democrats take at least 258 seats - a historic House "
         "majority in the midterms.",
         icon_capitol),
        ("COP31 CLIMATE TALKS COLLAPSE",
         "Fossil-fuel deadlock ends the summit with no deal.",
         icon_climate),
    ]
    y = 468
    for headline, summary, icon in rows:
        cv.fill_rect(24, y, 976, 2, (200, 192, 172))
        icon(cv, 76, y + 60, 46)
        cv.text(140, y + 12, headline, 1.25, NAVY)
        yy = y + 58
        for line in wrap_text(summary, 1.0, 860):
            cv.text(140, yy, line, 1.0, INK)
            yy += 30
        y += 120

    # ---- footer ticker
    cv.fill_rect(0, 948, W, 76, NAVY_DARK)
    cv.fill_rect(0, 948, W, 4, GOLD)
    cv.text(512, 958, "ALSO: EL CHAPO ISIDRO CAPTURED - US BLACKLISTS MEGASPEED",
            0.8, WHITE, align="center")
    cv.text(512, 986, "NIGERIA BOAT TOLL 24 - DRONE ATTACK WOUNDS 3 IN CUCUTA",
            0.8, GOLD_LT, align="center")
    return cv


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    data = draw().png_bytes()
    with open(os.path.join(outdir, "entry.png"), "wb") as f:
        f.write(data)


if __name__ == "__main__":
    main()
