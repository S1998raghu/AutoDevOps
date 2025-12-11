import click
from ai.triage import analyze_failure
from orchestrator.k8_runner import submit_job

@click.group()
def cli():
    pass


@cli.command()
@click.argument("logfile")
def triage(logfile):
    """Analyze a failure log with AI."""
    result = analyze_failure(logfile)
    click.echo(result)

@cli.command()
@click.argument("job_name")
def run(job_name):
    """Submit a job to K8s (or local simulation)."""
    submit_job(job_name)

def run_cli(config):
    cli()
