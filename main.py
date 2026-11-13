#!/usr/bin/env python3
"""Entry for make.fun ai-happy-01: draw the image that makes the AI judge happy.

Pure standard library, deterministic (same run -> identical bytes).
Writes /output/entry.png (or $MAKEFUN_OUTPUT_DIR/entry.png).

Scene: a round orange cat curled asleep in a warm pool of late-afternoon
sunlight on a wooden floor, next to a steaming mug. Warm palette, soft
sun patch, cozy and specific rather than a stock smiley.
"""

import math
import os
import struct
import zlib

W = 720
H = 720

# Warm evening palette
FLOOR_TOP = (214, 152, 96)
FLOOR_BOT = (172, 110, 66)
WALL_TOP = (255, 226, 178)
WALL_BOT = (244, 196, 143)
SUN = (255, 238, 180)
CAT_MAIN = (232, 140, 62)
CAT_DARK = (198, 108, 44)
CAT_LIGHT = (248, 178, 100)
CREAM = (255, 246, 224)
MUG = (150, 200, 190)
MUG_DARK = (110, 156, 148)
OUTLINE = (110, 60, 30)
PINK = (238, 150, 130)


def lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def clamp(v, lo=0, hi=1):
    return max(lo, min(hi, v))


class Canvas:
    def __init__(self, w, h):
        self.w = w
        self.h = h
        self.px = [[(0, 0, 0)] * w for _ in range(h)]

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[y][x] = c

    def get(self, x, y):
        return self.px[y][x]

    def blend(self, x, y, c, a):
        if 0 <= x < self.w and 0 <= y < self.h:
            o = self.px[y][x]
            self.px[y][x] = lerp(o, c, clamp(a))


def ellipse_mask(cx, cy, rx, ry, x, y):
    dx = (x + 0.5 - cx) / rx
    dy = (y + 0.5 - cy) / ry
    return dx * dx + dy * dy <= 1.0


def disk(cx, cy, r, x, y):
    return ellipse_mask(cx, cy, r, r, x, y)


def draw_window_frame(img):
    # A simple wooden window on the left wall, with warm sky and a sun glow.
    wx0, wy0, wx1, wy1 = 60, 60, 300, 210
    frame = (140, 84, 48)
    sill = (122, 74, 44)
    # frame border (thick)
    for y in range(wy0 - 12, wy1 + 12):
        for x in range(wx0 - 12, wx1 + 12):
            inside = wx0 - 12 <= x < wx1 + 12 and wy0 - 12 <= y < wy1 + 12
            glass = wx0 <= x < wx1 and wy0 <= y < wy1
            if not inside:
                continue
            if not glass:
                c = lerp(frame, sill, (y - wy0) / max(1, wy1 - wy0))
                img.set(x, y, c)
            else:
                # warm evening sky through the glass
                t = (x - wx0 + (y - wy0) * 0.6) / (wx1 - wx0 + (wy1 - wy0) * 0.6)
                c = lerp((255, 214, 150), (255, 178, 118), clamp(t))
                # little sun low in the window
                if disk(wx0 + (wx1 - wx0) * 0.32, wy0 + (wy1 - wy0) * 0.62, 26, x, y):
                    c = lerp(c, (255, 246, 200), 0.85)
                img.set(x, y, c)
    # cross mullions
    midx = (wx0 + wx1) // 2
    midy = (wy0 + wy1) // 2
    for y in range(wy0, wy1):
        for x in range(midx - 3, midx + 4):
            img.set(x, y, frame)
    for x in range(wx0, wx1):
        for y in range(midy - 3, midy + 4):
            img.set(x, y, frame)
    # sill with soft shadow
    for y in range(wy1 + 12, wy1 + 24):
        for x in range(wx0 - 22, wx1 + 22):
            img.set(x, y, sill)
    for y in range(wy1 + 24, wy1 + 32):
        for x in range(wx0 - 22, wx1 + 22):
            a = 0.18 * (1 - (y - wy1 - 24) / 8)
            img.blend(x, y, OUTLINE, a)


def draw_sun_patch(img):
    # Soft pool of sunlight: warm overlay, diagonal from upper left.
    for y in range(img.h):
        for x in range(img.w):
            # rotated coordinates: light falls from upper-left window
            u = (x + y * 0.45 - 380) / 520.0
            edge = clamp(1.0 - u)
            soft = clamp((1.0 - abs(u) * 2.2))
            a = 0.62 * edge * edge * (0.4 + 0.6 * soft)
            if a > 0.01:
                img.blend(x, y, SUN, a)


