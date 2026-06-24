# CI/CD Demo: FastAPI + GitHub Actions + Render

A minimal FastAPI service with a fully automated CI/CD pipeline: every push to `main`
runs tests, lints the code, scans for security vulnerabilities (code + dependencies +
Docker image), builds a Docker image, and deploys automatically to Render — with a
post-deploy health check that verifies the rollout actually worked.

## Architecture

```
push to main
   │
   ▼
┌─────────┐   ┌──────────┐   ┌───────┐   ┌────────┐
│  test   │──▶│ security │──▶│ build │──▶│ deploy │
└─────────┘   └──────────┘   └───────┘   └────────┘
 pytest +      bandit +       docker      Render API
 ruff lint     pip-audit +    build       + health
               trivy                      check
```

Each stage gates the next — if tests fail, nothing gets scanned; if a scan finds a
critical vuln, nothing gets built or deployed.

| Stage | Tool | Purpose |
|---|---|---|
| Test | `pytest` + coverage | Unit tests against the API |
| Lint | `ruff` | Fast Python linting |
| Security (SAST) | `bandit` | Scans Python code for insecure patterns |
| Security (deps) | `pip-audit` | Checks dependencies against known CVEs |
| Security (image) | `trivy` | Scans filesystem/image for HIGH/CRITICAL vulns |
| Build | Docker Buildx | Builds the container image, cached via GHA cache |
| Deploy | Render Deploy Hook | Triggers a deploy of the latest image |
| Verify | `curl` health check | Confirms `/health` returns 200 after deploy, with retries |

## Local development

```bash
python -m venv venv
source venv/bin/activate           # Windows: venv\Scripts\activate
pip install -r requirements-dev.txt

# run the app
uvicorn app.main:app --reload

# run tests
pytest --cov=app

# lint
ruff check app tests

# security scans (same as CI)
bandit -r app
pip-audit -r requirements.txt

# build the docker image
docker build -t cicd-demo .
docker run -p 8000:8000 cicd-demo
```

Visit `http://localhost:8000/docs` for interactive API docs (Swagger UI).

## Setting up the deploy step (Render)

1. Create a free account at [render.com](https://render.com).
2. New → Web Service → connect this GitHub repo. Render will detect `render.yaml`
   automatically (or just point it at the Dockerfile manually).
3. In the Render dashboard for the service: **Settings → Deploy Hook** → copy the URL.
4. In your GitHub repo: **Settings → Secrets and variables → Actions → New repository secret**
   - `RENDER_DEPLOY_HOOK_URL` = the deploy hook URL from step 3
   - `RENDER_SERVICE_URL` = your service's public URL (e.g. `https://cicd-demo.onrender.com`)
5. Push to `main` — the `deploy` job will hit the hook and then poll `/health` until it's live.

> Note: `autoDeploy: false` in `render.yaml` is intentional — it stops Render from
> auto-deploying on every push by itself, so the GitHub Actions pipeline is the single
> source of truth for *when* a deploy happens (after tests + security gates pass).

## Why this is structured this way (notes for interviews)

- **Gating, not just running steps in parallel.** `security` depends on `test`,
  `build` depends on `security`, `deploy` depends on `build`. A failure anywhere
  upstream stops the pipeline — this is the difference between "we run scans" and
  "we actually enforce them."
- **Three layers of security scanning**, because each catches different things:
  code-level bugs (bandit), known-vulnerable dependencies (pip-audit), and
  OS/package vulnerabilities in the built image (trivy).
- **Deploys are decoupled from Render's own auto-deploy**, so the only way code
  reaches production is through the pipeline — not a side channel.
- **Post-deploy verification** (the health check loop) catches the class of bug
  where the deploy "succeeds" per the platform but the app is actually crashing on
  boot. This is a real production lesson, not just a checkbox.
- **PRs run test+security but not deploy** (`if: github.ref == 'refs/heads/main'`),
  so you get fast feedback on PRs without ever deploying unmerged code.

## API endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/` | Service status |
| GET | `/health` | Health check (used by CI/CD and Render) |
| GET | `/items` | List all items |
| POST | `/items` | Create an item |
| GET | `/items/{id}` | Get one item |
| DELETE | `/items/{id}` | Delete an item |
