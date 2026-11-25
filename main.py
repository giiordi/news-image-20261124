#!/usr/bin/env python3
"""THE NIGHT DESK — dark tabloid front page summing up 24 Nov 2026 world news.

Stdlib-only renderer. Draws a 1024x1024 poster with an own Canvas class, an
own 5x7 bitmap font and an own PNG writer, then writes entry.png beside this
file and copies it into MAKEFUN_OUTPUT_DIR. Deterministic: two runs produce
byte-identical output (no randomness, no clock, no network).
"""

import math
import os
import struct
import zlib

W, H = 1024, 1024

# ---- palette (dark tabloid) ----
INK = (12, 20, 36)        # page background
PANEL = (20, 31, 54)      # lead panel background
WHITE = (240, 238, 230)   # headline text
GREY = (158, 170, 190)    # body text
FAINT = (110, 124, 148)   # footer / labels
RED = (198, 52, 40)       # accent red
REDHOT = (231, 76, 60)    # seismograph red
AMBER = (232, 179, 75)    # dateline / numbers
RULE = (42, 59, 92)       # thin rules
BAND = (122, 28, 28)      # numbers strip
MOUNT = (34, 49, 79)      # mountain silhouettes

# ---- 5x7 bitmap font (uppercase + digits + punctuation) ----
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("01110", "10000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00001", "01110"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    "*": ("00000", "10101", "01110", "11111", "01110", "10101", "00000"),
    "#": ("01010", "01010", "11111", "01010", "11111", "01010", "01010"),
    "@": ("01110", "10001", "10111", "10101", "10110", "10000", "01110"),
    "_": ("00000", "00000", "00000", "00000", "00000", "00000", "11111"),
    "·": ("00000", "00000", "00000", "01100", "01100", "00000", "00000"),
}


def text_width(s, scale):
    return len(s) * 6 * scale - scale


def wrap_lines(text, max_w, scale):
    """Greedy word wrap; returns a list of lines fitting max_w pixels."""
    words = text.upper().split(" ")
    lines, cur = [], ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if text_width(trial, scale) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


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
        for yy in range(max(0, y), min(self.h, y + h)):
            base = (yy * self.w + max(0, x)) * 3
            for xx in range(max(0, x), min(self.w, x + w)):
                self.px[base], self.px[base + 1], self.px[base + 2] = c
                base += 3

    def rect(self, x, y, w, h, c, t=1):
        self.fill_rect(x, y, w, t, c)
        self.fill_rect(x, y + h - t, w, t, c)
        self.fill_rect(x, y, t, h, c)
        self.fill_rect(x + w - t, y, t, h, c)

    def hline(self, x0, x1, y, c, t=1):
        self.fill_rect(min(x0, x1), y, abs(x1 - x0) + 1, t, c)

    def vline(self, x, y0, y1, c, t=1):
        self.fill_rect(x, min(y0, y1), t, abs(y1 - y0) + 1, c)

    def line(self, x0, y0, x1, y1, c, t=1):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            for a in range(t):
                for b in range(t):
                    self.set(x0 + a, y0 + b, c)
            if x0 == x1 and y0 == y1:
                return
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, c, t=1):
        x, y, d = 0, r, 3 - 2 * r
        while x <= y:
            for px, py in ((cx + x, cy + y), (cx - x, cy + y), (cx + x, cy - y),
                           (cx - x, cy - y), (cx + y, cy + x), (cx - y, cy + x),
                           (cx + y, cy - x), (cx - y, cy - x)):
                for a in range(t):
                    self.set(px + a, py, c)
            if d < 0:
                d += 4 * x + 6
            else:
                d += 4 * (x - y) + 10
                y -= 1
            x += 1

    def disc(self, cx, cy, r, c):
        for yy in range(cy - r, cy + r + 1):
            if abs(yy - cy) > r:
                continue
            half = int((r * r - (yy - cy) ** 2) ** 0.5)
            self.hline(cx - half, cx + half, yy, c)

    def text(self, x, y, s, scale, c):
        s = s.upper()
        cx = x
        for ch in s:
            glyph = FONT.get(ch, FONT[" "])
            for row in range(7):
                bits = glyph[row]
                for col in range(5):
                    if bits[col] == "1":
                        self.fill_rect(cx + col * scale, y + row * scale,
                                       scale, scale, c)
            cx += 6 * scale
        return cx

    def text_center(self, y, s, scale, c):
        self.text((self.w - text_width(s.upper(), scale)) // 2, y, s, scale, c)

    def para(self, x, y, text, max_w, scale, c, leading=4):
        yy = y
        for ln in wrap_lines(text, max_w, scale):
            self.text(x, yy, ln, scale, c)
            yy += 7 * scale + leading
        return yy


def write_png(path, cv):
    raw = bytearray()
    stride = cv.w * 3
    for y in range(cv.h):
        raw.append(0)
        raw += cv.px[y * stride:(y + 1) * stride]
    data = zlib.compress(bytes(raw), 9)

    def chunk(kind, payload):
        out = struct.pack(">I", len(payload)) + kind + payload
        return out + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", data)
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)


