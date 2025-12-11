import click
import subprocess
import time
from ai.triage import analyze_failure
from orchestrator.k8_runner import submit_job

@click.group()
def cli():
    pass


@cli.command()
@click.argument("logfile")
def triage(logfile):
    """Analyze a failure log with AI (standalone mode)."""
    result = analyze_failure(logfile)
    click.echo(result)

@cli.command()
@click.argument("job_name")
@click.option("--repo", "-r", help="Git repository URL to test")
def run(job_name, repo):
    """Submit a job to K8s and auto-analyze failures."""
    click.echo(f"[AutoDev] Submitting job: {job_name}")
    if repo:
        click.echo(f"[AutoDev] Repository: {repo}")

    # 1. Submit the job
    result = submit_job(job_name, repo_url=repo)

    if result.get("status") == "failed":
        click.echo(f"[AutoDev] Failed to submit job: {result.get('error')}")
        return

    namespace = result.get("namespace", "default")
    click.echo(f"[AutoDev] Job submitted successfully!")

    # 2. Wait for job to complete
    click.echo(f"[AutoDev] Waiting for job to complete...")
    max_wait = 300  # 5 minutes timeout
    start_time = time.time()

    while time.time() - start_time < max_wait:
        # Check job status
        status_result = subprocess.run(
            ["kubectl", "get", "job", job_name, "-n", namespace, "-o", "jsonpath={.status.succeeded}"],
            capture_output=True,
            text=True
        )

        failed_result = subprocess.run(
            ["kubectl", "get", "job", job_name, "-n", namespace, "-o", "jsonpath={.status.failed}"],
            capture_output=True,
            text=True
        )

        if status_result.stdout.strip() == "1":
            click.echo("[AutoDev] ✓ Job completed successfully!")
            # Get and show logs
            logs = subprocess.run(
                ["kubectl", "logs", f"job/{job_name}", "-n", namespace],
                capture_output=True,
                text=True
            )
            click.echo(f"\n--- Job Logs ---\n{logs.stdout}")
            return

        if failed_result.stdout.strip() == "1":
            click.echo("[AutoDev] ✗ Job failed!")
            # Get logs
            logs_result = subprocess.run(
                ["kubectl", "logs", f"job/{job_name}", "-n", namespace],
                capture_output=True,
                text=True
            )
            logs = logs_result.stdout

            click.echo(f"\n--- Failure Logs ---\n{logs}")

            # 3. Auto-triage the failure
            click.echo("\n[AutoDev] Running AI triage analysis...")
            analysis = analyze_failure(logs)
            click.echo(f"\n--- AI Analysis ---\n{analysis}")
            return

        time.sleep(5)

    click.echo("[AutoDev] Timeout waiting for job completion")

def run_cli(config):
    cli()
