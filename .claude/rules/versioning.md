---
description: Check git tags to decide if version bump is needed
---

# Versioning

After any non-documentation change, check if the version needs to be bumped:

1. Find the latest tag: `git tag --sort=-version:refname | head -1`
2. Compare it to the version in `index.html`
3. Only bump if they match (meaning no unreleased bump exists)

If `index.html` already has a higher version than the latest tag, do **not** bump again.

```html
<div class="subtitle">Scrum Poker · v1.0.0</div>
```

## How to set the version

When bumping, look at everything that has changed since the latest tag and apply
**exactly one bump** at the highest level required:

- Any breaking change → major (1.2.0 → 2.0.0)
- Any new feature, no breaking changes → minor (1.2.0 → 1.3.0)
- Only bug fixes → patch (1.2.0 → 1.2.1)

The result is always `tag_version + one bump`. Never accumulate multiple bumps
(e.g. if the tag is v1.2.0 and there is already a feature bump to v1.3.0 in
`index.html`, a subsequent bug fix leaves it at v1.3.0 — do not bump to v1.3.1).
