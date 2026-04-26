---
description: Bump the semver version number on non-documentation changes
---

# Versioning

Bump the semver version in the subtitle line of `index.html` whenever a non-documentation change is made.
Only bump once per logical change — do not bump again if the same piece of functionality is being refined within the same conversation.

```html
<div class="subtitle">Japanese Reader For Learners · v1.0.2</div>
```

- Bug fixes → patch (1.0.2 → 1.0.3)
- New features → minor (1.0.2 → 1.1.0)
- Breaking changes → major (1.0.2 → 2.0.0)
