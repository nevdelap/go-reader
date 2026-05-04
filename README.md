# 語 Reader — Japanese Reader For Learners

A free Japanese reading tool for advanced learners. Type or paste Japanese text
and tap or click any morpheme to instantly see its hiragana reading and English
meaning. Look up kanji, vocabulary, and grammar while reading native Japanese
content.

<img src="phone-image.png" width="400" alt="語 Reader on mobile"><br>
*語 Reader on mobile.*

<img src="og-image.png" alt="語 Reader on desktop"><br>
*語 Reader on desktop.*

Japanese text processing runs in your browser — no account, no server-side text
analysis, **no AI**. The site does load Google Analytics and Google Fonts; your
reading text is not sent to them by the app.

**[https://nevdelap.github.io/go-reader/](https://nevdelap.github.io/go-reader/)**

## Features

- **Instant morpheme lookup** — tap or click any morpheme in Japanese text to
  see its reading and English definition
- **Hiragana readings** — see how any morpheme is pronounced
- **Browser-local reading** — once the app and dictionaries are loaded, lookups
  run locally in your browser and may keep working from the browser cache
- **Light and dark modes** — follows your system preference, or can be set
  manually
- **Mobile-friendly** — works on phones and tablets
- **Welcome overlay** — introduction for first-time visitors
- **Free and open source** — no sign-up, no server-side text processing, no ads

Google Analytics is used for basic usage stats, such as country-level visitor
counts, and is skipped when browser Do Not Track is enabled.

## How it works

- **Tokenization** — [kuromoji.js](https://github.com/takuyaa/kuromoji.js), a
  pure JavaScript Japanese morphological analyzer
- **Dictionary lookups** — [JMdict](https://www.edrdg.org/jmdict/j_jmdict.html),
  the Electronic Dictionary Research and Development Group's Japanese-English
  dictionary, bundled as a compact gzipped JSON file

See [docs/architecture.md](docs/architecture.md) for a detailed breakdown.

## Licenses

- App code: [MIT](LICENSE)
- Dictionary data: [CC BY-SA 4.0](LICENSE-JMDICT) — © Electronic Dictionary
  Research and Development Group
- kuromoji.js: browser build from the [kuromoji npm
  package](https://www.npmjs.com/package/kuromoji), [Apache
  2.0](LICENSE-KUROMOJI) — [NOTICE.md](NOTICE.md) is included from the package
  as required by Apache 2.0, though it covers mecab-ipadic dictionary data, not
  kuromoji
- Lucide icons: [ISC](LICENSE-LUCIDE)

## Local development

```bash
just install-hooks # install git hooks
just serve         # serve locally and open in browser
just format        # format Markdown
just lint          # format then lint
just test          # run tests
just tag_and_push  # tag the release and push
```

## Maintaining the repository

Periodically update the dictionary in compliance with its license and rewrite
history to keep the repo lean.

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
scripts/update_jmdict_and_compact_repo.sh
```

The script checks for a new JMdict release, downloads it if one is available,
rebuilds the compact dictionary, rewrites git history to remove old dictionary
blobs, and prompts before force-pushing.

Note: GitHub will also periodically run its own garbage collection on the server
side, which helps over time, but won't rewrite history to remove old blobs —
that requires the steps above.
