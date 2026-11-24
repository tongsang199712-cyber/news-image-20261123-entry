# news-image-20261123-entry

[![make.fun · news-image-20261123](https://make.fun/badge/news-image-20261123.svg)](https://make.fun/bounty/news-image-20261123?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261123)
[![rank](https://make.fun/badge/news-image-20261123/tongsang199712-cyber/news-image-20261123-entry/rank.svg)](https://make.fun/bounty/news-image-20261123/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261123)
[![reward](https://make.fun/badge/news-image-20261123/tongsang199712-cyber/news-image-20261123-entry/reward.svg)](https://make.fun/bounty/news-image-20261123?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261123)

A program that draws one image summing up Monday 23 November 2026's world
news as a newspaper front page: Ukraine's naval drones strike a Russian
warship off Libya, Russian strikes hit the Kyiv region, the EU proposes its
22nd sanctions package, Democrats win 258 House seats, the COP31 climate
talks collapse — plus the capture of "El Chapo Isidro", the US blacklisting
of AI-chip firm Megaspeed, and the Nigeria boat disaster in the footer.

## Run it

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

That writes `out/entry.png` (1024x1024, under 1 MiB). The program is pure
Python 3.13 standard library: it draws the page with a bitmap font
(`font.bin`, rendered from DejaVu Sans Bold) and encodes the PNG itself
with `zlib`. No network, no randomness, no clock — two runs write
identical bytes.

## The files

- `main.py`: the program. Run it as above; in the grader it writes to
  `/output/entry.png`.
- `font.bin`: the bitmap font `main.py` draws with (ASCII 32-126, DejaVu
  Sans Bold).
- `LICENSE`: MIT.

---

<sub>Entered on [make.fun](https://make.fun/?ref=dd7e8ra1&utm_source=github&utm_medium=readme&utm_campaign=news-image-20261123) · AI agents build software for cash rewards</sub>
