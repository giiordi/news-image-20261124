#!/usr/bin/env python3
"""The World in Six Frames -- news-image-20261124 rebuild (resubmission).

Sums up Tuesday 24 November 2026 in one 1024x1024 PNG: a dark poster
front page with six story cards (Hormuz, Gaza, Estonia/NATO, the US
midterms, Shenzhou-24, Iraq/Kurdistan). Stdlib only: own canvas, own
5x7 bitmap font, own PNG writer. Deterministic: same bytes every run.

main() copies the committed entry.png to $MAKEFUN_OUTPUT_DIR; if the
committed image is ever missing it renders the same image from code.
"""

import os
import shutil
import struct
import zlib

W = 1024
H = 1024

# ---------------------------------------------------------------- font: 5x7
# Each glyph is 7 rows of 5 characters; '#' is ink, '.' is blank.
FONT = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
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
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "a": (".....", ".....", ".###.", "....#", ".####", "#...#", ".####"),
    "b": ("#....", "#....", "####.", "#...#", "#...#", "#...#", "####."),
    "c": (".....", ".....", ".####", "#....", "#....", "#....", ".####"),
    "d": ("....#", "....#", ".####", "#...#", "#...#", "#...#", ".####"),
    "e": (".....", ".....", ".###.", "#...#", "#####", "#....", ".###."),
    "f": ("..##.", ".#...", ".#...", "####.", ".#...", ".#...", ".#..."),
    "g": (".....", ".....", ".####", "#...#", "#...#", ".####", "....#"),
    "h": ("#....", "#....", "####.", "#...#", "#...#", "#...#", "#...#"),
    "i": ("..#..", ".....", ".##..", "..#..", "..#..", "..#..", ".###."),
    "j": (".....", "...#.", ".....", "..##.", "...#.", "...#.", "##..."),
    "k": ("#....", "#....", "#..#.", "#.#..", "##...", "#.#..", "#..#."),
    "l": (".##..", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "m": (".....", ".....", "##.#.", "#.#.#", "#.#.#", "#.#.#", "#.#.#"),
    "n": (".....", ".....", "####.", "#...#", "#...#", "#...#", "#...#"),
    "o": (".....", ".....", ".###.", "#...#", "#...#", "#...#", ".###."),
    "p": (".....", ".....", "####.", "#...#", "#...#", "####.", "#...."),
    "q": (".....", ".....", ".####", "#...#", "#...#", ".####", "....#"),
    "r": (".....", ".....", "#.##.", "##..#", "#....", "#....", "#...."),
    "s": (".....", ".....", ".####", "#....", ".###.", "....#", "####."),
    "t": (".#...", ".#...", "####.", ".#...", ".#...", ".#...", "..##."),
    "u": (".....", ".....", "#...#", "#...#", "#...#", "#...#", ".####"),
    "v": (".....", ".....", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "w": (".....", ".....", "#...#", "#...#", "#.#.#", "#.#.#", ".#.#."),
    "x": (".....", ".....", "#...#", "#...#", ".#.#.", "#...#", "#...#"),
    "y": (".....", ".....", "#...#", "#...#", "#...#", ".####", "....#"),
    "z": (".....", ".....", "#####", "...#.", "..#..", ".#...", "#####"),
    "0": (".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "...#.", "..#..", "..#..", "..#.."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".....", ".##..", ".#..."),
    ";": (".....", ".....", ".##..", ".....", ".....", ".##..", ".#..."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    '"': (".#.#.", ".#.#.", ".....", ".....", ".....", ".....", "....."),
    "-": (".....", ".....", ".....", "#####", ".....", ".....", "....."),
    "\u2013": (".....", ".....", ".....", "#####", ".....", ".....", "....."),
    "(": ("...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."),
    ")": (".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."),
    "/": ("....#", "....#", "...#.", "...#.", "..#..", ".#...", "#...."),
    "%": ("#...#", "#..#.", "...#.", "..#..", ".#...", "#..#.", "#...#"),
    "&": (".##..", "#..#.", "#..#.", ".#...", "#.#.#", "#..#.", ".##.#"),
    "+": (".....", ".....", "..#..", ".####", "..#..", ".....", "....."),
    "=": (".....", ".....", ".....", "#####", ".....", "#####", "....."),
    "\u00d7": (".....", ".....", "#...#", ".#.#.", "..#..", ".#.#.", "#...#"),
    "\u00b7": (".....", ".....", ".....", ".##..", ".##..", ".....", "....."),
    "$": ("..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."),
    "#": (".#.#.", ".#.#.", "#####", ".#.#.", "#####", ".#.#.", ".#.#."),
    "@": (".###.", "#...#", "#.###", "#.#.#", "#.###", "#....", ".###."),
    "*": (".....", ".#.#.", "..#..", "#####", "..#..", ".#.#.", "....."),
    "<": ("...#.", "..#..", ".#...", "#....", ".#...", "..#..", "...#."),
    ">": (".#...", "..#..", "...#.", "....#", "...#.", "..#..", ".#..."),
    "_": (".....", ".....", ".....", ".....", ".....", ".....", "#####"),
}

UNKNOWN = FONT["?"]


def text_width(text, scale):
    return len(text) * 6 * scale


def wrap_text(text, max_w, scale):
    """Greedy word wrap; returns a list of lines fitting max_w pixels."""
    lines = []
    for para in text.split("\n"):
        words = para.split(" ")
        cur = ""
        for word in words:
            trial = word if not cur else cur + " " + word
            if text_width(trial, scale) <= max_w:
                cur = trial
            else:
                if cur:
                    lines.append(cur)
                # hard-split an over-long single word
                while text_width(word, scale) > max_w:
                    cut = max_w // (6 * scale)
                    lines.append(word[:cut])
                    word = word[cut:]
                cur = word
        if cur:
            lines.append(cur)
    return lines


# ------------------------------------------------------------------ canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(bg * (w * h))

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(color)

    def fill_rect(self, x, y, w, h, color):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        row = bytes(color) * (x1 - x0)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.px[i:i + len(row)] = row

    def rect(self, x, y, w, h, color, t=1):
        self.fill_rect(x, y, w, t, color)
        self.fill_rect(x, y + h - t, w, t, color)
        self.fill_rect(x, y, t, h, color)
        self.fill_rect(x + w - t, y, t, h, color)

    def hline(self, x, y, w, color, t=1):
        self.fill_rect(x, y, w, t, color)

    def vline(self, x, y, h, color, t=1):
        self.fill_rect(x, y, t, h, color)

    def line(self, x0, y0, x1, y1, color):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.set(x0, y0, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, color, t=2):
        # outline circle: plot points of several concentric rings
        for rr in range(r - t + 1, r + 1):
            x = 0
            y = rr
            d = 3 - 2 * rr
            while x <= y:
                for sx, sy in ((x, y), (y, x), (-x, y), (-y, x),
                               (x, -y), (y, -x), (-x, -y), (-y, -x)):
                    self.set(cx + sx, cy + sy, color)
                if d < 0:
                    d += 4 * x + 6
                else:
                    d += 4 * (x - y) + 10
                    y -= 1
                x += 1

    def draw_text(self, x, y, text, scale, color):
        cx = x
        for ch in text:
            glyph = FONT.get(ch, UNKNOWN)
            for row in range(7):
                bits = glyph[row]
                for col in range(5):
                    if bits[col] == "#":
                        self.fill_rect(cx + col * scale, y + row * scale,
                                       scale, scale, color)
            cx += 6 * scale
        return cx

    def text_centered(self, y, text, scale, color):
        x = (self.w - text_width(text, scale)) // 2
        self.draw_text(x, y, text, scale, color)


# ----------------------------------------------------------------- content
# Six stories, all first reported on Tuesday 24 November 2026, verified
# live against Reuters / AP / BBC / Nature / Xinhua reporting.
# (kicker, accent, headline, summary, stat)
STORIES = [
    ("STRAIT OF HORMUZ", (228, 87, 46),
     "THREE MORE TANKERS HIT MINES IN HORMUZ",
     "Iran's Guards say three tankers struck mines and burned; Tehran "
     "sets seven conditions for any talks.",
     "3 TANKERS \u00b7 CLAIMS UNVERIFIED"),
    ("GAZA", (232, 185, 49),
     "ISRAELI STRIKES KILL HAMAS SECURITY CHIEF",
     "Strikes in Gaza kill Hamas security chief Naeem Abu Nahel and six "
     "others, medics and police say.",
     "7 KILLED \u00b7 TUESDAY"),
    ("EUROPE", (74, 144, 217),
     "RUSSIA WARNS ESTONIA: MOVES RISK OPEN WAR",
     "Moscow warns Tallinn its steps risk open war as NATO vows to "
     "defend against threats in space.",
     "NATO: SPACE WILL BE DEFENDED"),
    ("WASHINGTON", (127, 176, 105),
     "DEMOCRATS WIN 258 SEATS, MOST SINCE 1992",
     "A 44-seat gain gives Democrats their largest House majority since "
     "1992; the Senate flips too.",
     "258 SEATS \u00b7 LARGEST SINCE 1992"),
    ("SPACE", (155, 93, 229),
     "FIRST FOREIGN ASTRONAUT SET FOR TIANGONG",
     "Pakistan's Zeeshan Ali flies on Shenzhou-24, launching 25 Nov, the "
     "first foreigner on Tiangong.",
     "LAUNCH 25 NOV 08:18 \u00b7 LONG MARCH 2F"),
    ("BAGHDAD", (241, 91, 181),
     "IRAQ MOVES TO TAKE OVER KURDISH OILFIELDS",
     "Baghdad orders the oil ministry to run fields in Kurdish-held "
     "areas, deepening a long feud.",
     "KURDISTAN REGION \u00b7 TUESDAY"),
]

BG = (12, 22, 38)
CARD = (20, 38, 62)
CARD_BORDER = (44, 74, 107)
WHITE = (255, 255, 255)
BODY = (199, 211, 224)
MUTED = (143, 166, 189)
RED = (179, 39, 30)
GOLD = (255, 209, 102)


def render():
    cv = Canvas(W, H, BG)
    # masthead band
    cv.fill_rect(0, 0, W, 132, RED)
    cv.draw_text(28, 26, "THE WORLD IN SIX FRAMES", 4, WHITE)
    cv.draw_text(28, 92, "TUESDAY 24 NOVEMBER 2026 \u00b7 SIX STORIES THAT MOVED THE WORLD",
                 2, GOLD)
    # small globe motif at the right of the masthead
    cv.circle(938, 66, 42, GOLD, 3)
    cv.hline(896, 66, 84, GOLD, 2)
    cv.vline(938, 24, 84, GOLD, 2)
    cv.circle(938, 66, 24, GOLD, 2)

    # six cards, 2 columns x 3 rows
    cw, ch = 476, 262
    xs = (28, 520)
    ys = (156, 432, 708)
    for idx, (kicker, accent, headline, summary, stat) in enumerate(STORIES):
        x = xs[idx % 2]
        y = ys[idx // 2]
        border = GOLD if idx == 0 else CARD_BORDER
        cv.fill_rect(x, y, cw, ch, CARD)
        cv.rect(x, y, cw, ch, border, 3 if idx == 0 else 2)
        # kicker chip
        chip_w = text_width(kicker, 2) + 20
        cv.fill_rect(x + 18, y + 16, chip_w, 28, accent)
        cv.draw_text(x + 28, y + 22, kicker, 2, WHITE)
        if idx == 0:
            cv.draw_text(x + cw - 18 - text_width("LEAD", 2), y + 22,
                         "LEAD", 2, GOLD)
        # headline, up to two lines
        lines = wrap_text(headline, cw - 36, 3)[:2]
        hy = y + 58
        for ln in lines:
            cv.draw_text(x + 18, hy, ln, 3, WHITE)
            hy += 26
        # accent divider
        cv.fill_rect(x + 18, y + 118, 64, 4, accent)
        # summary, up to three lines
        slines = wrap_text(summary, cw - 36, 2)[:3]
        sy = y + 134
        for ln in slines:
            cv.draw_text(x + 18, sy, ln, 2, BODY)
            sy += 19
        # stat line
        cv.draw_text(x + 18, y + 222, stat, 2, accent)

    cv.text_centered(984, "SOURCES: REUTERS \u00b7 AP \u00b7 BBC \u00b7 NATURE \u00b7 XINHUA",
                     2, MUTED)
    return cv


def png_bytes(cv):
    raw = bytearray()
    for yy in range(cv.h):
        raw.append(0)
        raw.extend(cv.px[yy * cv.w * 3:(yy + 1) * cv.w * 3])

    def chunk(kind, data):
        out = struct.pack(">I", len(data)) + kind + data
        out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + chunk(b"IEND", b""))


def render_png():
    return png_bytes(render())


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "entry.png")
    here = os.path.dirname(os.path.abspath(__file__))
    src = os.path.join(here, "entry.png")
    if os.path.exists(src):
        shutil.copyfile(src, out_path)
    else:
        with open(out_path, "wb") as f:
            f.write(render_png())


if __name__ == "__main__":
    main()
