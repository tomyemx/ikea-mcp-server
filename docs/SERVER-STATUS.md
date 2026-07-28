# Server status — WORKING as of 2026-07-28

The server runs and is registered with Claude Code. Verified end to end over the real MCP
stdio protocol against the live IKEA Israel site.

```
tools advertised: ['get_sale_items', 'check_product']
get_sale_items(limit=3)  -> count=3  total_available=24
  first item: SÖDERHAMN @ 3,590 ILS
check_product(<that url>) -> status=Available  price=2580.0
All checks passed.
```

Reproduce with `.venv\Scripts\python.exe tests\test_server_flow.py` (needs network, ~30s).

## What the server does now

Two data tools, no LLM work of its own, no API key:

| Tool | Purpose |
|---|---|
| `get_sale_items(category=None, limit=50)` | Scrape the IKEA Israel sale page; returns JSON with name, description, price, image_url, product_url. Optional free-text category filter. Results cached per category for the process lifetime (a scrape takes ~20s). |
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

## Known data caveats

- The sale page listed SÖDERHAMN at **3,590** while the product page reported **2580.0**. Not a
  VAT difference (2580 × 1.17 ≈ 3019). Most likely the sale page shows the pre-discount price.
  Treat `check_product` as authoritative and verify before recommending.
- Only **24 items** are currently on the sale page, well under the `limit` of 50.
- The January HELMER URL now redirects — `status: "Unavailable (Redirected)"`. Correct behaviour,
  stale data. Product URLs from the recovered 2026 sessions should all be re-checked.
- Product names come back in Hebrew, with the English range name on the first line.

## Untouched

`ikea_scraper.py`'s scraping and anti-detection logic (still works against the live site), the
design-session helper scripts, and `docs/antigravity-history/` — the recovered project history.
