# Web Viewer Maintenance

Last updated: 2026-06-18

## Published Site

- GitHub repository: `https://github.com/caodudu/sci-journal-archive`
- Public page: `https://caodudu.github.io/sci-journal-archive/`
- The published branch is `gh-pages`.
- The source viewer files live in `web/` on `main`.

Important: pushing `main` is not enough proof that the public page changed. Always verify `gh-pages` and the live URL.

## What Should Be Published

Only static viewer files should be published:

```text
web/index.html
web/journals-data.js
```

Do not publish:

```text
data/raw/
data/processed/*.sqlite
data/processed/*.csv
logs/
enrichment cache files
```

`web/journals-data.js` is the active static data source because the viewer must work from local `file://` as well as GitHub Pages.

## Normal Publish Flow

1. Edit source files on `main`.
2. Verify locally from `web/index.html` or a temporary static server.
3. Commit and push `main`.
4. Confirm the GitHub Pages workflow updates `gh-pages`.
5. Verify the public page and its data file.

Useful commands:

```powershell
git status --short
git log --oneline -3
git push origin main
git fetch origin gh-pages main --prune
git rev-parse origin/main
git rev-parse origin/gh-pages
git ls-tree -l origin/gh-pages
```

Check live files:

```powershell
Invoke-WebRequest -UseBasicParsing -Uri "https://caodudu.github.io/sci-journal-archive/index.html" -TimeoutSec 20
Invoke-WebRequest -UseBasicParsing -Uri "https://caodudu.github.io/sci-journal-archive/journals-data.js" -Method Head -TimeoutSec 20
```

If the workflow does not update `gh-pages`, publish `web/` manually with a temporary worktree or a safe deploy action, then verify the live URL again.

## UI Verification Checklist

After each frontend change, verify:

- The page renders non-zero journal cards.
- Clicking a journal opens the floating detail modal.
- The old right-side detail panel is not present.
- Search defaults to title-only matching.
- Country filters still use multi-role country signals when enrichment data exists.
- Dark mode toggles and persists after reload.
- `file://` remains supported through `journals-data.js`.

## Current UI Notes

- The search box is intentionally title-only by default. It should not match publisher, country, category, ISSN, or other metadata unless a separate explicit search mode is added later.
- The journal detail view is a modal, not a right-column card.
- The IF distribution uses a fixed semantic order; `IF < 1` appears above `1 <= IF < 3`.
