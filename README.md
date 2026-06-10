# Expense Tracker — DevOps Final Project

A multi-tier microservice application built to demonstrate a complete CI/CD and
infrastructure-as-code workflow: Docker → ECR → Helm → ArgoCD → EKS, with
Terraform-managed infrastructure and Prometheus/Grafana monitoring.

## Architecture

```
Streamlit (frontend) ──HTTP──▶ FastAPI (backend) ──SQL──▶ PostgreSQL (StatefulSet)
```

| Service  | Tech                 | Port |
| -------- | -------------------- | ---- |
| frontend | Python + Streamlit   | 8501 |
| backend  | Python + FastAPI     | 8000 |
| db       | PostgreSQL 16        | 5432 |

## Run locally

```bash
docker compose up --build
```

Then open http://localhost:8501 (UI) and http://localhost:8000/docs (API docs).

## Run the backend tests

```bash
cd backend
pip install -r requirements.txt
pytest -v
```

## Lint

```bash
ruff check backend frontend
```

## API

| Method | Path             | Description                  |
| ------ | ---------------- | ---------------------------- |
| GET    | /healthz         | Health probe for Kubernetes  |
| GET    | /expenses        | List all expenses            |
| POST   | /expenses        | Create an expense            |
| DELETE | /expenses/{id}   | Delete an expense            |
| GET    | /summary         | Totals grouped by category   |
| GET    | /metrics         | Prometheus metrics           |

## Helm charts

Per-service charts live in [`charts/`](charts/):

- `charts/backend` — Deployment, Service, Ingress, ServiceMonitor, and a
  `pre-install`/`pre-upgrade` Job that creates tables and seeds sample data.
- `charts/frontend` — Deployment, Service, Ingress.
- `charts/db` — thin wrapper around the Bitnami `postgresql` chart (StatefulSet).

Each chart is deployed by ArgoCD using env-specific values from the
[expense-tracker-infra](https://github.com/NiceXD1204/expense-tracker-infra) repo's
`gitops/dev/values-*.yaml`. To render locally:

```bash
helm template charts/backend -f ../expense-tracker-infra/gitops/dev/values-backend.yaml
helm lint charts/backend charts/frontend charts/db
```

## Infrastructure & deployment

Cluster (EKS), ECR, and cluster add-ons (ingress-nginx, ArgoCD,
kube-prometheus-stack) are provisioned by Terraform in the
[expense-tracker-infra](https://github.com/NiceXD1204/expense-tracker-infra) repo.
See that repo's README for the apply/destroy workflow and how to access ArgoCD.

## CI/CD (GitHub Actions)

| Workflow | Trigger | What it does |
| --- | --- | --- |
| `ci.yml` | PR to `master` | lint (`ruff`) + `pytest` + `docker build` (no push) |
| `deploy-staging.yml` | push to `master` | re-runs CI, builds & pushes images to ECR (`:<sha>` and `:latest`), updates `gitops/dev/values-*.yaml` in the infra repo so ArgoCD syncs |
| `deploy-production.yml` | tag `v*.*.*` | same, tags images with the version and updates the infra repo's values to that version |

### Required repo configuration

Settings → Secrets and variables → Actions:

- **Secrets**
  - `AWS_ROLE_ARN` — from `terraform output github_actions_role_arn` in the infra repo
  - `INFRA_REPO_TOKEN` — a fine-grained PAT (or deploy key) with push access to `expense-tracker-infra`
  - `SLACK_WEBHOOK_URL` — optional, for CI/deploy failure notifications
- **Variables**
  - `ECR_BACKEND_REPO` = `expense-tracker-backend`
  - `ECR_FRONTEND_REPO` = `expense-tracker-frontend`

### Branch protection

Settings → Branches → add a rule for `master`:

- Require a pull request before merging
- Require status checks to pass: `ci / lint`, `ci / test`, `ci / build (backend)`, `ci / build (frontend)`

## Project roadmap

- [x] Phase 1 — Application (frontend, backend, DB, Docker, tests)
- [x] Phase 2 — Terraform infrastructure (VPC, EKS, ECR, S3 state) — see `expense-tracker-infra`
- [x] Phase 3 — Helm charts + ArgoCD GitOps
- [x] Phase 4 — CI/CD with GitHub Actions (GitHub Flow)
- [x] Phase 5 — Monitoring (Prometheus/Grafana) + Slack alerts (bonus)

## Git workflow (GitHub Flow)

1. Create a feature branch: `feature/RND-123-add-new-feature`
2. Push commits → CI runs lint + build
3. Open a pull request into `master` (protected branch)
4. Merge to `master` → tests run + deploy to **staging**
5. Push a version tag (`v1.0.0`) → deploy to **production**
