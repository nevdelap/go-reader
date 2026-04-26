---
description: Keep the version correct so releases need no manual adjustment
---

# Versioning

After any non-documentation change, set the version in `index.html` so that tagging
a release right now would produce a correct semver. The user should never need to
adjust the version before releasing.

```html
<div class="subtitle">Japanese Reader For Learners · v1.0.2</div>
```

## How to set the version

1. Find the latest tag: `git tag --sort=-version:refname | head -1`
2. Look at everything that has changed since that tag (not just the current session)
3. Apply **exactly one bump** at the highest level required:
   - Any breaking change → major (1.2.0 → 2.0.0)
   - Any new feature, no breaking changes → minor (1.2.0 → 1.3.0)
   - Only bug fixes → patch (1.2.0 → 1.2.1)

The result is always `tag_version + one bump`. Never accumulate multiple bumps
(e.g. if the tag is v1.2.0 and there is already a feature bump to v1.3.0 in
`index.html`, a subsequent bug fix leaves it at v1.3.0 — do not bump to v1.3.1).
