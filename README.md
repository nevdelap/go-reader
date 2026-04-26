# 語 Reader

A Japanese reader for learners. Type or paste Japanese text and tap any word to
see its reading and English meaning. Everything runs in the browser — no server,
no API calls, no cost to run.

**[https://nevdelap.github.io/go-reader/](https://nevdelap.github.io/go-reader/)**

## How it works

- **Tokenisation** — [kuromoji.js](https://github.com/takuyaa/kuromoji.js), a
  pure JavaScript Japanese morphological analyser
- **Dictionary lookups** — [JMdict](https://www.edrdg.org/jmdict/j_jmdict.html),
  the Electronic Dictionary Research and Development Group's Japanese-English
  dictionary, bundled as a compact gzipped JSON file

See [docs/architecture.md](docs/architecture.md) for a detailed breakdown.

## Licences

- App code: [MIT](LICENSE)
- Dictionary data: [CC BY-SA 4.0](LICENSE-JMDICT) — © Electronic Dictionary
  Research and Development Group
- kuromoji.js: [Apache 2.0](https://www.apache.org/licenses/LICENSE-2.0)

## Compacting the repository

Each dictionary update adds a new 6.5MB binary blob to git history. Periodically
rewrite history to keep the repo lean.

Install `git-filter-repo` if not already installed using your package manager,
e.g.:

```bash
# Linux (Debian/Ubuntu)
sudo apt install git-filter-repo

# macOS
brew install git-filter-repo
```

Then run:

```bash
./compact_repo.sh
```

Note: GitHub will also periodically run its own garbage collection on the server
side, which helps over time, but won't rewrite history to remove old blobs —
that requires the steps above.

## Building the dictionary

To regenerate `jmdict-compact.json.gz` when there are new releases:

1. Download `jmdict-eng-x.x.x.json` from [jmdict-simplified
   releases](https://github.com/scriptin/jmdict-simplified/releases/latest)
2. Run `./compact_jmdict.py` from the same directory
3. Commit and push `jmdict-compact.json.gz`
