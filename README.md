# AutoDevOps

An AI-powered DevOps automation tool for intelligent failure triage and Kubernetes job orchestration using **Claude AI** and **Kubernetes**.

## Features

- **AI-Powered Triage**: Automatically analyze failure logs using Claude AI
- **Kubernetes Job Orchestration**: Submit jobs that clone a repo and run tests
- **Auto Language Detection**: Detects Python, Node, Java, Go projects automatically
- **Auto Triage on Failure**: Any failing job gets triaged by Claude automatically
- **Two Interfaces**: CLI for local use, FastAPI via Docker for deployment

## Project Structure

```
AutoDevOps/
├── ai/
│   └── triage.py              # Claude log analysis (SDK or API depending on context)
├── cli/
│   └── autodev_cli.py         # CLI commands
├── orchestrator/
│   └── k8_runner.py           # Kubernetes job submission
├── service/
│   └── main.py                # FastAPI app (runs via Docker)
├── terraform/
│   └── local-k8s/             # Deploys AutoDevOps to K8s
│       ├── namespace.tf
│       ├── deployment.tf
│       ├── service.tf
│       └── rbac.tf
├── test-jobs/
│   └── failing-python/        # Demo job designed to fail
│       ├── requirements.txt   # Bad dependency (requests==99.99.99)
│       └── test_dummy.py      # Tests with intentional failures
├── client.py                  # CLI entry point
├── autodev.yaml               # Configuration
├── sample.log                 # Sample log for triage testing
├── requirements.txt
└── Dockerfile
```

---

## Claude Authentication — Two Modes

AutoDevOps uses Claude differently depending on where it runs:

| Interface | Auth Method | How |
|---|---|---|
| **CLI (local)** | Claude Agent SDK | No API key needed — uses your Claude Code CLI session |
| **Kubernetes (Docker)** | Anthropic API | Requires `ANTHROPIC_API_KEY` — set as a K8s Secret |

`ai/triage.py` detects which mode to use automatically:
- If `ANTHROPIC_API_KEY` env var is present → uses Anthropic API (Kubernetes mode)
- If not → uses Claude Agent SDK (CLI mode, requires Claude Code CLI to be authenticated)

---

## Prerequisites

- Python 3.11+
- Docker Desktop with Kubernetes enabled
- **Claude Code CLI** installed and authenticated (for CLI mode)
- **kubectl** configured
- **Anthropic API key** (for Kubernetes/Docker mode only)

## Installation

```bash
git clone https://github.com/S1998raghu/AutoDevOps
cd AutoDevOps
pip3 install -r requirements.txt
```

---

## Usage

### 1. CLI (Local) — no API key needed

The CLI uses Claude Agent SDK, which authenticates through your local Claude Code CLI session.

#### Triage a log file directly
```bash
python3 client.py triage sample.log
```

Example output:
```json
{
  "summary": "Build failed due to missing Python dependency",
  "type": "dependency_error",
  "suggested_fix": "Run: pip install requests"
}
```

#### Submit a job — with auto triage on failure
```bash
# Basic job (echo only)
python3 client.py run my-test-job

# With a real repo
python3 client.py run my-test-job --repo https://github.com/user/repo

# Target a subdirectory within the repo
python3 client.py run my-test-job \
  --repo https://github.com/S1998raghu/AutoDevOps \
  --subdir test-jobs/failing-python
```

If the job fails, Claude automatically triages the logs and prints the analysis.

---

### 2. FastAPI via Docker + Kubernetes — requires API key

The Kubernetes pod cannot use your local Claude Code CLI session, so it authenticates with the Anthropic API directly using `ANTHROPIC_API_KEY`.

#### Step 1 — Add secrets to GitHub
In your GitHub repo → **Settings → Secrets and variables → Actions**, add:

| Secret | Value |
|---|---|
| `ANTHROPIC_API_KEY` | `sk-ant-your-key-here` |
| `KUBECONFIG` | Contents of `~/.kube/config` |

The GitHub Actions workflow (`.github/workflows/deploy.yml`) automatically injects `ANTHROPIC_API_KEY` as a Kubernetes Secret on every push to `master` — no API key is ever stored in the image or code.

#### Step 2 — Push to deploy
```bash
git push origin master
```

The workflow will:
1. Create the `anthropic-api-key` K8s Secret from GitHub Secrets
2. Run `terraform apply` to deploy the FastAPI pod

#### Manual deploy (local only)
```bash
docker build -t autodevops:latest .

cd terraform/local-k8s
terraform init
terraform apply
```

API available at **http://localhost:30080**

#### Health check
```bash
curl http://localhost:30080/
curl http://localhost:30080/api/v1/health
```

#### Submit a job
```bash
curl -X POST http://localhost:30080/api/v1/jobs/submit \
  -H "Content-Type: application/json" \
  -d '{"job_name": "api-test-job"}'
```

