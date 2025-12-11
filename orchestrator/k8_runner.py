import os
import subprocess
import time
import tempfile

def detect_project_type(repo_url: str) -> tuple:
    """Detect project type from repo. Returns (type, image, command)."""
    # Clone repo temporarily to detect type
    temp_dir = tempfile.mkdtemp()
    try:
        subprocess.run(
            ["git", "clone", "--depth", "1", repo_url, temp_dir],
            capture_output=True,
            check=True
        )

        # Check for project files
        if (os.path.exists(os.path.join(temp_dir, "requirements.txt")) or
            os.path.exists(os.path.join(temp_dir, "setup.py")) or
            os.path.exists(os.path.join(temp_dir, "pyproject.toml"))):
            return ("python", "python:3.9",
                   f"git clone {repo_url} /app && cd /app && pip install pytest && (pip install -r requirements.txt 2>/dev/null || pip install -e '.[dev]' 2>/dev/null || pip install -e . 2>/dev/null || true) && pytest")

        elif os.path.exists(os.path.join(temp_dir, "package.json")):
            return ("node", "node:18-alpine",
                   f"git clone {repo_url} /app && cd /app && npm install && npm test")

        elif os.path.exists(os.path.join(temp_dir, "pom.xml")):
            return ("java", "maven:3.8-openjdk-11",
                   f"git clone {repo_url} /app && cd /app && mvn test")

        elif os.path.exists(os.path.join(temp_dir, "go.mod")):
            return ("go", "golang:1.20",
                   f"git clone {repo_url} /app && cd /app && go test ./...")

        else:
            # Default: just clone and list
            return ("generic", "alpine/git:latest",
                   f"git clone {repo_url} /app && ls -la /app")

    finally:
        subprocess.run(["rm", "-rf", temp_dir], capture_output=True)

def submit_job(job_name: str, repo_url: str = None):
    """Submit a job to Kubernetes cluster using kubectl."""
    try:
        namespace = os.getenv("K8S_NAMESPACE", "default")

        # Detect project type and get appropriate image/command
        if repo_url:
            project_type, image, test_command = detect_project_type(repo_url)
            print(f"[AutoDev] Detected project type: {project_type}")
        else:
            # Fallback if no repo provided
            image = os.getenv("K8S_JOB_IMAGE", "busybox:latest")
            test_command = f"echo 'Running job: {job_name}'"

        # Create job YAML
        job_yaml = f"""apiVersion: batch/v1
kind: Job
metadata:
  name: {job_name}
  namespace: {namespace}
spec:
  template:
    metadata:
      labels:
        app: {job_name}
    spec:
      restartPolicy: Never
      containers:
      - name: {job_name}
        image: {image}
        command: ["sh", "-c"]
        args: ["{test_command}"]
"""

        # Apply the job using kubectl
        result = subprocess.run(
            ["kubectl", "apply", "-f", "-"],
            input=job_yaml,
            text=True,
            capture_output=True,
            check=True
        )

        print(f"[AutoDev] Job '{job_name}' created successfully in namespace '{namespace}'")
        print(f"[AutoDev] kubectl output: {result.stdout.strip()}")

        # Get job UID
        uid_result = subprocess.run(
            ["kubectl", "get", "job", job_name, "-n", namespace, "-o", "jsonpath={.metadata.uid}"],
            capture_output=True,
            text=True,
            check=True
        )

        return {
            "job_name": job_name,
            "namespace": namespace,
            "uid": uid_result.stdout.strip(),
            "status": "created"
        }

    except subprocess.CalledProcessError as e:
        print(f"[AutoDev] kubectl error: {e.stderr}")
        return {
            "error": e.stderr,
            "status": "failed"
        }
    except FileNotFoundError:
        print("[AutoDev] kubectl not found. Please install kubectl and configure access to K8s cluster")
        return {
            "error": "kubectl not found",
            "status": "failed"
        }
    except Exception as e:
        print(f"[AutoDev] Error submitting job: {e}")
        return {
            "error": str(e),
            "status": "failed"
        }
