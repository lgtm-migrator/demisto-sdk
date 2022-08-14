import logging

import docker
import requests
from demisto_sdk.commands.common.tools import run_command
from requests.adapters import HTTPAdapter, Retry

from constants import NEO4J_PASSWORD, REPO_PATH

logger = logging.getLogger('demisto-sdk')


def start_neo4j_service(use_docker: bool = True):
    if not use_docker:
        run_command(f'neo4j-admin set-initial-password {NEO4J_PASSWORD}', cwd=REPO_PATH / 'neo4j', is_silenced=False)
        run_command('neo4j start', cwd=REPO_PATH / 'neo4j', is_silenced=False)

    else:
        run_command('docker-compose down', cwd=REPO_PATH / 'neo4j', is_silenced=False)
        run_command('docker-compose up -d', cwd=REPO_PATH / 'neo4j', is_silenced=False)
    # health check to make sure that neo4j is up
    s = requests.Session()

    retries = Retry(
        total=10,
        backoff_factor=0.1
    )

    s.mount('http://localhost', HTTPAdapter(max_retries=retries))
    s.get('http://localhost:7474')


def stop_neo4j_service(use_docker: bool):
    if not use_docker:
        run_command('neo4j stop', cwd=REPO_PATH / 'neo4j', is_silenced=False)
    else:
        run_command('docker-compose down', cwd=REPO_PATH / 'neo4j', is_silenced=False)


def neo4j_admin_command(use_docker: bool, name: str, command: list):
    if not use_docker:
        run_command(command, cwd=REPO_PATH / 'neo4j', is_silenced=False)
    else:
        docker_client = docker.from_env()
        try:
            docker_client.containers.get(f'neo4j-{name}').remove(force=True)
        except Exception as e:
            logger.info(f'Could not remove neo4j container: {e}')
        docker_client.containers.run(image='neo4j/neo4j-admin:4.4.9',
                                     name=f'neo4j-{name}',
                                     remove=True,
                                     volumes=[f'{REPO_PATH}/neo4j/data:/data', f'{REPO_PATH}/neo4j/backups:/backups'],
                                     command=command,
                                     )


def dump(use_docker: bool):
    command = ['neo4j-admin', 'dump', '--database=neo4j', f'--to={"/backups/content-graph.dump" if use_docker else REPO_PATH / "neo4" / "content-graph.dump"}']
    neo4j_admin_command(use_docker, 'dump', command)


def load(use_docker: bool):
    command = ['neo4j-admin', 'load', '--database=neo4j',
               f'--from={"/backups/content-graph.dump" if use_docker else REPO_PATH / "neo4" / "content-graph.dump"}']
    neo4j_admin_command(use_docker, 'load', command)
