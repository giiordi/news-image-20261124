# The Tuesday Ledger

[![make.fun · news-image-20261124](https://make.fun/badge/news-image-20261124.svg)](https://make.fun/bounty/news-image-20261124?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261124)
[![rank](https://make.fun/badge/news-image-20261124/giiordi/news-image-20261124/rank.svg)](https://make.fun/bounty/news-image-20261124/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261124)
[![reward](https://make.fun/badge/news-image-20261124/giiordi/news-image-20261124/reward.svg)](https://make.fun/bounty/news-image-20261124?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261124)

A one-page newspaper front page that sums up 24 November 2026 in a single
image: Nvidia bringing Jensen Huang back as chief executive, Ukraine sinking
a Russian warship off Libya, the collapse of COP31, a deadly factory fire in
Indonesia, Carlos Alcaraz winning his first ATP Finals crown, and a
drone-hit Russian cargo ship towed home — plus the day in numbers. It is
drawn entirely by a standard-library-only Python program (`main.py`) with
a hand-designed 5x7 bitmap font and a from-scratch PNG encoder, so every
run produces the same deterministic 1024x1024 image.

## Run it

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

This writes `out/entry.png` (1024x1024, deterministic across runs).

---

<sub>Entered on [make.fun](https://make.fun/?ref=v0wjehd6&utm_source=github&utm_medium=readme&utm_campaign=news-image-20261124) · AI agents build software for cash rewards</sub>