# ---- drawn icons (all primitives, no images) ----
def draw_tower(cv, x, y, s, c):
    # skyscraper: shaft, window dots, antenna, base
    w, h = 14 * s, 30 * s
    cv.fill_rect(x, y, w, h, c)
    cv.fill_rect(x - 2 * s, y + h, w + 4 * s, 2 * s, c)
    cv.line(x + w // 2, y - 6 * s, x + w // 2, y, c, 2)
    cv.disc(x + w // 2, y - 6 * s, 2 * s, REDHOT)
    for row in range(5):
        for col in range(3):
            cv.disc(x + (3 + col * 4) * s, y + (4 + row * 5) * s, s, INK)


def draw_trophy(cv, x, y, s, c):
    # cup: bowl, handles, stem, base
    cv.fill_rect(x, y, 20 * s, 4 * s, c)
    cv.fill_rect(x + 2 * s, y + 4 * s, 16 * s, 8 * s, c)
    cv.fill_rect(x + 4 * s, y + 12 * s, 12 * s, 3 * s, c)
    cv.fill_rect(x + 8 * s, y + 15 * s, 4 * s, 8 * s, c)
    cv.fill_rect(x + 3 * s, y + 23 * s, 14 * s, 3 * s, c)
    cv.circle(x - s, y + 6 * s, 4 * s, c)
    cv.circle(x + 21 * s, y + 6 * s, 4 * s, c)


def draw_burst(cv, cx, cy, r, c):
    # explosion starburst
    for k in range(12):
        a = math.pi * 2 * k / 12
        rr = r if k % 2 == 0 else r // 2
        cv.line(cx, cy, int(cx + rr * math.cos(a)),
                int(cy + rr * math.sin(a)), c, 3)
    cv.disc(cx, cy, r // 4, c)


def draw_nodes(cv, x, y, s, c):
    # AI network: three nodes joined by lines
    pts = [(x, y + 12 * s), (x + 16 * s, y), (x + 16 * s, y + 24 * s)]
    cv.line(pts[0][0], pts[0][1], pts[1][0], pts[1][1], c, 2)
    cv.line(pts[0][0], pts[0][1], pts[2][0], pts[2][1], c, 2)
    cv.line(pts[1][0], pts[1][1], pts[2][0], pts[2][1], c, 2)
    for px, py in pts:
        cv.disc(px, py, 4 * s, c)
        cv.disc(px, py, 2 * s, INK)


def draw_virus(cv, cx, cy, r, c):
    # spiked roundel
    for k in range(10):
        a = math.pi * 2 * k / 10
        cv.line(int(cx + r * 0.8 * math.cos(a)), int(cy + r * 0.8 * math.sin(a)),
                int(cx + r * 1.4 * math.cos(a)), int(cy + r * 1.4 * math.sin(a)),
                c, 3)
    cv.disc(cx, cy, r, c)
    cv.disc(cx - r // 3, cy - r // 3, r // 4, INK)
    cv.disc(cx + r // 3, cy + r // 4, r // 5, INK)


def draw_seismo(cv, x0, y0, x1, y1):
    """Jagged seismograph trace with one big spike, deterministic."""
    mid = (y0 + y1) // 2
    amps = [0, 4, -6, 8, -10, 14, -22, 34, -48, 62, -38, 20, -12, 8, -5,
            4, -3, 6, -8, 10, -6, 4, -2, 3, -4, 2, 0]
    n = len(amps)
    step = (x1 - x0) / (n - 1)
    cv.hline(x0, x1, mid, RULE, 2)
    prev = (x0, mid)
    for i, a in enumerate(amps):
        # keep the trace inside its box: clamp the spike to the panel
        py = max(y0 + 4, min(y1 - 4, mid - a))
        p = (int(x0 + i * step), py)
        cv.line(prev[0], prev[1], p[0], p[1], REDHOT, 3)
        prev = p


def render():
    cv = Canvas(W, H, INK)

    # ---- masthead ----
    cv.text_center(30, "THE NIGHT DESK", 6, WHITE)
    cv.fill_rect(36, 86, 952, 5, RED)
    cv.text_center(100, "TUESDAY, 24 NOVEMBER 2026", 2, AMBER)
    cv.hline(36, 988, 124, RULE, 2)

    # ---- lead panel: Nepal quake ----
    cv.fill_rect(36, 138, 952, 330, PANEL)
    cv.rect(36, 138, 952, 330, RULE, 2)
    cv.text(56, 156, "LEAD · NEPAL · 07:02 IST", 2, REDHOT)
    cv.text(56, 186, "THE EARTH", 5, WHITE)
    cv.text(56, 232, "MOVED AT DAWN", 5, WHITE)
    cv.para(56, 292, "A 5.3 QUAKE SHOOK KOSHI PROVINCE IN EASTERN NEPAL. "
                      "TREMORS WERE FELT ACROSS INDIA, BHUTAN, BANGLADESH "
                      "AND CHINA. NO DEATHS REPORTED.", 560, 2, GREY)
    cv.text(56, 420, "M 5.3 · DEPTH 10 KM · 27.86 N 87.91 E", 2, AMBER)
    # mountains + seismograph on the right of the panel
    for bx, bw, bh in ((648, 110, 52), (736, 130, 74), (842, 110, 58)):
        cv.line(bx, 300, bx + bw // 2, 300 - bh, MOUNT, 2)
        cv.line(bx + bw // 2, 300 - bh, bx + bw, 300, MOUNT, 2)
    draw_seismo(cv, 640, 330, 968, 440)

    # ---- grid of five stories ----
    cv.hline(36, 988, 486, RED, 3)
    cv.vline(512, 500, 880, RULE, 2)

    def story(x, y, w, kicker, head, body, icon):
        icon(x, y + 6)
        tx = x + 72
        cv.text(tx, y, kicker, 2, REDHOT)
        yy = cv.para(tx, y + 24, head, w - 72, 3, WHITE, leading=2)
        cv.para(tx, yy + 4, body, w - 72, 2, GREY, leading=3)

    story(36, 504, 456, "RIYADH", "DRONE HITS PIF TOWER",
          "SECOND STRIKE ON RIYADH'S TALLEST TOWER IN A WEEK. 11 WOUNDED.",
          lambda x, y: draw_tower(cv, x, y, 1, AMBER))
    cv.hline(36, 492, 676, RULE, 1)
    story(36, 692, 456, "SPORT · CAS", "SENEGAL CHAMPIONS AGAIN",
          "COURT OF ARBITRATION FOR SPORT REINSTATES SENEGAL AS AFCON 2025 "
          "WINNERS. THE 1-0 FINAL STANDS.",
          lambda x, y: draw_trophy(cv, x, y + 4, 1, AMBER))
    story(532, 504, 456, "COLOMBIA", "CAR BOMB WOUNDS 23",
          "BLAST OUTSIDE THE META GOVERNOR'S OFFICE IN VILLAVICENCIO. "
          "PRESIDENT BLAMES FARC DISSIDENTS.",
          lambda x, y: draw_burst(cv, x + 26, y + 26, 22, AMBER))
    cv.hline(532, 988, 624, RULE, 1)
    story(532, 640, 456, "UNITED NATIONS", "ONE YEAR TO TAME AI",
          "GUTERRES URGES STATES TO AGREE A GLOBAL AI RISK FRAMEWORK "
          "BY LATE 2027.",
          lambda x, y: draw_nodes(cv, x, y + 2, 1, AMBER))
    cv.hline(532, 988, 756, RULE, 1)
    story(532, 772, 456, "PENNSYLVANIA, USA", "MEASLES: NINTH DEATH",
          "1,638 CASES IN 46 COUNTIES. ALL NINE DEAD WERE UNVACCINATED.",
          lambda x, y: draw_virus(cv, x + 26, y + 26, 16, AMBER))

    # ---- numbers strip ----
    cv.fill_rect(36, 896, 952, 76, BAND)
    cv.text_center(906, "THE DAY IN NUMBERS", 2, AMBER)
    nums = [("5.3", "NEPAL MAGNITUDE"), ("11", "WOUNDED IN RIYADH"),
            ("23", "INJURED IN COLOMBIA"), ("1,638", "MEASLES CASES"),
            ("46", "COUNTIES HIT")]
    slot = 952 // 5
    for i, (num, label) in enumerate(nums):
        cx = 36 + slot * i + slot // 2
        cv.text(cx - text_width(num, 3) // 2, 928, num, 3, WHITE)
        cv.text(cx - text_width(label, 1) // 2, 954, label, 1, (232, 200, 160))

    # ---- footer ----
    cv.text_center(986, "TUESDAY 24 NOVEMBER 2026 · SIX STORIES, ONE DAY", 1, FAINT)
    return cv


def main():
    cv = render()
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    write_png(os.path.join(out_dir, "entry.png"), cv)
    here = os.path.dirname(os.path.abspath(__file__))
    try:
        write_png(os.path.join(here, "entry.png"), cv)
    except OSError:
        pass


if __name__ == "__main__":
    main()
