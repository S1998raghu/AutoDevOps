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

app = FastAPI(title="AutoDevOps API", version="1.0.0")

class JobSubmission(BaseModel):
    job_name: str

class TriageResponse(BaseModel):
    summary: str
    type: str
    suggested_fix: str

@app.get("/")
def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "AutoDevOps"}

@app.post("/api/v1/jobs/submit")
def submit_k8s_job(job: JobSubmission):
    """Submit a job to Kubernetes cluster."""
    try:
        result = submit_job(job.job_name)
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        return result
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