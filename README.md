# 語 Reader

A Japanese reader for learners. Type or paste Japanese text and tap any word to see its reading and English meaning. Everything runs in the browser — no server, no API calls, no cost to run.

**[https://nevdelap.github.io/go-reader/](https://nevdelap.github.io/go-reader/)**

## How it works

- **Tokenisation** — [kuromoji.js](https://github.com/takuyaa/kuromoji.js), a pure JavaScript Japanese morphological analyser
- **Dictionary lookups** — [JMdict](https://www.edrdg.org/jmdict/j_jmdict.html), the Electronic Dictionary Research and Development Group's Japanese-English dictionary, bundled as a compact gzipped JSON file

See [docs/architecture.md](docs/architecture.md) for a detailed breakdown.

## Licences

- App code: [MIT](LICENSE)
- Dictionary data: [CC BY-SA 4.0](LICENSE-JMDICT) — © Electronic Dictionary Research and Development Group
- kuromoji.js: [Apache 2.0](https://www.apache.org/licenses/LICENSE-2.0)

## Building the dictionary

If you need to regenerate `jmdict-compact.json.gz` from a fresh JMdict release:

1. Download `jmdict-eng-x.x.x.json` from [jmdict-simplified releases](https://github.com/scriptin/jmdict-simplified/releases/latest)
2. Run `./compact_jmdict.py` from the same directory
