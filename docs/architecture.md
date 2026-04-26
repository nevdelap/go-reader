# 語 Reader — Architecture

A single-file static Japanese reader. No server, no build step — deploys anywhere (currently GitHub Pages).

## Files

| File                            | Purpose                                                                 |
| ------------------------------- | ----------------------------------------------------------------------- |
| `index.html`                    | Entire app — HTML, CSS, and JavaScript                                  |
| `kuromoji.js`                   | Japanese morphological analyser (runs in the browser)                   |
| `jmdict-compact.json.gz`        | Compact gzipped dictionary (word → English glosses)                     |
| `dict/`                         | Binary dictionary files loaded by kuromoji at runtime                   |
| `compact_jmdict.py`             | Build script: preprocesses full JMdict JSON into compact form           |
| `compact_repo.sh`               | Maintenance script: rewrites git history to remove old dictionary blobs |
| `local_serve.py`                | Local dev server                                                        |
| `manifest.json` / `favicon.svg` | PWA manifest and icon                                                   |

______________________________________________________________________

## Libraries

- **[kuromoji.js](https://github.com/takuyaa/kuromoji.js)** — Pure JavaScript Japanese morphological analyser. Loads binary dictionary files from `dict/` at startup, then tokenizes text entirely in-browser.
- **[JMdict](https://www.edrdg.org/jmdict/j_jmdict.html)** — Japanese-English dictionary from EDRDG, bundled as a compact gzipped JSON lookup table.

______________________________________________________________________

## Analytics

[GoatCounter](https://www.goatcounter.com/) is used for privacy-friendly page view tracking. No cookies, no personal data. The script tag in `index.html` points to `go-reader.goatcounter.com`.

______________________________________________________________________

## Data Flow

```text
User pastes text
       │
       ▼  (300ms debounce)
stripNonJapanese()          — strips Latin, numbers, punctuation
       │
       ▼
kuromoji.tokenize()         — produces morpheme tokens:
                              surface_form, reading, basic_form, pos
       │
       ▼
renderTokens()              — builds clickable <span> elements (display: inline)
                              content words: white
                              grammar/particles: gray
       │
       ▼  (tap/click)
openPanel()                 — bottom panel shows:
                              • surface form + hiragana reading
                              • part of speech (mapped JP → EN)
                              • English gloss from JMdict
```

______________________________________________________________________

## Dictionary Build

The full JMdict JSON is ~50 MB — too large to load in a browser. `compact_jmdict.py` reduces it to a flat map containing only what the app needs:

```json
{ "word": ["gloss1", "gloss2", ...], ... }
```

- Only the first sense that has English glosses is used — secondary senses are discarded
- All English glosses from that sense are kept
- On key collision (multiple entries share the same kanji/kana form), the common entry's glosses
  overwrite an uncommon entry's, but uncommon entries are still included if there is no collision
- Output: `jmdict-compact.json.gz` (~6.5 MB gzipped)

To regenerate, see [Building the dictionary](../README.md#building-the-dictionary) in the README.

______________________________________________________________________

## Dictionary Loading

At startup, kuromoji and JMdict are loaded in parallel. The browser decompresses `jmdict-compact.json.gz` using the native
`DecompressionStream` API (falls back to server-decompressed response when a local dev server handles gzip automatically).

Up to 5 retry attempts with increasing delays (2s, 4s, 6s…) if either load fails.

______________________________________________________________________

## Lookup Logic

When a token is tapped, `lookupWord(surface_form, basic_form)` tries:

1. `surface_form` — the exact text as it appears (e.g. `食べました`)
2. `basic_form` — the dictionary/base form (e.g. `食べる`), skipped if it equals `surface_form` or `*`

This handles conjugated verbs and adjectives. If neither is found in JMdict, the display falls back to the `basic_form`
string from kuromoji.

Katakana readings from kuromoji are converted to hiragana for display (`toHiragana()`).

______________________________________________________________________

## UI Details

- **Token rendering** — tokens use `display: inline` so letter-spacing and glyph metrics behave consistently with the textarea input
- **Token area rebuild** — on re-tokenization, the token area DOM node is replaced with a clone to avoid accumulating event listeners
- **Panel height tracking** — a `ResizeObserver` keeps `--panel-height` in sync so the token area scrolls far enough to keep the active token visible above the bottom panel
- **Input deduplication** — if the raw input hasn't changed since last tokenization, rendering is skipped
- **Debounce** — 300ms after last keypress before `analyze()` fires
- **Grammar classification** — particles (`助詞`), auxiliary verbs (`助動詞`), symbols, punctuation, and whitespace tokens are styled gray and show their POS label rather than a dictionary lookup

______________________________________________________________________

## Deployment

The app is fully static — serve `index.html` and the supporting files from any static host. On first load, the browser
fetches Google Fonts, `jmdict-compact.json.gz`, and the kuromoji binary dictionary files in `dict/`.
