import os
import subprocess
import time
import tempfile

def submit_job(job_name: str):
    """Submit a job to Kubernetes cluster using kubectl."""
    try:
        namespace = os.getenv("K8S_NAMESPACE", "default")
        image = os.getenv("K8S_JOB_IMAGE", "busybox:latest")

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
        command: ["echo", "Running job: {job_name}"]
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
