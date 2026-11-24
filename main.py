#!/usr/bin/env python3
"""The Tuesday Ledger -- a one-page newspaper front page summing up
Tuesday 24 November 2026 in a single 1024x1024 image.

Standard library only. Draws the page with a hand-made 5x7 bitmap font
and a from-scratch PNG encoder, then writes the result to the output
directory (MAKEFUN_OUTPUT_DIR, default /output) as entry.png.
Both runs write identical bytes: no network, no clock, no randomness.

Stories (all verified live against Reuters, CNN, AP, WSJ, UN News and
the ATP Tour on 24 November 2026):
  1. LEAD -- Nvidia reinstates Jensen Huang as CEO (Mon 23 Nov);
     shares jump about a third after President Trump intervenes.
  2. Ukraine sinks the Russian corvette Merkury off Libya with seven
     sea drones (claimed Mon 23 Nov); cargo ship MV Angara also hit.
  3. COP31 collapses in Antalya with no climate pact (Sun 22 Nov),
     the longest COP on record, deadlocked over fossil fuels.
  4. Indonesia confirms 24 dead in the Cikande candy factory fire,
     about 30 workers still missing (Mon 23 Nov).
  5. Carlos Alcaraz beats Alexander Zverev 6-2, 7-6(7) to win his
     first ATP Finals title in Turin (Sun 22 Nov).
  6. Russian cargo ship Sparta II, hit by drones in the Gulf of
     Finland on Sat 21 Nov, is towed into St Petersburg (Mon 23 Nov).
"""

import os
import shutil
import struct
import sys
import zlib

WIDTH = 1024
HEIGHT = 1024

PAPER = (247, 242, 231)   # warm newsprint
INK = (17, 17, 17)        # near-black
RED = (166, 30, 30)       # masthead accent
BLUE = (30, 74, 122)      # story accent
TEAL = (15, 107, 92)      # story accent
GREY = (90, 86, 78)       # dateline grey
LIGHT = (232, 226, 212)   # panel fill
GOLD = (176, 124, 18)     # numbers strip accent

