---
description: Use just format to fix Markdown formatting issues
---

# Markdown Formatting

Never manually reformat Markdown (tables, line wrapping, etc.). Always run `just format` instead — it runs `mdformat` which handles all formatting consistently.

Run `just format` after any Markdown change that may affect formatting, or when linting reports Markdown issues.
