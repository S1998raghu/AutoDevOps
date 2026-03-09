import sys
from pathlib import Path

# Add parent directory to path so imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from orchestrator.k8_runner import submit_job
import subprocess
import time

app = FastAPI(title="AutoDevOps API", version="1.0.0")

class JobSubmission(BaseModel):
    job_name: str
    repo_url: str = None
    wait_for_completion: bool = True

class JobResult(BaseModel):
    job_name: str
    namespace: str
    status: str
    logs: str = None

@app.get("/")
def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "AutoDevOps"}

@app.post("/api/v1/jobs/submit", response_model=JobResult)
def submit_k8s_job(job: JobSubmission):
    """Submit a job to Kubernetes cluster and optionally wait for completion."""
    try:
        result = submit_job(job.job_name, repo_url=job.repo_url)
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        job_name = result["job_name"]
        namespace = result.get("namespace", "default")

        if not job.wait_for_completion:
            return JobResult(job_name=job_name, namespace=namespace, status="submitted")

        max_wait = 300  # 5 minutes
        start_time = time.time()

        while time.time() - start_time < max_wait:
            status_result = subprocess.run(
                ["kubectl", "get", "job", job_name, "-n", namespace, "-o", "jsonpath={.status.succeeded}"],
                capture_output=True, text=True
            )
            failed_result = subprocess.run(
                ["kubectl", "get", "job", job_name, "-n", namespace, "-o", "jsonpath={.status.failed}"],
                capture_output=True, text=True
            )
            logs_result = subprocess.run(
                ["kubectl", "logs", f"job/{job_name}", "-n", namespace],
                capture_output=True, text=True
            )
            logs = logs_result.stdout

            if status_result.stdout.strip() == "1":
                return JobResult(job_name=job_name, namespace=namespace, status="succeeded", logs=logs)

            if failed_result.stdout.strip() == "1":
                return JobResult(job_name=job_name, namespace=namespace, status="failed", logs=logs)

            time.sleep(5)

        raise HTTPException(status_code=408, detail="Job execution timeout")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/health")
def detailed_health():
    """Detailed health check with service status."""
    return {
        "status": "healthy",
        "services": {
            "api": "running",
            "claude": "configured",
            "kubernetes": "unknown"
        }
    }
