# Wiki source pages and publishing

The Markdown files here are the canonical, version-controlled source for the Market Structure Lab GitHub Wiki. They are reviewed alongside code and research reports on `RUSSEL_SP`.

The repository has Wiki enabled, but the separate Wiki Git repository was not initialized when these pages were prepared. This directory keeps the content safe and reviewable in the main repository.

## Publish

1. Open **Wiki** in the repository and create the first page. This initializes GitHub's separate Wiki repository.
2. Add an Actions secret named `WIKI_PUSH_TOKEN` containing a classic personal access token with permission to write to this repository's Wiki. Never commit the token.
3. Open **Actions → Publish GitHub Wiki**, select `RUSSEL_SP`, and run it manually.
4. Review the published Home page and links.

Publishing is deliberately manual, not automatic on every push. If the token is absent, the workflow stops with an error. The canonical content remains available here.
