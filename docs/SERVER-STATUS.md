# Server status — WORKING as of 2026-07-28

The server runs and is registered with Claude Code. Verified end to end over the real MCP
stdio protocol against the live IKEA Israel site.

```
tools advertised: ['get_sale_items', 'check_product']
get_sale_items(category_url='sofas-armchairs', limit=100) -> count=100  total_available=126
  first item: BÅRSLÖV @ 2,795 ILS
check_product(<that url>) -> status=Available  price=2795.0
  listing 2795.0 == product page 2795.0
All checks passed.
```

Reproduce with `.venv\Scripts\python.exe tests\test_server_flow.py` (needs network, ~30s).

## What the server does now

Two data tools, no LLM work of its own, no API key:

| Tool | Purpose |
|---|---|
| `get_sale_items(category=None, limit=50, category_url=None, max_items=200)` | Scrape an IKEA Israel offers page, paginating through "הצג עוד" until `max_items`. Returns JSON with name, description, `price` (payable), `price_before` (struck-out original), `discount`, image_url, product_url. Optional free-text category filter. Cached per `(category, category_url, max_items)` for the process lifetime — a paginated scrape takes ~40s. |
| `check_product(url)` | Live price and availability for one product URL. A redirect to a category page means the item is gone. |

The client's own model does the styling, matching and recommending from the returned data.

## How the four blockers were fixed

### 1. Import failure — fixed by removing the cause

`from mcp.types import UserMessage` never existed as a valid import. Rather than patch it to
`SamplingMessage`, `server.py` was rewritten without sampling, so the offending import is gone
entirely.

### 2. MCP Sampling — dropped

Both tools previously called `ctx.session.create_message`, delegating generation to the client.
That was chosen (transcript msgs 9–12) so the client would pay for generation rather than a
hardcoded Gemini key. Dropping it **preserves that goal** — the client's model still does the
work, just directly, without a protocol round-trip that Claude Code appears not to support.

`analyze_room_style` was deleted. Claude and Antigravity both read room photos natively; a tool
that asks the client to look at an image the client can already see added a hop and a failure
mode for nothing. Attach the photo to the conversation instead, then ask for sale items.

### 3. Dead venv — rebuilt

The old `.venv` pointed at a nonexistent Python and had been copied from `Downloads\telegram-bot`.
Rebuilt against the Store **Python 3.13.14** on PATH, with a new `requirements.txt`
(mcp 1.28.1, playwright 1.61.0, markdown, xhtml2pdf, pytest, requests) plus
`playwright install chromium`.

The old one is kept at `.venv.broken-from-telegram-bot/` (319 MB, gitignored). Safe to delete
whenever you like — nothing references it.

### 4. Not registered — done

Registered at **user scope**, so it works from any directory:

```
claude mcp add ikea-designer --scope user -- \
  C:\Users\tomye\Projects\ikea-mcp-server\.venv\Scripts\python.exe \
  C:\Users\tomye\Projects\ikea-mcp-server\server.py
```

`claude mcp list` reports `ikea-designer: ... - √ Connected`. Remove with
`claude mcp remove ikea-designer --scope user`.

For **Antigravity or Claude Desktop**, use `mcp-config.json` in the project root. Note it points
at the venv interpreter — a bare `python` resolves to the Store Python, which does not have `mcp`
or `playwright` installed. (The historical `docs/antigravity-history/antigravity-mcp-config.json`
has the old bare-`python` command and the old Desktop path; it is kept as a record, not for use.)

## Setting up on another machine

The repo carries no environment. After cloning:

```bash
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m playwright install chromium
.venv\Scripts\python.exe tests\test_server_flow.py       # verify: needs network, ~30s
```

Then register it, substituting the real clone path:

```bash
claude mcp add ikea-designer --scope user -- <repo>\.venv\Scripts\python.exe <repo>\server.py
```

Two things are machine-specific and will need editing: the absolute paths in `mcp-config.json`
(used by Antigravity / Claude Desktop, not by Claude Code), and the MCP registration itself, which
lives in the user's `.claude.json` rather than in the repo.

**Not in this repo:** `docs/antigravity-history/` — the recovered Antigravity session transcripts,
room photos and floor plan. Deliberately gitignored, because the GitHub remote is public and those
files show the inside of a home. They exist only on the original machine. If you need them
elsewhere, copy them out of band rather than committing them.

## Also fixed along the way

**stdout pollution — would have broken the server in any client.** `ikea_scraper.py` printed
progress messages to stdout, which on a stdio MCP server is the JSON-RPC channel. Any scrape
would have corrupted the protocol stream. All progress output now goes to stderr via `_log()`.
This bug predates the sampling refactor and was never hit, because the server was never run.

**Debug dumps escaped the project.** On a failed scrape the code wrote `debug_screenshot.png` and
`sale_page_dump.html` to the current working directory — arbitrary when launched by an MCP client.
Now written next to `ikea_scraper.py`.

**`tests/test_server_flow.py` rewritten.** It previously called the pre-refactor signature and
could not have passed. It now launches the server as a real MCP subprocess and drives it over the
protocol, which is what actually proves the thing works.

## Two scraper bugs, found 2026-07-28

Both were mine, and both were reported here as facts about IKEA before being diagnosed.
The user pushed back on a claim that no armchairs were on sale, which is what exposed them.

**We read the wrong price node.** A discounted card renders *two* `.plp-price__integer`
elements: the struck-out original first, then the price you actually pay. `querySelector`
returns the first, so every quoted price was the pre-discount figure.

This document previously recorded that gap — KALLAX 475→350, RÅSKOG 195→150, SÖDERHAMN
3,590→2,580 — as "the sale page shows the pre-discount price", i.e. as IKEA's behaviour.
That was wrong. The listing does show the offer price; we were not reading it. The
conclusion that the earlier recommendation list was inflated still holds; the cause does not.

Fixed by selecting `.plp-price-module__primary-currency-price-energy-class .plp-price__integer`
for `price` and `.plp-price-module__comparison-price .plp-price__integer` for `price_before`,
falling back on DOM order (payable price is last). `tests/test_server_flow.py` now asserts the
listing price equals the `check_product` price, which is the assertion that catches a relapse.

**We only ever scraped the first page.** IKEA paginates at 24 cards behind a "הצג עוד"
control that the old blind-scroll loop never clicked. The hub reports ~2,107 items and we
were collecting 24 of them — 1.1%. The January run's 48 rows (≈24 unique) hit the same
ceiling. Anything concluded from "what's on sale" before this date rests on that sample.

Fixed with a click-until-exhausted loop bounded by `max_items`. A stalled batch is retried
up to `MAX_STALLS` times before being treated as the end of the list — without the retry the
scrape silently truncated at 48 of 126 on roughly half of runs.

Verified: category `700640` now returns 126/126 items on consecutive runs, and 19 armchairs
under ₪1,000 that the old code could not see.

## Known data caveats

- Prefer a category page over the sale hub. `category_url` accepts `sofas-armchairs`,
  `tables-chairs`, `desks-office-chairs`, or any full IKEA offers URL.
- Sale listings go stale fast. Of six items chosen in February, three now redirect
  (`status: "Unavailable (Redirected)"`) — LISTERBY, VEDBO and SANDTRAV all lost the exact
  variant, though each range still has live siblings. Re-check every URL before quoting it.
- The January HELMER URL redirects for the same reason.
- Product names come back in Hebrew, with the English range name on the first line.

## Untouched

`ikea_scraper.py`'s scraping and anti-detection logic (still works against the live site), the
design-session helper scripts, and `docs/antigravity-history/` — the recovered project history.
