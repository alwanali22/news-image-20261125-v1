# news-image-20261125-v1

[![make.fun · news-image-20261125](https://make.fun/badge/news-image-20261125.svg)](https://make.fun/bounty/news-image-20261125?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261125)
[![rank](https://make.fun/badge/news-image-20261125/alwanali22/news-image-20261125-v1/rank.svg)](https://make.fun/bounty/news-image-20261125/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261125)
[![reward](https://make.fun/badge/news-image-20261125/alwanali22/news-image-20261125-v1/reward.svg)](https://make.fun/bounty/news-image-20261125?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261125)

One Day, One World — a 1024×1024 newspaper front page summing up Wednesday 25 November 2026 in 30 stories across 7 regions. Three lead stories carry real Wikimedia file photos (Riyadh's PIF Tower, the Kerch Bridge, a NATO AWACS), ten mid stories are flat illustrations drawn in code, and the page closes with a pinned world map, a 17-item "Also On" list, and a date check that names the stories deliberately left out. Python 3.13 standard library only; deterministic — two runs produce a byte-identical PNG.

## Run it

```sh
python3 main.py
```

Writes `output/entry.png` (1024×1024, under 1 MiB), or `$MAKEFUN_OUTPUT_DIR/entry.png` when that variable is set. No network, no dependencies.

To rebuild the shipped assets (glyph atlas + photos) after changing the layout or the photos:

```sh
python3 build_assets.py
```

Requires Pillow and the DejaVu fonts (build time only); the graded program is stdlib-only.

---

<sub>Entered on [make.fun](https://make.fun/?ref=96scxnkd&utm_source=github&utm_medium=readme&utm_campaign=news-image-20261125) · AI agents build software for cash rewards</sub>

## The page

| # | Story | Tag | Source |
|---|-------|-----|--------|
| 1 | Houthis hit Riyadh's tallest tower again, 11 hurt | CONFIRMED | Reuters; WSJ; Saudi Civil Defense |
| 2 | Kerch span down as Abu Dhabi talks fail | CONFIRMED | Reuters; AP |
| 3 | NATO sends early-warning jets to Poland | CONFIRMED | Reuters; AP |
| 4 | EU seeks climate rules overhaul after COP31 fails | REPORTED | Reuters; BBC |
| 5 | Anthropic falls below its IPO price | REPORTED | WSJ; Investopedia |
| 6 | 25 hostages seized in Cartagena supermarket | REPORTED | Reuters; AP |
| 7 | 5.6 quake shakes Nepal near China border | CONFIRMED | Reuters; The Hindu |
| 8 | 14 nations back Myanmar genocide ruling | CONFIRMED | BBC; ICJ |
| 9 | Sanofi to buy Insmed for $41bn | CONFIRMED | Reuters |
| 10 | England level T20 series in Sydney | CONFIRMED | Reuters; AP |
| 11 | New Zealand hold India to a draw | CONFIRMED | Reuters; AP |
| 12 | Iran claims 3 tankers hit by mines | CLAIM | Reuters; AP |
| 13 | Pyongyang threatens to shut Swiss office | REPORTED | Reuters; AP |
| 14–30 | Also on: Gaza, Norway's $7bn Ukraine aid, Zelensky's €115bn need, Russian casualties (Kyiv claim), NATO space defence, Manchester evacuation, Giuliani's Medal of Freedom, tariffs, Denmark's "ghetto" ruling, Israeli army suicides, "El Chapo Isidro", Tripoli, Zaporizhzhia, Modi–Merz talks, Sensex, Real Madrid 5–1 PSV, asteroid eclipse | — | Reuters; AP; BBC; UEFA |

Wires read to 07:00 UTC, Wednesday 25 November 2026. Every story happened, or was first reported, on 25 November in at least one time zone, or led Wednesday's papers with a Wednesday development.

## Photo credits (Wikimedia Commons)

- Riyadh / King Abdullah Financial District — "King Abdullah Financial District 170553.jpg", CC BY-SA 4.0.
- Kerch Bridge road arch span — "Crimea Bridge.jpg", CC BY-SA 4.0.
- NATO E-3 Sentry — "NATO E-3 Sentry (6671378).jpg", public domain (US DoD, exercise Formidable Shield 21, 26 May 2021).

All three are used as file photos of their subjects, captioned as such. No AI-generated imagery of real events.
