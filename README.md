# AutoDevOps

An AI-powered DevOps automation tool for intelligent failure triage and Kubernetes job orchestration using **real OpenAI API** and **real Kubernetes clusters**.

## Features

- **AI-Powered Triage**: Automatically analyze failure logs using OpenAI GPT-4o-mini and get intelligent suggestions for fixes
- **Real Kubernetes Integration**: Submit and manage jobs on real Kubernetes clusters (Docker Desktop K8s)
- **Dual Interface**:
  - **CLI** for command-line operations
  - **REST API** (FastAPI) for programmatic access
- **Containerized**: Fully Dockerized for easy deployment

## Project Structure

```
AutoDevOps/
├── ai/
│   ├── __init__.py        # Python module marker
│   └── triage.py          # Real OpenAI integration for log analysis
├── cli/
│   ├── __init__.py        # Python module marker
│   └── autodev_cli.py     # CLI commands and interface
├── orchestrator/
│   ├── __init__.py        # Python module marker
│   └── k8_runner.py       # Real Kubernetes job submission
├── service/
│   └── main.py            # FastAPI REST API service
├── client.py              # Main CLI entry point
├── autodev.yaml           # Configuration file
├── .env.example           # Environment variables template
├── sample.log             # Sample error log for testing
├── requirements.txt       # Python dependencies
└── Dockerfile             # Container definition
```

## Prerequisites

- Python 3.11+
- Docker Desktop with Kubernetes enabled
- **OpenAI API Key** with credits - Get one at https://platform.openai.com/api-keys
- **kubectl** configured to connect to Kubernetes

## Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd AutoDevOps
```

### 2. Install Dependencies
```bash
pip3 install -r requirements.txt
```

### 3. Set Up OpenAI API Key

```bash
export OPENAI_API_KEY=sk-your-actual-key-here
```

**Important:** Make sure you have credits in your OpenAI account. Add billing at https://platform.openai.com/account/billing

### 4. Enable Kubernetes in Docker Desktop

1. Open **Docker Desktop**
2. Go to **Settings** → **Kubernetes**
3. Check ☑️ **Enable Kubernetes**
4. Click **Apply & Restart**
5. Wait for green "Kubernetes is running" indicator

Verify:
```bash
kubectl config use-context docker-desktop
kubectl get nodes
```

## Usage

### CLI Interface

#### Test 1: AI Triage (Analyze Logs with OpenAI)

```bash
# Export your API key
export OPENAI_API_KEY=sk-your-key-here

# Analyze the sample log
python3 client.py triage sample.log
```

**What it does:**
- Sends the log file to OpenAI GPT-4o-mini
- Returns summary, error type, and suggested fix

**Example Output:**
```json
{
  "summary": "Build failed due to missing Python dependency requests",
  "type": "dependency_error",
  "suggested_fix": "Install the missing module: pip install requests"
}
```

#### Test 2: Submit Kubernetes Job

```bash
# Submit a job to your K8s cluster
python3 client.py run my-test-job

# Verify it was created
kubectl get jobs
kubectl get pods
kubectl logs job/my-test-job
```

**What it does:**
- Creates a real Kubernetes job on Docker Desktop K8s
- Runs a busybox container that echoes a message

#### Help
```bash
python3 client.py --help
```

---

### REST API (FastAPI)

#### Start the API Server

```bash
# Set your OpenAI key
export OPENAI_API_KEY=sk-your-key-here

# Start the server
python3 service/main.py
```

The API runs at: **http://localhost:8000**

#### Test the Endpoints

**Health Check:**
```bash
curl http://localhost:8000/
# Response: {"status":"ok","service":"AutoDevOps"}

curl http://localhost:8000/api/v1/health
# Response: {"status":"healthy","services":{"api":"running","openai":"configured","kubernetes":"unknown"}}
```

**Submit Kubernetes Job via API:**
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
  "uid": "0fb4804d-3688-4269-94a5-477c4101425e",
  "status": "created"
}
```

**Triage a Log via API:**
```bash
curl -X POST http://localhost:8000/api/v1/triage \
  -F "file=@sample.log"
```