#### Submit a job with a repo
```bash
curl -X POST http://localhost:30080/api/v1/jobs/submit \
  -H "Content-Type: application/json" \
  -d '{
    "job_name": "real-test-job",
    "repo_url": "https://github.com/user/repo"
  }'
```

#### Demo: end-to-end triage without K8s (dry run)
```bash
curl -X POST http://localhost:30080/api/v1/jobs/submit \
  -H "Content-Type: application/json" \
  -d '{"job_name": "demo", "dry_run": true}'
```

#### Demo: end-to-end triage with failing job
```bash
curl -X POST http://localhost:30080/api/v1/jobs/submit \
  -H "Content-Type: application/json" \
  -d '{
    "job_name": "failing-job",
    "repo_url": "https://github.com/S1998raghu/AutoDevOps",
    "repo_subdir": "test-jobs/failing-python"
  }'
```

Response includes Claude's triage automatically on failure:
```json
{
  "job_name": "failing-job",
  "namespace": "default",
  "status": "failed",
  "logs": "ERROR: Could not find a version that satisfies the requirement requests==99.99.99...",
  "triage": {
    "summary": "pip failed to install requests==99.99.99 which does not exist",
    "type": "dependency_error",
    "suggested_fix": "Fix the version in requirements.txt to a valid release e.g. requests==2.31.0"
  }
}
```

**Interactive docs:** http://localhost:30080/docs

---

## Testing Your Own Code

Any repo with the right structure will be automatically detected, tested, and triaged on failure. Just point `repo_url` at it:

| Your repo has | AutoDevOps runs |
|---|---|
| `requirements.txt` | `pip install && pytest` |
| `package.json` | `npm install && npm test` |
| `pom.xml` | `mvn test` |
| `go.mod` | `go test ./...` |

Use `repo_subdir` to target a subdirectory within a repo:
```json
{
  "job_name": "my-job",
  "repo_url": "https://github.com/user/monorepo",
  "repo_subdir": "services/my-service"
}
```

---

## How It Works

### Full Flow (API)

```
curl POST /api/v1/jobs/submit
        ↓
FastAPI (K8s pod via Terraform)
        ↓
k8_runner → kubectl → K8s Job created
        ↓
Job clones repo → runs tests
        ↓
  ┌─────────────────────────────────┐
  │ success → logs returned         │
  │ failure → logs + Claude triage  │
  └─────────────────────────────────┘
        ↓
JSON response returned
```

### Triage Flow

```
failure logs
    ↓
ai/triage.py
    ├── ANTHROPIC_API_KEY set?
    │       YES → Anthropic API (claude-opus-4-6)        ← Kubernetes mode
    │       NO  → Claude Agent SDK → Claude Code CLI     ← CLI mode
    ↓
{ summary, type, suggested_fix }
```

---

## Kubernetes Setup

```bash
# Enable in Docker Desktop → Settings → Kubernetes
kubectl config use-context docker-desktop
kubectl get nodes
```

---

## Configuration

### autodev.yaml
```yaml
environment: "local"
k8s:
  namespace: "autodev"
  image: "autodevops:latest"
ai:
  provider: "claude"
  model: "claude-opus-4-6"
logging:
  level: "DEBUG"
```

### GitHub Secrets (for Kubernetes/Docker mode)

| Secret | Description |
|---|---|
| `ANTHROPIC_API_KEY` | Anthropic API key — injected as a K8s Secret by the deploy workflow |
| `KUBECONFIG` | Kubeconfig for the target cluster |

### Environment Variables (optional overrides)
```bash
K8S_NAMESPACE=default         # K8s namespace (default: default)
K8S_JOB_IMAGE=busybox:latest  # Fallback image when no repo provided
```

---

## Troubleshooting

**`CLINotFoundError`** — Claude Code CLI not installed. Get it at https://claude.ai/download

**`CLIConnectionError`** — Not authenticated. Run `claude` in terminal and log in

**Triage returns `api_error` in K8s** — `ANTHROPIC_API_KEY` GitHub Secret is missing or wrong.
Go to GitHub → Settings → Secrets → Actions and ensure `ANTHROPIC_API_KEY` is set, then re-run the workflow.

**`kubectl not found`** — kubectl not in PATH inside container. Rebuild the Docker image

**`connection refused` (K8s)** — Enable Kubernetes in Docker Desktop → Settings → Kubernetes

**`Forbidden` (K8s jobs)** — RBAC not applied. Run `terraform apply` in `terraform/local-k8s/`

---

## License

MIT License

## Security Notes

- Never commit API keys or credentials to git
- The `ANTHROPIC_API_KEY` is stored as a Kubernetes Secret, not baked into the image
- K8s RBAC is scoped to job creation only (`rbac.tf`)
