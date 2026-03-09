# AutoDevOps

An AI-powered DevOps automation tool for intelligent failure triage and Kubernetes job orchestration using **Claude AI** and **Kubernetes**.

## Features

- **AI-Powered Triage**: Automatically analyze failure logs using Claude AI and get intelligent suggestions for fixes
- **Kubernetes Job Orchestration**: Submit and monitor jobs on a Kubernetes cluster
- **Two Interfaces**: CLI for local use, FastAPI via Docker for deployment

## Project Structure

```
AutoDevOps/
├── ai/
│   ├── __init__.py
│   └── triage.py          # Claude Agent SDK integration for log analysis
├── cli/
│   ├── __init__.py
│   └── autodev_cli.py     # CLI commands
├── orchestrator/
│   ├── __init__.py
│   └── k8_runner.py       # Kubernetes job submission
├── service/
│   └── main.py            # FastAPI app (runs via Docker)
├── terraform/
│   └── local-k8s/         # Terraform config to deploy to K8s
├── client.py              # CLI entry point
├── autodev.yaml           # Configuration
├── sample.log             # Sample log for testing
├── requirements.txt
└── Dockerfile
```

## Prerequisites

- Python 3.11+
- Docker Desktop with Kubernetes enabled
- **Claude Code CLI** installed and authenticated
- **kubectl** configured

## Installation

```bash
git clone <repository-url>
cd AutoDevOps
pip3 install -r requirements.txt
```

---

## Usage

### 1. CLI (Local)

Run directly on your machine — no Docker needed.

#### Triage a log file
```bash
python3 client.py triage sample.log
```

Example output:
```json
{
  "summary": "Build failed due to missing Python dependency requests",
  "type": "dependency_error",
  "suggested_fix": "Run: pip install requests"
}
```

#### Submit a Kubernetes job
```bash
python3 client.py run my-test-job

# With a repo to test
python3 client.py run my-test-job --repo https://github.com/user/repo
```

#### Help
```bash
python3 client.py --help
```

---

### 2. FastAPI via Docker

Build the image and run the API server in a container.

#### Build
```bash
docker build -t autodevops:latest .
```

#### Run
```bash
docker run -p 8000:8000 autodevops:latest
```

The API runs at **http://localhost:8000**

#### Endpoints

**Health check:**
```bash
curl http://localhost:8000/
curl http://localhost:8000/api/v1/health
```

**Submit a Kubernetes job:**
```bash
curl -X POST http://localhost:8000/api/v1/jobs/submit \
  -H "Content-Type: application/json" \
  -d '{"job_name": "api-test-job"}'
```

Response:
```json
{
  "job_name": "api-test-job",
  "namespace": "default",
  "status": "succeeded",
  "logs": "Running job: api-test-job"
}
```

**Interactive docs:** http://localhost:8000/docs

---

## Kubernetes Setup

Enable Kubernetes in Docker Desktop:

1. **Docker Desktop** → **Settings** → **Kubernetes**
2. Check **Enable Kubernetes** → **Apply & Restart**
3. Verify:
```bash
kubectl config use-context docker-desktop
kubectl get nodes
```

### Deploy AutoDevOps itself to K8s (Terraform)

```bash
cd terraform/local-k8s
terraform init
terraform apply
```

This deploys the FastAPI server as a Kubernetes Deployment, exposed on port `30080`.

---

## Configuration

### autodev.yaml
```yaml
environment: "local"
k8s:
  enabled: false
  namespace: "autodev"
  image: "autodev:latest"
ai:
  provider: "claude"
  model: "claude-sonnet-4-6"
logging:
  level: "DEBUG"
```

### Environment Variables
```bash
K8S_NAMESPACE=default        # K8s namespace (default: default)
K8S_JOB_IMAGE=busybox:latest # Container image for jobs
```

---

## Dependencies

```
pyyaml            # Config parsing
fastapi           # REST API framework
uvicorn           # ASGI server (used by Docker)
kubernetes        # K8s Python client
click             # CLI framework
python-multipart  # File upload support
claude-agent-sdk  # Claude AI via Claude Code CLI
```

---

## Troubleshooting

**Claude Agent SDK errors:**
- `CLINotFoundError` — Claude Code CLI not installed. Get it at https://claude.ai/download
- `CLIConnectionError` — Not authenticated. Run `claude` in terminal and log in

**Kubernetes errors:**
- `connection refused` — K8s not running. Enable in Docker Desktop → Settings → Kubernetes
- `namespace not found` — Run `kubectl create namespace default`

---

## License

MIT License

## Security Notes

- Never commit API keys or `.env` files to git
- Use environment variables for sensitive data
- For production, use secrets management (AWS Secrets Manager, Vault, etc.)