Response:
```json
{
  "summary": "Build failed due to missing Python dependency",
  "type": "dependency_error",
  "suggested_fix": "Run: pip install requests"
}
```

**Interactive API Documentation:**

Open in browser: **http://localhost:8000/docs**

This gives you Swagger UI to test all endpoints interactively!

---

### Docker Deployment

Build and run with Docker:

```bash
# Build the image
docker build -t autodev:latest .

# Run CLI commands
docker run -e OPENAI_API_KEY=sk-your-key autodev:latest python client.py --help

# Run the API server
docker run -p 8000:8000 -e OPENAI_API_KEY=sk-your-key autodev:latest python service/main.py
```

## Configuration

### Environment Variables
```bash
OPENAI_API_KEY=sk-xxx        # Required - Your OpenAI API key
K8S_NAMESPACE=default        # Optional - K8s namespace (default: default)
K8S_JOB_IMAGE=busybox:latest # Optional - Container image for jobs
```

### Application Config (autodev.yaml)
```yaml
environment: "local"
k8s:
  enabled: true
  namespace: "default"
ai:
  provider: "openai"
  model: "gpt-4o-mini"
logging:
  level: "DEBUG"
```

## What We Tested

✅ **AI Triage** - Analyzed sample.log with OpenAI
✅ **K8s Job Submission** - Created job `my-test-job` on Docker Desktop K8s
✅ **FastAPI Server** - Running on http://localhost:8000
✅ **Health Endpoints** - All API endpoints working
✅ **CLI Commands** - Both `triage` and `run` commands functional

## Dependencies

```
pyyaml         # Configuration file parsing
fastapi        # REST API framework
uvicorn        # ASGI server
kubernetes     # K8s Python client
click          # CLI framework
openai         # OpenAI Python SDK
```

Install all:
```bash
pip3 install -r requirements.txt
```

## Troubleshooting

### OpenAI API Errors

**Error: `429 Too Many Requests` or `insufficient_quota`**
- Your OpenAI account has no credits
- Go to https://platform.openai.com/account/billing
- Add a payment method and credits ($5 minimum)

**Error: `Invalid API key`**
- Check your key: `echo $OPENAI_API_KEY`
- Get a new one at https://platform.openai.com/api-keys

### Kubernetes Errors

**Error: `connection refused`**
- Kubernetes isn't running in Docker Desktop
- Enable it: Docker Desktop → Settings → Kubernetes → Enable
- Switch context: `kubectl config use-context docker-desktop`

**Error: `namespace not found`**
- Create it: `kubectl create namespace default`

### Import Errors

**Error: `ModuleNotFoundError: No module named 'ai.triage'`**
- Missing `__init__.py` files in directories
- Already fixed with: `touch ai/__init__.py cli/__init__.py orchestrator/__init__.py`

**Error: Missing dependencies**
```bash
pip3 install -r requirements.txt
```

## How It Works

### Architecture

```
┌─────────────┐         ┌──────────────┐
│   CLI       │────────▶│  OpenAI API  │
│ (client.py) │         │  GPT-4o-mini │
└─────────────┘         └──────────────┘
      │
      │
      ▼
┌─────────────┐         ┌──────────────┐
│  FastAPI    │────────▶│  Kubernetes  │
│ (main.py)   │         │ Docker Desktop│
└─────────────┘         └──────────────┘
```

### Flow:

1. **User** runs `python3 client.py triage sample.log`
2. **client.py** calls `analyze_failure()` from `ai/triage.py`
3. **triage.py** sends log content to OpenAI API
4. **OpenAI** returns analysis (summary, type, fix)
5. **Result** is displayed to user

OR

1. **User** runs `python3 client.py run my-job`
2. **client.py** calls `submit_job()` from `orchestrator/k8_runner.py`
3. **k8_runner.py** connects to K8s cluster via kubectl config
4. **Kubernetes** creates and runs the job
5. **Job status** is returned to user

## License

MIT License

## Security Notes

- Never commit `.env` file or API keys to git
- Use environment variables for sensitive data
- `.env.example` is a template only
- For production, use secrets management (AWS Secrets Manager, etc.)
