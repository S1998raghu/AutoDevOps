import sys
from pathlib import Path

# Add parent directory to path so imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from ai.triage import analyze_failure
from orchestrator.k8_runner import submit_job
import tempfile
import os
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
    triage_analysis: dict = None

class TriageResponse(BaseModel):
    summary: str
    type: str
    suggested_fix: str

@app.get("/")
def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "AutoDevOps"}

@app.post("/api/v1/jobs/submit", response_model=JobResult)
def submit_k8s_job(job: JobSubmission):
    """Submit a job to Kubernetes cluster and optionally wait for completion with auto-triage."""
    try:
        # 1. Submit the job
        result = submit_job(job.job_name, repo_url=job.repo_url)
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        job_name = result["job_name"]
        namespace = result.get("namespace", "default")

        # If not waiting, return immediately
        if not job.wait_for_completion:
            return JobResult(
                job_name=job_name,
                namespace=namespace,
                status="submitted"
            )

        # 2. Wait for completion
        max_wait = 300  # 5 minutes
        start_time = time.time()

        while time.time() - start_time < max_wait:
            # Check if succeeded
            status_result = subprocess.run(
                ["kubectl", "get", "job", job_name, "-n", namespace, "-o", "jsonpath={.status.succeeded}"],
                capture_output=True,
                text=True
            )

            # Check if failed
            failed_result = subprocess.run(
                ["kubectl", "get", "job", job_name, "-n", namespace, "-o", "jsonpath={.status.failed}"],
                capture_output=True,
                text=True
            )

            # Get logs
            logs_result = subprocess.run(
                ["kubectl", "logs", f"job/{job_name}", "-n", namespace],
                capture_output=True,
                text=True
            )
            logs = logs_result.stdout

            if status_result.stdout.strip() == "1":
                return JobResult(
                    job_name=job_name,
                    namespace=namespace,
                    status="succeeded",
                    logs=logs
                )

            if failed_result.stdout.strip() == "1":
                # 3. Auto-triage on failure
                triage_result = analyze_failure(logs)

                return JobResult(
                    job_name=job_name,
                    namespace=namespace,
                    status="failed",
                    logs=logs,
                    triage_analysis=triage_result
                )

            time.sleep(5)

        # Timeout
        raise HTTPException(status_code=408, detail="Job execution timeout")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/triage", response_model=TriageResponse)
async def triage_log(file: UploadFile = File(...)):
    """
    Analyze a failure log file using AI.
    Upload a log file and get AI-powered analysis.
    """
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".log") as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name

        # Analyze the log
        result = analyze_failure(tmp_file_path)

        # Clean up temp file
        os.unlink(tmp_file_path)

        if result.get("type") == "configuration_error" or result.get("type") == "api_error":
            raise HTTPException(status_code=500, detail=result["summary"])

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing log: {str(e)}")

@app.get("/api/v1/health")
def detailed_health():
    """Detailed health check with service status."""
    openai_configured = bool(os.getenv("OPENAI_API_KEY"))

    return {
        "status": "healthy",
        "services": {
            "api": "running",
            "openai": "configured" if openai_configured else "not_configured",
            "kubernetes": "unknown"  # Could add K8s connectivity check
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)