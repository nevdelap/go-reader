set shell := ["bash", "-cu"]

MARKDOWNLINT_IMAGE := "ghcr.io/igorshubovych/markdownlint-cli:latest"
BLUE := '\033[0;34m'
RESET := '\033[0m'

# Codex sandboxes can make uv's default cache read-only. Claude Code and manual
# local runs work with the normal cache, so only use the fallback when needed or
# if UV_CACHE_DIR is already set by the caller.
UV_CACHE := "if [[ -z \"${UV_CACHE_DIR:-}\" && ! -w \"${XDG_CACHE_HOME:-$HOME/.cache}/uv\" ]]; then export UV_CACHE_DIR=/home/nevd/.tmp/uv-cache; fi"

# Show help.
@_:
    just --list

# Install git hooks.
install_hooks:
    ln -sf ../../scripts/pre-push .git/hooks/pre-push

# Serve locally and open in browser.
serve:
    scripts/local_serve.py

# Format Markdown files.
format:
    @echo $'{{ BLUE }}Formatting Markdown files...{{ RESET }}'
    uv tool run --with mdformat-gfm --with mdformat-frontmatter mdformat --number .claude/ docs/ design_docs/ README.md

# Lint Markdown files.
lint: format
    @echo $'{{ BLUE }}Linting Markdown files...{{ RESET }}'
    docker pull {{ MARKDOWNLINT_IMAGE }} > /dev/null
    docker run --pull always --rm -u "$(id -u):$(id -g)" -v "$(pwd)":/workdir {{ MARKDOWNLINT_IMAGE }} /workdir/.claude /workdir/docs /workdir/design_docs /workdir/README.md

# Run tests.
test:
    node test.js
    {{ UV_CACHE }}; uv run scripts/test_compact_jmdict.py

# Download source if needed and generate JMdict lookup files.
build-dict:
    {{ UV_CACHE }}; uv run scripts/download_jmdict_source.py
    {{ UV_CACHE }}; uv run scripts/compact_jmdict.py

# Build the WASM tokenizer (requires wasm-pack; run setup-wasm-dict first if pkg/ is missing).
build-wasm:
    cd kuromoji-wasm && LINDERA_CACHE={{justfile_directory()}}/kuromoji-wasm/lindera-cache wasm-pack build --target web --release --out-dir ../pkg

# Pre-build the Lindera IPAdic dictionary from a local tarball (run once after cloning).
# Downloads the MeCab IPAdic tarball from SourceForge, then compiles it.
setup-wasm-dict:
    mkdir -p kuromoji-wasm/lindera-cache
    curl -L "https://sourceforge.net/projects/mecab/files/mecab-ipadic/2.7.0-20070801/mecab-ipadic-2.7.0-20070801.tar.gz/download" -o kuromoji-wasm/lindera-cache/mecab-ipadic-2.7.0-20070801.tar.gz
    cd kuromoji-wasm/build-dict && cargo build --release
    kuromoji-wasm/build-dict/target/release/build-dict kuromoji-wasm/lindera-cache/mecab-ipadic-2.7.0-20070801.tar.gz kuromoji-wasm/lindera-cache/0.32.3/lindera-ipadic

# Run Rust tests for the WASM tokenizer (native, not in browser).
test-wasm:
    cd kuromoji-wasm && LINDERA_CACHE={{justfile_directory()}}/kuromoji-wasm/lindera-cache cargo test

# Build the ultra-compact JMdict WASM binary.
build-jmdict-wasm-ultra:
    cd jmdict-wasm && wasm-pack build --target web --release --out-dir ../pkg --out-name jmdict_ultra_wasm -- --features ultra

# Build the full JMdict WASM binary.
build-jmdict-wasm-full:
    cd jmdict-wasm && wasm-pack build --target web --release --out-dir ../pkg --out-name jmdict_full_wasm -- --features full

# Build both JMdict WASM binaries and compress them.
build-jmdict-wasm: build-jmdict-wasm-ultra build-jmdict-wasm-full compress-wasm

# Pre-compress WASM binaries for local serving (local_serve.py uses the .gz sidecars).
compress-wasm:
    gzip -kf pkg/jmdict_ultra_wasm_bg.wasm
    gzip -kf pkg/jmdict_full_wasm_bg.wasm
    gzip -kf pkg/kuromoji_wasm_bg.wasm

# Run all tests (JS + Python + Rust).
test-all: test test-wasm

# Push to unstable (origin).
push_unstable *args:
    git push origin HEAD:main --force {{ args }}

# Tag the release and push to prod.
tag_and_push: lint
    scripts/tag_and_push.sh
