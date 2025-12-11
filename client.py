import yaml
import logging
from cli.autodev_cli import run_cli

def load_config():
    with open('autodev.yaml','r') as f:
        return yaml.safe_load(f)

def configure_loggin(level):
    logging.basicConfig(level=getattr(logging,level))

if __name__ == "__main__":
    config = load_config()
    configure_loggin(config['logging']['level'])
    run_cli(config)