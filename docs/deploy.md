# Deploy and data refresh

The site is static (`site/`) and is published with GitHub Pages. Data is refreshed by a scheduled GitHub Action that runs the Python pipeline and commits `site/data/`.

## Workflows

| Workflow | Trigger | What it does |
|---|---|---|
| `.github/workflows/refresh-data.yml` | Weekdays 12:23 UTC; manual ("Run workflow") | Installs `requirements.txt`, restores the previous `data/` from the Actions cache, runs `python run_pipeline.py` (fetch, process, export, validate), writes the validation report to the run summary, commits `site/data/` if it changed, then deploys |
| `.github/workflows/deploy.yml` | Push to `main` touching `site/`; manual; called by the refresh | Validates `site/data/`, copies `site/` without `site/dev/` to the Pages artifact, publishes |

Failure behaviour:
- If a source's API is down, its fetch fails but processing uses the cached download, so the refresh still succeeds and the validator reports the series as stale in the run summary.
- If processing, export or validation fails, the job fails, nothing is committed, and the published site keeps the previous data. GitHub emails the person who last edited the schedule.

## One-time setup (repository owner)

1. Push `main` to GitHub.
2. **Settings → Pages → Build and deployment → Source: GitHub Actions.**
   GitHub Pages on a private repository needs a paid plan (Pro, Team or Enterprise). On a free plan the repository must be public.
3. **Settings → Actions → General → Workflow permissions:** "Read and write permissions" (the refresh commits `site/data/`). If the organisation forbids it, the refresh job will fail at the push step.
4. **Actions → Refresh data → Run workflow** once to check everything end to end. The site appears at `https://<owner>.github.io/<repo>/` (here `https://chasecde.github.io/CdE-Dashboard-v1/`).
5. Optional: a custom domain such as `datos.circulodeempresarios.org` (Settings → Pages → Custom domain, plus a CNAME record from whoever manages the Círculo's DNS).

## Running locally

```
pip install -r requirements.txt
python run_pipeline.py              # ~2 min; rebuilds and validates site/data
cd site && python -m http.server 8000
```

Open http://localhost:8000/. Opening `index.html` directly from disk does not work: browsers block the data requests on `file://`.
