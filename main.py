#!/usr/bin/env python3
"""news-image-20261125: draw one front-page image summing up Wednesday 25 November 2026.

Standard library only. Writes entry.png to /output (or $MAKEFUN_OUTPUT_DIR).
Deterministic: the same bytes on every run, no network, no time, no randomness.
"""
import os
import struct
import zlib

W, H = 1024, 1024

# 5x7 pixel font: each glyph is 7 rows, each row a 5-bit value (bit 4 = left pixel).
FONT = {
    'A': (0x0E, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    'B': (0x1E, 0x11, 0x11, 0x1E, 0x11, 0x11, 0x1E),
    'C': (0x0E, 0x11, 0x10, 0x10, 0x10, 0x11, 0x0E),
    'D': (0x1E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x1E),
    'E': (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x1F),
    'F': (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x10),
    'G': (0x0E, 0x11, 0x10, 0x17, 0x11, 0x11, 0x0F),
    'H': (0x11, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    'I': (0x0E, 0x04, 0x04, 0x04, 0x04, 0x04, 0x0E),
    'J': (0x07, 0x02, 0x02, 0x02, 0x02, 0x12, 0x0C),
    'K': (0x11, 0x12, 0x14, 0x18, 0x14, 0x12, 0x11),
    'L': (0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x1F),
    'M': (0x11, 0x1B, 0x15, 0x15, 0x11, 0x11, 0x11),
    'N': (0x11, 0x19, 0x15, 0x13, 0x11, 0x11, 0x11),
    'O': (0x0E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    'P': (0x1E, 0x11, 0x11, 0x1E, 0x10, 0x10, 0x10),
    'Q': (0x0E, 0x11, 0x11, 0x11, 0x15, 0x12, 0x0D),
    'R': (0x1E, 0x11, 0x11, 0x1E, 0x14, 0x12, 0x11),
    'S': (0x0F, 0x10, 0x10, 0x0E, 0x01, 0x01, 0x1E),
    'T': (0x1F, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04),
    'U': (0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    'V': (0x11, 0x11, 0x11, 0x11, 0x11, 0x0A, 0x04),
    'W': (0x11, 0x11, 0x11, 0x15, 0x15, 0x1B, 0x11),
    'X': (0x11, 0x11, 0x0A, 0x04, 0x0A, 0x11, 0x11),
    'Y': (0x11, 0x11, 0x0A, 0x04, 0x04, 0x04, 0x04),
    'Z': (0x1F, 0x01, 0x02, 0x04, 0x08, 0x10, 0x1F),
    '0': (0x0E, 0x11, 0x13, 0x15, 0x19, 0x11, 0x0E),
    '1': (0x04, 0x0C, 0x04, 0x04, 0x04, 0x04, 0x0E),
    '2': (0x0E, 0x11, 0x01, 0x02, 0x04, 0x08, 0x1F),
    '3': (0x1F, 0x02, 0x04, 0x02, 0x01, 0x11, 0x0E),
    '4': (0x02, 0x06, 0x0A, 0x12, 0x1F, 0x02, 0x02),
    '5': (0x1F, 0x10, 0x1E, 0x01, 0x01, 0x11, 0x0E),
    '6': (0x06, 0x08, 0x10, 0x1E, 0x11, 0x11, 0x0E),
    '7': (0x1F, 0x01, 0x02, 0x04, 0x08, 0x08, 0x08),
    '8': (0x0E, 0x11, 0x11, 0x0E, 0x11, 0x11, 0x0E),
    '9': (0x0E, 0x11, 0x11, 0x0F, 0x01, 0x02, 0x0C),
    ' ': (0, 0, 0, 0, 0, 0, 0),
    '.': (0, 0, 0, 0, 0, 0x0C, 0x0C),
    ',': (0, 0, 0, 0, 0x0C, 0x04, 0x08),
    ':': (0, 0x0C, 0x0C, 0, 0x0C, 0x0C, 0),
    ';': (0, 0x0C, 0x0C, 0, 0x0C, 0x04, 0x08),
    '!': (0x04, 0x04, 0x04, 0x04, 0x04, 0, 0x04),
    '?': (0x0E, 0x11, 0x01, 0x02, 0x04, 0, 0x04),
    "'": (0x04, 0x04, 0x08, 0, 0, 0, 0),
    '"': (0x0A, 0x0A, 0x0A, 0, 0, 0, 0),
    '-': (0, 0, 0, 0x1F, 0, 0, 0),
    '/': (0x01, 0x01, 0x02, 0x04, 0x08, 0x10, 0x10),
    '%': (0x19, 0x19, 0x02, 0x04, 0x08, 0x13, 0x13),
    '&': (0x0C, 0x12, 0x14, 0x08, 0x15, 0x12, 0x0D),
    '+': (0, 0x04, 0x04, 0x1F, 0x04, 0x04, 0),
    '=': (0, 0, 0x1F, 0, 0x1F, 0, 0),
    '*': (0, 0x04, 0x15, 0x0E, 0x15, 0x04, 0),
    '#': (0x0A, 0x0A, 0x1F, 0x0A, 0x1F, 0x0A, 0x0A),
    '(': (0x02, 0x04, 0x08, 0x08, 0x08, 0x04, 0x02),
    ')': (0x08, 0x04, 0x02, 0x02, 0x02, 0x04, 0x08),
    '@': (0x0E, 0x11, 0x17, 0x15, 0x16, 0x10, 0x0E),
    '_': (0, 0, 0, 0, 0, 0, 0x1F),
}


def _chunk(kind, data):
    return struct.pack('>I', len(data)) + kind + data + struct.pack(
        '>I', zlib.crc32(kind + data) & 0xFFFFFFFF)


def png_bytes(rgb, w, h):
    """Encode raw RGB bytes as a PNG (filter 0 on every scanline)."""
    raw = bytearray()
    stride = w * 3
    for y in range(h):
        raw.append(0)
        raw += rgb[y * stride:(y + 1) * stride]
    ihdr = struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)
    return (b'\x89PNG\r\n\x1a\n' + _chunk(b'IHDR', ihdr)
            + _chunk(b'IDAT', zlib.compress(bytes(raw), 9))
            + _chunk(b'IEND', b''))


class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bg * (w * h))

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = c

    def rect(self, x, y, w, h, c):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.set(xx, yy, c)

    def outline(self, x, y, w, h, c, t=1):
        self.rect(x, y, w, t, c)
        self.rect(x, y + h - t, w, t, c)
        self.rect(x, y, t, h, c)
        self.rect(x + w - t, y, t, h, c)

    def disc(self, cx, cy, r, c):
        for dy in range(-r, r + 1):
            dx = int((r * r - dy * dy) ** 0.5)
            for xx in range(cx - dx, cx + dx + 1):
                self.set(xx, cy + dy, c)

    def ring(self, cx, cy, r, c, t=2):
        for a in range(360):
            import math
            x = int(cx + r * math.cos(math.radians(a)) + 0.5)
            y = int(cy + r * math.sin(math.radians(a)) + 0.5)
            for dy in range(-(t // 2), t // 2 + 1):
                for dx in range(-(t // 2), t // 2 + 1):
                    self.set(x + dx, y + dy, c)

    def line(self, x0, y0, x1, y1, c, t=1):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            for a in range(-(t // 2), t // 2 + 1):
                for b in range(-(t // 2), t // 2 + 1):
                    self.set(x0 + a, y0 + b, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def triangle(self, p0, p1, p2, c):
        xs = [p0[0], p1[0], p2[0]]
        ys = [p0[1], p1[1], p2[1]]
        for yy in range(min(ys), max(ys) + 1):
            spans = []
            for (ax, ay), (bx, by) in ((p0, p1), (p1, p2), (p2, p0)):
                if ay == by:
                    continue
                if min(ay, by) <= yy < max(ay, by) or yy == max(ys):
                    t = (yy - ay) / (by - ay)
                    spans.append(ax + t * (bx - ax))
            if len(spans) >= 2:
                for xx in range(int(min(spans)), int(max(spans)) + 1):
                    self.set(xx, yy, c)

    def text(self, s, x, y, scale, c, align='left'):
        adv = 6 * scale
        if align == 'center':
            x -= len(s) * adv // 2
        elif align == 'right':
            x -= len(s) * adv
        cx = x
        for ch in s:
            glyph = FONT.get(ch.upper(), FONT[' '])
            for row in range(7):
                bits = glyph[row]
                for col in range(5):
                    if bits & (1 << (4 - col)):
                        self.rect(cx + col * scale, y + row * scale,
                                  scale, scale, c)
            cx += adv
        return cx

    def text_width(self, s, scale):
        return len(s) * 6 * scale


def wrap(text, max_chars):
    """Greedy word wrap into lines of at most max_chars characters."""
    lines, cur = [], ''
    for word in text.split(' '):
        if cur and len(cur) + 1 + len(word) > max_chars:
            lines.append(cur)
            cur = word
        else:
            cur = cur + ' ' + word if cur else word
    if cur:
        lines.append(cur)
    return lines


# ---- colours ----
PAPER = bytes((247, 242, 231))
WHITE = bytes((255, 255, 255))
INK = bytes((26, 26, 26))
NAVY = bytes((20, 38, 76))
GOLD = bytes((217, 164, 65))
GOLD_DK = bytes((176, 128, 32))
RED = bytes((179, 55, 46))
BLUE = bytes((46, 94, 140))
TEAL = bytes((31, 122, 109))
GREEN = bytes((47, 107, 79))
PURPLE = bytes((107, 78, 142))
ORANGE = bytes((201, 106, 30))
SKY = bytes((214, 232, 244))
SEA = bytes((64, 120, 168))
GREY = bytes((201, 194, 176))
BROWN = bytes((122, 82, 42))
YELLOW = bytes((240, 196, 66))


def burst(cv, cx, cy, r, c):
    """Starburst: radiating lines + centre disc."""
    import math
    for k in range(12):
        a = math.radians(k * 30)
        cv.line(cx, cy, int(cx + r * math.cos(a)), int(cy + r * math.sin(a)), c, 3)
    cv.disc(cx, cy, r // 3, c)


def pic_rocket(cv, bx, by, bw, bh):
    cv.rect(bx, by, bw, bh, SKY)
    for sx, sy in ((bx + 12, by + 12), (bx + bw - 14, by + 20), (bx + 30, by + 44),
                   (bx + bw - 26, by + 52), (bx + 18, by + 66)):
        cv.rect(sx, sy, 3, 3, WHITE)
    cx = bx + bw // 2
    cv.triangle((cx - 13, by + 34), (cx + 13, by + 34), (cx, by + 12), RED)
    cv.rect(cx - 13, by + 34, 26, 44, WHITE)
    cv.outline(cx - 13, by + 34, 26, 44, INK, 2)
    cv.disc(cx, by + 50, 7, BLUE)
    cv.disc(cx, by + 50, 3, SKY)
    cv.triangle((cx - 13, by + 62), (cx - 26, by + 82), (cx - 13, by + 78), RED)
    cv.triangle((cx + 13, by + 62), (cx + 26, by + 82), (cx + 13, by + 78), RED)
    cv.triangle((cx - 9, by + 78), (cx + 9, by + 78), (cx, by + 104), ORANGE)
    cv.triangle((cx - 5, by + 78), (cx + 5, by + 78), (cx, by + 96), YELLOW)


def pic_ship(cv, bx, by, bw, bh):
    cv.rect(bx, by, bw, bh, SKY)
    cv.rect(bx, by + 78, bw, bh - 78, SEA)
    cv.line(bx + 8, by + 88, bx + 40, by + 84, WHITE, 2)
    cv.line(bx + 60, by + 92, bx + 110, by + 86, WHITE, 2)
    cv.line(bx + 100, by + 96, bx + 140, by + 92, WHITE, 2)
    cx = bx + bw // 2
    cv.rect(cx - 52, by + 58, 104, 20, INK)
    cv.triangle((cx + 52, by + 58), (cx + 66, by + 66), (cx + 52, by + 78), INK)
    cv.line(cx - 8, by + 58, cx - 8, by + 26, INK, 3)
    cv.rect(cx - 26, by + 30, 36, 10, RED)
    burst(cv, cx + 44, by + 26, 20, ORANGE)
    burst(cv, cx + 44, by + 26, 10, YELLOW)


def pic_tower(cv, bx, by, bw, bh):
    cv.rect(bx, by, bw, bh, SKY)
    cx = bx + bw // 2 - 10
    cv.rect(cx, by + 34, 46, 84, NAVY)
    cv.rect(cx + 8, by + 16, 30, 18, NAVY)
    cv.line(cx + 23, by + 16, cx + 23, by + 4, INK, 2)
    cv.disc(cx + 23, by + 4, 3, RED)
    for r in range(4):
        for col in range(3):
            cv.rect(cx + 7 + col * 13, by + 42 + r * 18, 7, 9, GOLD)
    cv.rect(bx + 96, by + 18, 26, 8, INK)
    cv.line(bx + 102, by + 18, bx + 96, by + 10, INK, 2)
    cv.line(bx + 116, by + 18, bx + 122, by + 10, INK, 2)
    cv.line(bx + 109, by + 18, bx + 109, by + 8, INK, 2)
    burst(cv, bx + 118, by + 34, 14, ORANGE)


def pic_radar(cv, bx, by, bw, bh):
    cv.rect(bx, by, bw, bh, bytes((224, 238, 226)))
    cx, cy = bx + bw // 2, by + bh // 2 + 8
    cv.ring(cx, cy, 46, GREEN, 2)
    cv.ring(cx, cy, 30, GREEN, 2)
    cv.ring(cx, cy, 14, GREEN, 2)
    cv.line(cx, cy, cx + 34, cy - 30, GREEN, 2)
    cv.disc(cx, cy, 4, GREEN)
    px, py = bx + 34, by + 26
    cv.rect(px, py + 6, 52, 10, NAVY)
    cv.triangle((px + 52, py + 6), (px + 70, py + 11), (px + 52, py + 16), NAVY)
    cv.triangle((px + 10, py + 6), (px + 22, py - 8), (px + 30, py + 6), NAVY)
    cv.triangle((px + 34, py + 16), (px + 44, py + 28), (px + 48, py + 16), NAVY)
    cv.triangle((px, py + 6), (px - 8, py + 2), (px, py + 16), NAVY)


def pic_chart(cv, bx, by, bw, bh):
    cv.rect(bx, by, bw, bh, WHITE)
    cv.line(bx + 14, by + 12, bx + 14, by + bh - 16, INK, 2)
    cv.line(bx + 14, by + bh - 16, bx + bw - 10, by + bh - 16, INK, 2)
    pts = [(bx + 20, by + 26), (bx + 48, by + 34), (bx + 76, by + 30),
           (bx + 104, by + 58), (bx + 128, by + 84)]
    for a, b in zip(pts, pts[1:]):
        cv.line(a[0], a[1], b[0], b[1], RED, 4)
    for p in pts:
        cv.disc(p[0], p[1], 4, RED)
    cv.triangle((bx + 128, by + 84), (bx + 112, by + 78), (bx + 122, by + 96), RED)
    cv.text('-1.5%', bx + 22, by + 92, 2, RED)


def pic_turkey(cv, bx, by, bw, bh):
    cv.rect(bx, by, bw, bh, bytes((250, 238, 214)))
    cx, cy = bx + bw // 2, by + bh // 2 + 14
    for k, ang in enumerate((-50, -25, 0, 25, 50)):
        import math
        a = math.radians(270 + ang)
        cv.line(cx, cy - 6, int(cx + 46 * math.cos(a)), int(cy - 6 + 46 * math.sin(a)),
                BROWN, 4)
    cv.disc(cx, cy, 26, BROWN)
    cv.disc(cx + 4, cy - 30, 12, BROWN)
    cv.triangle((cx + 14, cy - 32), (cx + 26, cy - 28), (cx + 14, cy - 24), ORANGE)
    cv.disc(cx + 8, cy - 33, 2, INK)
    cv.disc(cx + 22, cy - 16, 8, bytes((150, 60, 50)))
    cv.line(cx - 8, cy + 24, cx - 8, cy + 40, ORANGE, 3)
    cv.line(cx + 8, cy + 24, cx + 8, cy + 40, ORANGE, 3)


PANELS = [
    dict(tag='SPACE', color=NAVY, pic=pic_rocket,
         head="PAKISTAN'S FIRST ASTRONAUT REACHES ORBIT ON SHENZHOU-24",
         sub="Zeeshan Ali flies to Tiangong, first foreign visitor to China's station."),
    dict(tag='UKRAINE', color=BLUE, pic=pic_ship,
         head='KYIV CONFIRMS HIT ON RUSSIAN SHIP IN GULF OF FINLAND',
         sub='Zelenskiy owns the drone strike; ally Norway urges caution.'),
    dict(tag='MIDDLE EAST', color=RED, pic=pic_tower,
         head="DRONE HITS RIYADH'S TALLEST TOWER, 11 WOUNDED",
         sub='Houthi strike on the PIF Tower; Saudi civil defence reports injuries.'),
    dict(tag='EUROPE', color=TEAL, pic=pic_radar,
         head='NATO TO DEPLOY EARLY-WARNING JETS IN POLAND',
         sub='Alliance bolsters its eastern flank after a missile scare.'),
    dict(tag='MARKETS', color=PURPLE, pic=pic_chart,
         head='TARIFF FEARS SINK CHIP STOCKS, NASDAQ -1.5%',
         sub='Nvidia -6%, Micron -11% as the US weighs hikes on China, the EU and 14 more.'),
    dict(tag='USA', color=ORANGE, pic=pic_turkey,
         head='TRUMP PARDONS TURKEYS FREEDOM AND FEATHERS',
         sub='Thanksgiving eve ceremony at the White House.'),
]


# ---- layout ----
def draw_panel(cv, x, y, w, h, panel):
    cv.rect(x, y, w, h, WHITE)
    cv.outline(x, y, w, h, GREY, 2)
    cv.rect(x, y, w, 34, panel['color'])
    cv.text(panel['tag'], x + 14, y + 10, 2, WHITE)
    lines = wrap(panel['head'], 24)
    ly = y + 46
    for ln in lines[:3]:
        cv.text(ln, x + 14, ly, 3, INK)
        ly += 26
    div_y = ly + 8
    cv.rect(x + 14, div_y, w - 28, 3, GOLD)
    zone_top = div_y + 12
    zone_bot = y + h - 14
    for i, ln in enumerate(wrap(panel['sub'], 24)[:5]):
        cv.text(ln, x + 14, zone_top + i * 18, 2, bytes((64, 64, 64)))
    pic_x, pic_w = x + w - 164, 150
    panel['pic'](cv, pic_x, zone_top, pic_w, zone_bot - zone_top)


def build():
    cv = Canvas(W, H, PAPER)
    # Masthead
    cv.rect(0, 0, W, 116, NAVY)
    cv.text('THE WORLD IN ONE PAGE', W // 2, 16, 5, WHITE, align='center')
    # centre the title: text() with align='center' treats x as centre
    cv.text('WEDNESDAY 25 NOVEMBER 2026', W // 2, 66, 3, GOLD, align='center')
    # Ribbon: the day's observance
    cv.rect(0, 116, W, 28, GOLD)
    cv.text('ALSO TODAY: INTERNATIONAL DAY FOR THE ELIMINATION OF VIOLENCE AGAINST WOMEN',
            W // 2, 124, 2, NAVY, align='center')
    # Grid of six stories
    pw, ph, gap, mx = 494, 268, 12, 12
    for i, panel in enumerate(PANELS):
        px = mx + (i % 2) * (pw + gap)
        py = 156 + (i // 2) * (ph + gap)
        draw_panel(cv, px, py, pw, ph, panel)
    # Footer
    cv.text('SIX STORIES FROM ONE DAY - WEDNESDAY 25 NOVEMBER 2026',
            W // 2, 994, 2, bytes((90, 84, 70)), align='center')
    return png_bytes(bytes(cv.px), W, H)


def main():
    out_dir = os.environ.get('MAKEFUN_OUTPUT_DIR', '/output')
    os.makedirs(out_dir, exist_ok=True)
    data = build()
    with open(os.path.join(out_dir, 'entry.png'), 'wb') as f:
        f.write(data)


if __name__ == '__main__':
    main()