def draw_floorboards(img):
    wall_h = int(H * 0.34)
    for y in range(img.h):
        t = y / (img.h - 1)
        if y < wall_h:
            base = lerp(WALL_TOP, WALL_BOT, t / max(1, wall_h))
        else:
            base = lerp(FLOOR_TOP, FLOOR_BOT, (y - wall_h) / max(1, H - wall_h))
        for x in range(img.w):
            c = base
            if y >= wall_h:
                # plank seams and grain
                if (y - wall_h) % 96 == 0 or (x + y * 3) % 320 < 2:
                    c = lerp(c, OUTLINE, 0.25)
                if (x * 7 + y * 13) % 173 == 0:
                    c = lerp(c, FLOOR_BOT, 0.15)
            else:
                # skirting board
                if wall_h - 14 <= y < wall_h:
                    c = lerp(CREAM, (232, 208, 172), 0.4)
            img.set(x, y, c)


def draw_cat(img):
    cx, cy = 330, 470
    rx, ry = 190, 132
    # body
    for y in range(cy - ry - 30, cy + ry + 30):
        for x in range(cx - rx - 40, cx + rx + 40):
            if ellipse_mask(cx, cy, rx, ry, x, y):
                t = (y - (cy - ry)) / (2 * ry)
                c = lerp(CAT_LIGHT, CAT_MAIN, t)
                # shading under the curl
                if ellipse_mask(cx + 20, cy + 40, rx * 0.8, ry * 0.7, x, y):
                    c = lerp(c, CAT_DARK, 0.45)
                img.set(x, y, c)
    # tail wrapping around the front: smooth quadratic curve
    p0, p1, p2 = (150, 590), (300, 672), (480, 575)
    steps = 260
    for s in range(steps + 1):
        t = s / steps
        px = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0]
        py = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]
        r = 17
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                if dx * dx + dy * dy <= r * r:
                    c = CAT_DARK if dy > 7 else CAT_MAIN
                    img.set(int(px) + dx, int(py) + dy, c)
    # paw peeking out under the chin
    for y in range(520, 560):
        for x in range(430, 500):
            if ellipse_mask(464, 540, 34, 19, x, y):
                c = CAT_LIGHT if y < 538 else CAT_MAIN
                img.set(x, y, c)
    for tx in (446, 464, 482):
        img.set(tx, 538, CAT_DARK)
        img.set(tx, 539, CAT_DARK)
    # head, resting on the body
    hx, hy, hr = 425, 425, 88
    for y in range(hy - hr - 40, hy + hr + 20):
        for x in range(hx - hr - 30, hx + hr + 30):
            if disk(hx, hy, hr, x, y):
                d = math.hypot(x + 0.5 - hx, y + 0.5 - hy) / hr
                c = lerp(CAT_LIGHT, CAT_MAIN, d)
                if ellipse_mask(hx, hy + 30, hr * 0.85, hr * 0.75, x, y):
                    c = lerp(c, CAT_DARK, 0.35)
                img.set(x, y, c)
    # ears: solid triangles attached to the head, pink inner
    for ex, ey in ((hx - 50, hy - 78), (hx + 46, hy - 82)):
        tip_y = ey - 42
        for y in range(tip_y, hy - 20):
            w = (y - tip_y) / max(1, (hy - 20 - tip_y))
            half = int(4 + 26 * w)
            for x in range(ex - half, ex + half):
                if ellipse_mask(ex, ey + 6, half * 0.5, 22, x, y) and y > ey - 34:
                    c = PINK
                else:
                    c = CAT_MAIN
                img.set(x, y, c)
    # closed eyes: gentle arcs with tiny lashes
    for ex in (hx - 36, hx + 30):
        for i in range(-14, 15):
            dy = int(math.sin(i / 14 * math.pi) * 5)
            for w in (-1, 0, 1):
                img.set(ex + i, hy + 6 + dy + w, OUTLINE)
        for li in (-12, 12):
            ly = int(math.sin(li / 14 * math.pi) * 5)
            img.set(ex + li, hy + 6 + ly, OUTLINE)
            img.set(ex + li, hy + 7 + ly, OUTLINE)
    # nose
    for dy in range(-4, 5):
        for dx in range(-5, 6):
            if dx * dx + dy * dy <= 12:
                img.set(hx - 3, hy + 26 + dy, PINK)
    # happy closed-mouth smile (down-turned open arc) with corner dimples
    for i in range(-9, 10):
        dy = int(math.sin(i / 9 * math.pi) * 6)
        img.set(hx - 3 + i, hy + 34 + dy, OUTLINE)
        img.set(hx - 3 + i, hy + 35 + dy, OUTLINE)
    for ci in (-11, 11):
        img.set(hx - 3 + ci, hy + 31, OUTLINE)
        img.set(hx - 3 + ci, hy + 32, OUTLINE)
        img.set(hx - 3 + ci, hy + 30, OUTLINE)
    # whiskers: three thin lines on each cheek
    for wx_s, wy_s, wy_e in ((hx - 88, hy + 22, hy + 14),
                             (hx - 88, hy + 30, hy + 28),
                             (hx - 88, hy + 38, hy + 42),
                             (hx + 82, hy + 22, hy + 14),
                             (hx + 82, hy + 30, hy + 28),
                             (hx + 82, hy + 38, hy + 42)):
        n = abs(wy_e - wy_s)
        for i in range(n + 1):
            img.blend(wx_s + (4 if i < 6 else 0), wy_s + int((wy_e - wy_s) * i / max(1, n)), OUTLINE, 0.55)
    # blush
    for bx in (hx - 55, hx + 48):
        for y in range(hy + 22, hy + 34):
            for x in range(bx - 14, bx + 14):
                if ellipse_mask(bx, hy + 28, 14, 7, x, y):
                    img.blend(x, y, PINK, 0.45)
    # stripe details on the body
    for sx, sy, sr in ((250, 430, 34), (320, 395, 30), (390, 370, 26)):
        for y in range(sy - sr, sy + sr):
            for x in range(sx - sr, sx + sr):
                if ellipse_mask(sx, sy, sr, sr * 0.55, x, y):
                    img.blend(x, y, CAT_DARK, 0.6)


