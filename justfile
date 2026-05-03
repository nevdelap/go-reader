set shell := ["bash", "-cu"]

MARKDOWNLINT_IMAGE := "ghcr.io/igorshubovych/markdownlint-cli:latest"
BLUE := '\033[0;34m'
RESET := '\033[0m'

# Show help.
@_:
    just --list

# Install git hooks.
install-hooks:
    ln -sf ../../scripts/pre-push .git/hooks/pre-push

# Serve locally and open in browser.
serve:
    scripts/local_serve.py

# Format Markdown files.
format:
    @echo $'{{ BLUE }}Formatting Markdown files...{{ RESET }}'
    uv tool run --with mdformat-gfm --with mdformat-frontmatter mdformat --number .claude/ docs/ README.md

# Lint Markdown files.
lint: format
    @echo $'{{ BLUE }}Linting Markdown files...{{ RESET }}'
    docker pull {{ MARKDOWNLINT_IMAGE }} > /dev/null
    docker run --pull always --rm -u "$(id -u):$(id -g)" -v "$(pwd)":/workdir {{ MARKDOWNLINT_IMAGE }} /workdir/.claude /workdir/docs /workdir/README.md

# Run tests.
test:
    node test.js
    uv run scripts/test_compact_jmdict.py

# Tag the release and push.
tag_and_push:
    scripts/tag_and_push.sh
