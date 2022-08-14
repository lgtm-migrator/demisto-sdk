import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, List

from demisto_sdk.commands.content_graph.content_graph_builder import \
    ContentGraphBuilder
from demisto_sdk.commands.content_graph.interface.neo4j_graph import \
    Neo4jContentGraphInterface

import neo4j_service
from constants import (NEO4J_DATABASE_URL, NEO4J_PASSWORD, NEO4J_USERNAME,
                       REPO_PATH)

logger = logging.getLogger('demisto-sdk')


class Neo4jContentGraphBuilder(ContentGraphBuilder):
    def __init__(
        self,
        repo_path: Path,
        use_docker: bool = True,
        keep_service: bool = False,
        load_graph: bool = False,
        dump_on_exit: bool = False,
    ) -> None:
        super().__init__(repo_path)
        self.start_time = datetime.now()
        self.end_time = None
        self._content_graph = Neo4jContentGraphInterface(NEO4J_DATABASE_URL, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
        self.use_docker = use_docker
        self.keep_service = keep_service
        self.load_graph = load_graph
        self.dump_on_exit = dump_on_exit

    @property
    def content_graph(self) -> Neo4jContentGraphInterface:
        return self._content_graph

    def __enter__(self):
        if self.load_graph:
            self.load()
        neo4j_service.start_neo4j_service()
        return self


    def load(self):
        if self.use_docker:
            shutil.rmtree(REPO_PATH / 'neo4j' / 'data', ignore_errors=True)
            output = '/backups/content-graph.dump'
        else:
            # todo delete data folder in host (should get it somehow)
            output = (REPO_PATH / 'neo4j' / 'backups' / 'content-graph.dump').as_posix()

        self.neo4j_admin_command('load', f'neo4j-admin load --database=neo4j --from={output}')

    def delete_modified_packs_from_graph(self, packs: List[str]) -> None:
        pass  # todo

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        # self.driver.close()
        if not self.keep_service:
            self.stop_neo4j_service()
            if self.dump_on_exit:
                self.dump()


def create_content_graph(use_docker: bool = True, keep_service: bool = False) -> Neo4jContentGraphInterface:
    shutil.rmtree(REPO_PATH / 'neo4j' / 'data', ignore_errors=True)
    with Neo4jContentGraphBuilder(REPO_PATH, use_docker, keep_service=keep_service, dump_on_exit=True) as content_graph_builder:
        content_graph_builder.create_graph_from_repository()
    return content_graph_builder.content_graph


def load_content_graph(use_docker: bool = True, keep_service: bool = False, content_graph_path: Path = None) -> Neo4jContentGraphInterface:
    if content_graph_path and content_graph_path.is_file():
        shutil.copy(content_graph_path, REPO_PATH / 'neo4j' / 'backups' / 'content-graph.dump')

    with Neo4jContentGraphBuilder(REPO_PATH, use_docker, keep_service, load_graph=True) as content_graph_builder:
        logger.info('Content Graph was loaded')
    return content_graph_builder.content_graph


def stop_content_graph(use_docker: bool = True) -> None:
    with Neo4jContentGraphBuilder(REPO_PATH, use_docker, keep_service=False, load_graph=True):
        logger.info('Content Graph was stopped')