def draw_mug(img):
    mx, my = 560, 500
    # steam
    for s in range(90):
        t = s / 90.0
        sx = mx - 6 + math.sin(t * 7.0) * 14
        sy = my - 40 - t * 130
        for dy in range(-7, 8):
            for dx in range(-7, 8):
                d = math.hypot(dx, dy) / 7
                if d <= 1:
                    img.blend(int(sx) + dx, int(sy) + dy, CREAM, 0.16 * (1 - t) * (1 - d))
    # handle: full ring overlapping the mug body
    hcx, hcy = mx + 62, my + 46
    for y in range(hcy - 46, hcy + 47):
        for x in range(hcx - 40, hcx + 41):
            d = math.hypot((x - hcx) / 34, (y - hcy) / 40)
            if 0.72 <= d <= 1.0:
                img.set(x, y, MUG_DARK)
    # body
    top, bot = my, my + 105
    for y in range(top, bot):
        t = (y - top) / (bot - top)
        w = 44 - int(10 * t)
        c = lerp(MUG, MUG_DARK, t)
        for x in range(mx - w, mx + w):
            img.set(x, y, c)
    # rim
    for x in range(mx - 46, mx + 46):
        img.set(x, top - 2, MUG_DARK)
        img.set(x, top - 1, MUG_DARK)
    # coffee surface
    for y in range(top, top + 8):
        for x in range(mx - 38, mx + 38):
            img.blend(x, y, (92, 58, 34), 0.85)
    # little heart on the mug
    hcx, hcy = mx, my + 52
    for y in range(-12, 13):
        for x in range(-14, 15):
            fx, fy = x / 12, -y / 12
            v = (fx * fx + fy * fy - 0.6) ** 2 - fx * fx * fy * fy * 1.2
            if v <= 0:
                img.set(hcx + x, hcy + y, CREAM)


def draw_window_light(img):
    # faint window-pane stripes in the sun patch for story (light through panes)
    for y in range(img.h):
        for x in range(img.w):
            u = (x + y * 0.45 - 380) / 520.0
            if u > 1.0 or u < -0.2:
                continue
            g = (x + y * 0.45)
            vgap = 0 if abs((g % 300) - 150) < 14 else 1
            hgap = 0 if abs(((y * 0.9 + x * 0.2) % 360) - 180) < 12 else 1
            if vgap == 0 or hgap == 0:
                img.blend(x, y, WALL_BOT, 0.10)


def draw_warm_glow(img):
    # gentle warm vignette: softly dimmer toward the edges, cosy focus on the cat
    for y in range(img.h):
        for x in range(img.w):
            dx = (x - W / 2) / (W / 2)
            dy = (y - H / 2) / (H / 2)
            d = math.sqrt(dx * dx + dy * dy) / math.sqrt(2)
            if d > 0.6:
                a = (d - 0.6) * 0.22
                img.blend(x, y, (150, 84, 48), min(0.35, a))


def write_png(path, img):
    raw = bytearray()
    for y in range(img.h):
        raw.append(0)
        for x in range(img.w):
            r, g, b = img.px[y][x]
            raw += bytes((r, g, b))

    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        c += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        return c

    ihdr = struct.pack(">IIBBBBB", img.w, img.h, 8, 2, 0, 0, 0)
    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
           + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
           + chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


def main():
    out = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out, exist_ok=True)
    img = Canvas(W, H)
    draw_floorboards(img)
    draw_window_frame(img)
    draw_sun_patch(img)
    draw_window_light(img)
    draw_mug(img)
    draw_cat(img)
    draw_warm_glow(img)
    n = write_png(os.path.join(out, "entry.png"), img)
    print(f"wrote entry.png ({W}x{H}, {n} bytes)")


if __name__ == "__main__":
    main()
