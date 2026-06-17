# GitHub Pages Publishing

This project can publish the full agent HTML as a GitHub-hosted static site.

## Published files

The publish script writes these files into `docs/`:

- `index.html`
- `betmateedgeaflprops.html`
- `full-report.html`
- `premium-archive.html`
- `latest.json`
- `.nojekyll`

`index.html` and `betmateedgeaflprops.html` both serve the full agent report.

## Local publish

Publish the current checked-in report:

```bash
python3 publish_github_pages.py
```

Refresh live data first, then publish:

```bash
THE_ODDS_API_KEY=... python3 publish_github_pages.py --refresh
```

## GitHub Actions

Workflow file:

- `.github/workflows/publish-betmate-pages.yml`

Behavior:

- `push`: publishes the current checked-in HTML
- `workflow_dispatch`: can refresh live data first
- `schedule`: attempts hourly refresh and publish

## Required GitHub secret

For scheduled/manual live refreshes, set:

- `THE_ODDS_API_KEY`

Without that secret, the workflow still publishes the current checked-in report, but it will not fetch fresh Odds API data.

## Repository settings

In GitHub:

1. Open `Settings -> Pages`
2. Set `Source` to `GitHub Actions`

After that, the workflow deploys the HTML site automatically.