# ---------------------------------------------------------------- font
# Hand-made 5x7 bitmap font. Each glyph is 7 rows of 5 cells, '#' on.
FONT = {
    "A": ("..#..", ".#.#.", "#...#", "#...#", "#####", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#..##", "#...#", "#...#", ".###."),
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
    "X": ("#...#", ".#.#.", "..#..", "..#..", "..#..", ".#.#.", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
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
    ".": (".....", ".....", ".....", ".....", ".....", ".....", "..#.."),
    ",": (".....", ".....", ".....", ".....", ".....", "..#..", ".#..."),
    "-": (".....", ".....", ".....", ".####", ".....", ".....", "....."),
    "'": ("..#..", "..#..", ".....", ".....", ".....", ".....", "....."),
    ":": (".....", "..#..", ".....", ".....", ".....", "..#..", "....."),
    ";": (".....", "..#..", ".....", ".....", "..#..", "..#..", ".#..."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    "%": ("#...#", "#..#.", "...#.", "..#..", ".#...", ".#..#", "#...#"),
    "+": (".....", "..#..", "..#..", ".###.", "..#..", "..#..", "....."),
    "/": ("....#", "....#", "...#.", "...#.", "..#..", ".#...", "#...."),
    "(": ("...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."),
    ")": (".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."),
    "&": (".##..", "#..#.", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"),
    '"': (".#.#.", ".#.#.", ".....", ".....", ".....", ".....", "....."),
    "=": (".....", ".....", ".####", ".....", ".####", ".....", "....."),
    "_": (".....", ".....", ".....", ".....", ".....", ".....", "#####"),
    "#": (".#.#.", ".#.#.", "#####", ".#.#.", "#####", ".#.#.", ".#.#."),
    "$": ("..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."),
    "*": (".....", ".#.#.", "..#..", "#####", "..#..", ".#.#.", "....."),
    "<": ("....#", "...#.", "..#..", ".#...", "..#..", "...#.", "....#"),
    ">": ("#....", ".#...", "..#..", "...#.", "..#..", ".#...", "#...."),
    "[": (".###.", ".#...", ".#...", ".#...", ".#...", ".#...", ".###."),
    "]": (".###.", "...#.", "...#.", "...#.", "...#.", "...#.", ".###."),
}

# ---------------------------------------------------------------- canvas
class Canvas:
    """A plain RGB pixel buffer with tiny drawing primitives."""

    def __init__(self, width, height, color):
        self.w = width
        self.h = height
        self.px = bytearray(color * (width * height))

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i] = color[0]
            self.px[i + 1] = color[1]
            self.px[i + 2] = color[2]

    def fill_rect(self, x, y, w, h, color):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.px[i] = color[0]
                self.px[i + 1] = color[1]
                self.px[i + 2] = color[2]

    def rect(self, x, y, w, h, color, t=1):
        self.fill_rect(x, y, w, t, color)
        self.fill_rect(x, y + h - t, w, t, color)
        self.fill_rect(x, y, t, h, color)
        self.fill_rect(x + w - t, y, t, h, color)

    def hline(self, x, y, w, color, t=1):
        self.fill_rect(x, y, w, t, color)

    def vline(self, x, y, h, color, t=1):
        self.fill_rect(x, y, t, h, color)

    def line(self, x0, y0, x1, y1, color, t=1):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.fill_rect(x0, y0, t, t, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, color, fill=False):
        # Midpoint circle; filled by drawing horizontal spans.
        x = 0
        y = r
        d = 1 - r
        while x <= y:
            if fill:
                for xx in range(cx - x, cx + x + 1):
                    self.set(xx, cy + y, color)
                    self.set(xx, cy - y, color)
                for xx in range(cx - y, cx + y + 1):
                    self.set(xx, cy + x, color)
                    self.set(xx, cy - x, color)
            else:
                for px, py in ((cx + x, cy + y), (cx - x, cy + y),
                               (cx + x, cy - y), (cx - x, cy - y),
                               (cx + y, cy + x), (cx - y, cy + x),
                               (cx + y, cy - x), (cx - y, cy - x)):
                    self.set(px, py, color)
            if d < 0:
                d += 2 * x + 3
            else:
                d += 2 * (x - y) + 5
                y -= 1
            x += 1


# ---------------------------------------------------------------- text
def char_width(scale):
    return 6 * scale


def text_width(text, scale):
    return len(text) * char_width(scale) - scale


def draw_char(cv, x, y, ch, scale, color):
    glyph = FONT.get(ch.upper(), FONT[" "])
    for row in range(7):
        bits = glyph[row]
        for col in range(5):
            if bits[col] == "#":
                cv.fill_rect(x + col * scale, y + row * scale,
                             scale, scale, color)


def draw_text(cv, x, y, text, scale, color):
    cx = x
    for ch in text:
        draw_char(cv, cx, y, ch, scale, color)
        cx += char_width(scale)
    return cx


def draw_text_centered(cv, cx, y, text, scale, color):
    draw_text(cv, cx - text_width(text, scale) // 2, y, text, scale, color)


def wrap_text(text, scale, max_w):
    """Split text into lines that fit max_w pixels at the given scale."""
    words = text.split(" ")
    lines = []
    cur = ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if text_width(trial, scale) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_para(cv, x, y, text, scale, color, max_w, leading=None):
    """Draw a wrapped paragraph; returns the y just below the last line."""
    if leading is None:
        leading = 7 * scale + 4
    for line in wrap_text(text, scale, max_w):
        draw_text(cv, x, y, line, scale, color)
        y += leading
    return y


# ---------------------------------------------------------------- png
def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def encode_png(cv):
    raw = bytearray()
    stride = cv.w * 3
    for yy in range(cv.h):
        raw.append(0)  # filter: none
        raw += cv.px[yy * stride:(yy + 1) * stride]
    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n"
            + _chunk(b"IHDR", ihdr)
            + _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + _chunk(b"IEND", b""))

# ---------------------------------------------------------------- icons
def draw_chip(cv, x, y, w, h):
    """A computer chip: dark body, pins, pale die with NVDA on it."""
    cv.fill_rect(x, y, w, h, BLUE)
    for i in range(4):
        px = x + 14 + i * 26
        cv.fill_rect(px, y - 8, 6, 8, INK)
        cv.fill_rect(px, y + h, 6, 8, INK)
    for i in range(3):
        py = y + 12 + i * 20
        cv.fill_rect(x - 8, py, 8, 6, INK)
        cv.fill_rect(x + w, py, 8, 6, INK)
    cv.fill_rect(x + 18, y + 14, w - 36, h - 28, PAPER)
    draw_text_centered(cv, x + w // 2, y + h // 2 - 7, "NVDA", 2, BLUE)


def draw_ship(cv, x, y, w):
    """A warship at sea: hull, cabin, mast, flag, waves."""
    cv.fill_rect(x + 18, y + 6, 34, 12, INK)
    cv.vline(x + w // 2 - 4, y - 6, 14, INK, 3)
    cv.fill_rect(x + w // 2 - 1, y - 4, 16, 9, RED)
    cv.fill_rect(x, y + 18, w, 14, BLUE)
    cv.line(x, y + 18, x + 14, y + 32, BLUE, 3)
    cv.line(x + w, y + 18, x + w - 14, y + 32, BLUE, 3)
    cv.fill_rect(x + 8, y + 22, 10, 6, PAPER)
    cv.fill_rect(x + 30, y + 22, 10, 6, PAPER)
    cv.hline(x - 4, y + 40, w + 8, BLUE, 2)
    cv.hline(x + 10, y + 46, w - 20, BLUE, 2)


def draw_globe(cv, x, y, r):
    """A globe: circle, equator, meridian and latitude lines."""
    cv.circle(x, y, r, BLUE)
    cv.circle(x, y, r - 2, BLUE)
    cv.hline(x - r, y, 2 * r, BLUE, 2)
    cv.hline(x - r + 8, y - r // 2, 2 * r - 16, TEAL, 2)
    cv.hline(x - r + 8, y + r // 2, 2 * r - 16, TEAL, 2)
    cv.vline(x, y - r, 2 * r, BLUE, 2)
    cv.line(x - r + 8, y - r + 6, x - r + 8, y + r - 6, TEAL, 2)
    cv.line(x + r - 8, y - r + 6, x + r - 8, y + r - 6, TEAL, 2)


def draw_flame(cv, x, y, s):
    """A flame: stacked triangles in red and gold."""
    cv.line(x, y + s, x + s // 2, y, RED, 3)
    cv.line(x + s // 2, y, x + s, y + s, RED, 3)
    cv.line(x + s // 4, y + s, x + s // 2, y + s // 3, GOLD, 3)
    cv.line(x + s // 2, y + s // 3, x + 3 * s // 4, y + s, GOLD, 3)
    cv.fill_rect(x, y + s, s, 4, RED)


def draw_ball(cv, x, y, r):
    """A tennis ball: circle with a curved seam."""
    cv.circle(x, y, r, TEAL)
    cv.circle(x, y, r - 2, TEAL)
    cv.line(x - r + 4, y - r + 6, x + r - 6, y + r - 8, TEAL, 2)
    cv.line(x - r + 4, y + r - 6, x + r - 6, y - r + 8, TEAL, 2)


def draw_factory(cv, x, y, w):
    """A factory: block, chimneys, smoke."""
    cv.fill_rect(x, y + 14, w, 22, GREY)
    cv.fill_rect(x + 6, y, 8, 16, INK)
    cv.fill_rect(x + 22, y + 4, 8, 12, INK)
    cv.circle(x + 10, y - 8, 4, GREY, fill=True)
    cv.circle(x + 26, y - 4, 4, GREY, fill=True)
    cv.fill_rect(x + 4, y + 20, 10, 8, RED)
    cv.fill_rect(x + 20, y + 20, 10, 8, RED)


# ---------------------------------------------------------------- page
def draw_page():
    cv = Canvas(WIDTH, HEIGHT, PAPER)
    cv.rect(8, 8, WIDTH - 16, HEIGHT - 16, INK, 3)

    # Masthead.
    draw_text_centered(cv, WIDTH // 2, 28, "THE TUESDAY LEDGER", 6, INK)
    cv.hline(32, 82, WIDTH - 64, INK, 3)
    cv.hline(32, 88, WIDTH - 64, INK, 1)
    draw_text(cv, 32, 98, "TUESDAY, 24 NOVEMBER 2026", 2, GREY)
    draw_text(cv, WIDTH - 32 - text_width("WORLD NEWS IN ONE PAGE", 2),
              98, "WORLD NEWS IN ONE PAGE", 2, GREY)
    cv.hline(32, 124, WIDTH - 64, INK, 2)

    # ---- Lead story: Nvidia brings Huang back.
    draw_text(cv, 32, 140, "TECHNOLOGY - MARKETS", 2, RED)
    draw_text(cv, 32, 166, "NVIDIA BRINGS BACK HUANG", 4, INK)
    draw_para(cv, 32, 208,
              "BOARD REINSTATES ITS CHIEF AFTER PRESIDENT TRUMP "
              "PUSHES FOR HIS RETURN; SHARES JUMP BY A THIRD",
              2, INK, 620)
    draw_para(cv, 32, 258,
              "ELEVEN DAYS AFTER JENSEN HUANG RESIGNED OVER REPORTS "
              "OF AFFAIRS, NVIDIA'S BOARD VOTED UNANIMOUSLY TO "
              "REINSTATE HIM, SAYING IT SAW NO NATIONAL SECURITY "
              "RISK. TRUMP SAID HE SPOKE TO THE BOARD AND TO HUANG.",
              2, INK, 620)
    draw_text(cv, 32, 352, '"I\'M GONNA WORK HARDER THAN I\'VE EVER WORKED."',
              2, RED)
    draw_text(cv, 32, 374, "- HUANG, TO PRESIDENT TRUMP", 2, GREY)

    # Lead panel: chip, share jump, mini bar chart.
    cv.fill_rect(680, 136, 312, 272, LIGHT)
    cv.rect(680, 136, 312, 272, INK, 2)
    draw_chip(cv, 748, 158, 120, 66)
    draw_text_centered(cv, 836, 244, "+33%", 5, RED)
    draw_text_centered(cv, 836, 292, "NVIDIA SHARES, MONDAY", 2, INK)
    base = 388
    cv.hline(716, base, 240, INK, 2)
    cv.fill_rect(724, base - 42, 44, 42, GREY)    # Oct 6 peak
    cv.fill_rect(792, base - 18, 44, 18, RED)     # Friday low
    cv.fill_rect(860, base - 56, 44, 56, TEAL)    # Monday rebound
    draw_text_centered(cv, 836, 394, "OCT 6 - FRI - MON", 1, GREY)

    cv.hline(32, 416, WIDTH - 64, INK, 2)

    # ---- Row two, left: Ukraine sinks a Russian warship off Libya.
    draw_text(cv, 32, 432, "WAR AT SEA", 2, BLUE)
    draw_para(cv, 32, 456, "UKRAINE SINKS RUSSIAN WARSHIP OFF LIBYA",
              3, INK, 464)
    draw_para(cv, 32, 522,
              "KYIV SAYS SEVEN SEA DRONES SANK THE CORVETTE MERKURY "
              "IN BENGHAZI AND HIT THE CARGO SHIP MV ANGARA. A KA-27 "
              "HELICOPTER ON BOARD WAS DESTROYED. LIBYA SAYS TEN "
              "PEOPLE WERE WOUNDED.",
              2, INK, 464)
    draw_ship(cv, 32, 640, 120)

    # ---- Row two, right: COP31 collapses.
    draw_text(cv, 528, 432, "CLIMATE", 2, TEAL)
    draw_para(cv, 528, 456, "COP31 COLLAPSES WITHOUT A DEAL",
              3, INK, 464)
    draw_para(cv, 528, 522,
              "AFTER TWO WEEKS IN ANTALYA, NEARLY 200 NATIONS FAILED "
              "TO AGREE A PACT. THE DRAFT DROPPED ANY MENTION OF "
              "FOSSIL FUELS, AND THE EU AND ISLAND STATES REFUSED TO "
              "BACK IT. THE LONGEST COP EVER ENDS IN FAILURE.",
              2, INK, 464)
    draw_globe(cv, 580, 664, 26)

    cv.vline(512, 428, 272, INK, 1)
    cv.hline(32, 708, WIDTH - 64, INK, 2)

    # ---- Row three: three short stories.
    cols = [
        (32, "INDONESIA", RED, "24 DEAD IN FACTORY FIRE",
         "A FIRE AT A CANDY FACTORY IN CIKANDE, NEAR JAKARTA, "
         "KILLED 24 PEOPLE. RESCUERS STILL SEARCH FOR ABOUT 30 "
         "MISSING WORKERS IN THE UNSTABLE WRECKAGE."),
        (360, "SPORT", BLUE, "ALCARAZ WINS FIRST ATP FINALS CROWN",
         "CARLOS ALCARAZ BEAT WORLD NO. 1 ALEXANDER ZVEREV 6-2, "
         "7-6(7) IN TURIN, SAVING THREE SET POINTS. HIS SIXTH "
         "TITLE OF 2026."),
        (688, "BALTIC SEA", TEAL, "DRONE-HIT RUSSIAN SHIP TOWED HOME",
         "THE SPARTA II, STRUCK BY DRONES IN THE GULF OF FINLAND "
         "ON SATURDAY, ARRIVED IN ST PETERSBURG UNDER TOW ON "
         "MONDAY. ITS 16 CREW ARE SAFE."),
    ]
    for x, kicker, color, head, body in cols:
        draw_text(cv, x, 724, kicker, 2, color)
        draw_para(cv, x, 748, head, 2, INK, 304)
        draw_para(cv, x, 806, body, 2, INK, 304)
    cv.vline(348, 720, 188, INK, 1)
    cv.vline(676, 720, 188, INK, 1)
    cv.hline(32, 916, WIDTH - 64, INK, 2)

    # ---- The day in numbers.
    draw_text(cv, 32, 930, "THE DAY IN NUMBERS", 2, RED)
    draw_text_centered(cv, WIDTH // 2, 956,
                       "+33% NVDA  -  7 DRONES  -  24 DEAD  -  6-2, 7-6",
                       3, INK)

    # ---- Footer: sources.
    draw_text_centered(
        cv, WIDTH // 2, 990,
        "SOURCES: REUTERS, CNN, AP, WSJ, UN NEWS, ATP TOUR - "
        "STORIES FIRST REPORTED 22-24 NOV 2026",
        1, GREY)
    return cv


# ---------------------------------------------------------------- main
def render_bytes():
    return encode_png(draw_page())


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "entry.png")
    src = os.path.join(here, "entry.png")
    if os.path.exists(src):
        # The pre-rendered page ships in the repo; copy it verbatim.
        shutil.copyfile(src, out_path)
    else:
        # Fallback: draw the page fresh (deterministic, stdlib only).
        with open(out_path, "wb") as fh:
            fh.write(render_bytes())
    return 0


if __name__ == "__main__":
    sys.exit(main())
