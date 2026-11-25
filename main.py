#!/usr/bin/env python3
"""The Tuesday Gazette - a one-page front page summing up Tuesday 24 November 2026.

Draws a light cream-paper broadsheet with a hand-built 5x7 bitmap font and a
from-scratch PNG encoder. Standard library only, no network, deterministic:
every run writes the same bytes.
"""

import hashlib
import math
import os
import struct
import zlib

W = 1024
H = 1024

PAPER = (247, 242, 231)
INK = (26, 26, 26)
RED = (163, 22, 33)
GRAY = (110, 106, 96)
PANEL = (238, 231, 214)
RULE = (26, 26, 26)

# 5x7 bitmap font. Each glyph is 7 rows of 5 cells; '#' is ink, '.' is blank.
# Uppercase letters, digits and common punctuation. Text is uppercased on draw.
FONT = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#...#", ".###."),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": (".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "#.#.#", ".#.#."),
    "X": ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": (".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", "#....", "#####"),
    "3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".##..", "..#..", ".#..."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    ";": (".....", ".##..", ".##..", ".....", ".##..", "..#..", ".#..."),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    '"': (".#.#.", ".#.#.", ".....", ".....", ".....", ".....", "....."),
    "-": (".....", ".....", ".....", ".###.", ".....", ".....", "....."),
    "(": ("...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."),
    ")": (".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."),
    "/": ("....#", "...#.", "...#.", "..#..", ".#...", ".#...", "#...."),
    "&": (".##..", "#..#.", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"),
    "%": ("##..#", "##.#.", "....#", "...#.", "..#..", ".#..#", "#..##"),
    "+": (".....", "..#..", "..#..", ".###.", "..#..", "..#..", "....."),
    "=": (".....", ".....", "#####", ".....", "#####", ".....", "....."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    "·": (".....", ".....", ".....", ".##..", ".##..", ".....", "....."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
}

BLANK = (".....", ".....", ".....", ".....", ".....", ".....", ".....")


def glyph(ch):
    return FONT.get(ch, BLANK)


def text_width(text, scale):
    return len(text) * 6 * scale - scale


def wrap_text(text, max_width, scale):
    """Greedy word wrap; returns a list of lines that fit max_width pixels."""
    words = text.split()
    if not words:
        return [""]
    lines = []
    cur = words[0]
    for word in words[1:]:
        trial = cur + " " + word
        if text_width(trial, scale) <= max_width:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    lines.append(cur)
    return lines


class Canvas:
    def __init__(self, width, height, color):
        self.w = width
        self.h = height
        self.buf = bytearray(width * height * 3)
        r, g, b = color
        row = bytes((r, g, b)) * width
        for y in range(height):
            off = y * width * 3
            self.buf[off:off + width * 3] = row

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            off = (y * self.w + x) * 3
            self.buf[off] = color[0]
            self.buf[off + 1] = color[1]
            self.buf[off + 2] = color[2]

    def rect(self, x, y, w, h, color):
        if w <= 0 or h <= 0:
            return
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        if x0 >= x1 or y0 >= y1:
            return
        row = bytes(color) * (x1 - x0)
        for yy in range(y0, y1):
            off = (yy * self.w + x0) * 3
            self.buf[off:off + (x1 - x0) * 3] = row

    def hline(self, x, y, w, color):
        self.rect(x, y, w, 1, color)

    def vline(self, x, y, h, color):
        self.rect(x, y, 1, h, color)

    def line(self, x0, y0, x1, y1, color):
        """Bresenham line, 1px wide."""
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        x, y = x0, y0
        while True:
            self.set(x, y, color)
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x += sx
            if e2 <= dx:
                err += dx
                y += sy

    def thick_line(self, x0, y0, x1, y1, width, color):
        """A thick line drawn as small squares stamped along the segment."""
        dist = math.hypot(x1 - x0, y1 - y0)
        steps = max(1, int(dist))
        half = width // 2
        for i in range(steps + 1):
            t = i / steps
            cx = int(x0 + (x1 - x0) * t)
            cy = int(y0 + (y1 - y0) * t)
            self.rect(cx - half, cy - half, width, width, color)

    def circle(self, cx, cy, r, color):
        for deg in range(360):
            a = math.radians(deg)
            self.set(int(cx + r * math.cos(a)), int(cy + r * math.sin(a)), color)

    def filled_circle(self, cx, cy, r, color):
        for dy in range(-r, r + 1):
            dx = int(math.sqrt(max(0, r * r - dy * dy)))
            self.hline(cx - dx, cy + dy, 2 * dx + 1, color)

    def ellipse(self, cx, cy, rx, ry, color):
        for deg in range(360):
            a = math.radians(deg)
            self.set(int(cx + rx * math.cos(a)), int(cy + ry * math.sin(a)), color)

    def text(self, x, y, s, scale, color):
        s = s.upper().replace("—", "-")
        cx = x
        for ch in s:
            rows = glyph(ch)
            for row in range(7):
                line = rows[row]
                for col in range(5):
                    if line[col] == "#":
                        self.rect(cx + col * scale, y + row * scale,
                                  scale, scale, color)
            cx += 6 * scale

    def text_centered(self, cx, y, s, scale, color):
        w = text_width(s.upper().replace("—", "-"), scale)
        self.text(cx - w // 2, y, s, scale, color)


def png_bytes(canvas):
    """Encode the canvas as a deterministic RGB PNG (filter 0 per row)."""
    raw = bytearray()
    for y in range(canvas.h):
        raw.append(0)
        off = y * canvas.w * 3
        raw += canvas.buf[off:off + canvas.w * 3]
    comp = zlib.compress(bytes(raw), 6)

    def chunk(kind, data):
        out = struct.pack(">I", len(data)) + kind + data
        out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", canvas.w, canvas.h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", comp)
            + chunk(b"IEND", b""))


# ---------------------------------------------------------------- layout

def draw_frame(c):
    c.rect(16, 16, W - 32, 3, RULE)
    c.rect(16, H - 19, W - 32, 3, RULE)
    c.rect(16, 16, 3, H - 32, RULE)
    c.rect(W - 19, 16, 3, H - 32, RULE)
    c.rect(26, 26, W - 52, 1, RULE)
    c.rect(26, H - 27, W - 52, 1, RULE)
    c.rect(26, 26, 1, H - 52, RULE)
    c.rect(W - 27, 26, 1, H - 52, RULE)


def draw_masthead(c):
    c.text_centered(W // 2, 44, "The Tuesday Gazette", 7, INK)
    c.text_centered(W // 2, 108,
                    "Tuesday, 24 November 2026 — Six stories from around the world",
                    2, GRAY)
    c.rect(40, 138, W - 80, 4, RULE)
    c.rect(40, 146, W - 80, 1, RULE)


def draw_gavel_scene(c):
    """Courtroom pillars, a gavel on its block and a red GUILTY stamp."""
    # Pillars at the edges of the illustration area.
    for px in (652, 928):
        c.rect(px, 190, 16, 250, INK)
        c.rect(px - 6, 182, 28, 10, INK)
        c.rect(px - 6, 438, 28, 10, INK)
    # Table line.
    c.hline(640, 448, 320, INK)
    # Gavel: head across, handle down to the block.
    c.thick_line(792, 296, 872, 356, 26, INK)
    c.thick_line(832, 326, 772, 428, 10, INK)
    # Sound block.
    c.rect(740, 428, 84, 20, INK)
    c.rect(752, 418, 60, 10, INK)
    # GUILTY stamp: red block, paper inset, thin red inner border, red text.
    c.rect(700, 196, 208, 56, RED)
    c.rect(706, 202, 196, 44, PAPER)
    c.rect(708, 204, 192, 2, RED)
    c.rect(708, 242, 192, 2, RED)
    c.rect(708, 204, 2, 40, RED)
    c.rect(898, 204, 2, 40, RED)
    c.text_centered(804, 214, "Guilty", 4, RED)


def draw_lead(c):
    c.rect(40, 162, W - 80, 306, PANEL)
    c.rect(40, 162, W - 80, 2, RULE)
    c.rect(40, 466, W - 80, 2, RULE)
    c.rect(40, 162, 2, 306, RULE)
    c.rect(W - 42, 162, 2, 306, RULE)
    c.text(64, 182, "United States · Justice", 2, RED)
    c.text(64, 212, "Huawei found guilty", 4, INK)
    c.text(64, 248, "on 10 of 12 counts", 4, INK)
    deck = ("Brooklyn jury convicts the telecom giant of bank fraud, wire "
            "fraud and sanctions violations after a 12-week trial. "
            "Acquitted on racketeering and obstruction.")
    y = 296
    for line in wrap_text(deck, 540, 2):
        c.text(64, y, line, 2, INK)
        y += 18
    c.text(64, 388, "Sentencing set for September 2027", 2, GRAY)
    draw_gavel_scene(c)


def story_block(c, x, y, w, kicker, headline, deck):
    """Draw one story; returns the y just below it."""
    c.text(x, y, kicker, 2, RED)
    y += 22
    for line in wrap_text(headline, w, 3):
        c.text(x, y, line, 3, INK)
        y += 27
    y += 6
    for line in wrap_text(deck, w, 2):
        c.text(x, y, line, 2, GRAY)
        y += 18
    return y


def draw_columns(c):
    c.rect(40, 484, W - 80, 4, RULE)
    c.rect(40, 492, W - 80, 1, RULE)
    top = 512
    bottom = 848
    # Column gutters.
    c.vline(353, top, bottom - top, GRAY)
    c.vline(675, top, bottom - top, GRAY)

    # Column 1: Yemen, then the US economy.
    y = top
    y = story_block(c, 40, y, 304, "Yemen",
                    "Houthis 60 km from Aden",
                    "Rebels advance on the interim capital as the army "
                    "holds a fortified line.")
    y += 14
    c.hline(40, y, 304, GRAY)
    y += 16
    story_block(c, 40, y, 304, "Economy",
                "U.S. confidence jumps to 103.3",
                "Highest in nearly two years, the Conference Board says.")

    # Column 2: The Hague, then Turkey.
    y = top
    y = story_block(c, 362, y, 304, "The Hague",
                    "14 nations back ICJ genocide ruling",
                    "Joint statement says Myanmar violated the Genocide "
                    "Convention over the Rohingya.")
    y += 14
    c.hline(362, y, 304, GRAY)
    y += 16
    story_block(c, 362, y, 304, "Turkey",
                "Five killed in air force crash",
                "AS-532 Cougar goes down after takeoff from Eskisehir. "
                "Cause unknown.")

    # Column 3: Colombia, then a small globe of the day.
    y = top
    y = story_block(c, 684, y, 300, "Colombia",
                    "25 held in Cartagena supermarket siege",
                    "Gunmen seize an Exito store after a failed "
                    "armored-van robbery.")
    y += 14
    c.hline(684, y, 300, GRAY)
    y += 18
    c.text_centered(834, y, "Six stories, one day", 2, RED)
    cy = y + 78
    c.circle(834, cy, 56, INK)
    c.ellipse(834, cy, 56, 20, GRAY)
    c.ellipse(834, cy, 20, 56, GRAY)
    c.hline(834 - 56, cy, 113, GRAY)
    # Dots for the six story locations.
    for dx, dy in ((-38, -14), (30, 8), (-18, -34), (6, 22),
                   (40, -26), (-44, 26)):
        c.filled_circle(834 + dx, cy + dy, 4, RED)


def draw_numbers(c):
    c.rect(40, 866, W - 80, 4, RULE)
    c.text_centered(W // 2, 882, "The day in numbers", 2, RED)
    cells = [
        ("103.3", "Confidence"),
        ("10 of 12", "Counts"),
        ("60 km", "From Aden"),
        ("25", "Hostages"),
        ("5", "Crew killed"),
        ("14", "Nations"),
    ]
    cell_w = (W - 80) // 6
    for i, (num, cap) in enumerate(cells):
        cx = 40 + cell_w * i + cell_w // 2
        c.text_centered(cx, 912, num, 3, INK)
        c.text_centered(cx, 940, cap, 2, GRAY)


def draw_footer(c):
    c.rect(40, 970, W - 80, 1, RULE)
    c.text_centered(W // 2, 982,
                    "All stories first reported Tuesday 24 November 2026",
                    2, GRAY)


def render():
    c = Canvas(W, H, PAPER)
    draw_frame(c)
    draw_masthead(c)
    draw_lead(c)
    draw_columns(c)
    draw_numbers(c)
    draw_footer(c)
    return png_bytes(c)


def main():
    data = render()
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, "entry.png"), "wb") as f:
        f.write(data)
    here = os.path.dirname(os.path.abspath(__file__))
    try:
        with open(os.path.join(here, "entry.png"), "wb") as f:
            f.write(data)
    except OSError:
        # In the grader /bot is read-only; the output copy above is enough.
        pass
    print("entry.png 1024x1024 %d bytes sha256 %s"
          % (len(data), hashlib.sha256(data).hexdigest()))


if __name__ == "__main__":
    main()
