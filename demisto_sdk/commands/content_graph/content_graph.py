from abc import ABC, abstractmethod
import multiprocessing
import shutil
import requests
from requests.adapters import HTTPAdapter, Retry

import neo4j
import pickle

from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional, Tuple, Iterator, Dict

from demisto_sdk.commands.content_graph.constants import PACKS_FOLDER, ContentTypes, Rel, MARKETPLACE_PROPERTIES
from demisto_sdk.commands.content_graph.neo4j_query import Neo4jQuery
from demisto_sdk.commands.content_graph.parsers.pack import PackSubGraphCreator
from demisto_sdk.commands.common.git_util import GitUtil
from demisto_sdk.commands.common.content.content import Content
from demisto_sdk.commands.common.tools import run_command

import docker
import logging


DATABASE_URL = 'bolt://localhost:7687'
USERNAME = 'neo4j'
PASSWORD = 'test'
REPO_PATH = Path(GitUtil(Content.git()).git_path())
BATCH_SIZE = 10000
IMPORT_PATH = REPO_PATH / 'neo4j' / 'import'

logger = logging.getLogger('demisto-sdk')

NODES_PKL_PATH = REPO_PATH / 'nodes.pkl'
RELS_PKL_PATH = REPO_PATH / 'rels.pkl'


def load_pickle(url: str) -> Any:
    try:
        with open(url, 'rb') as file:
            return pickle.load(file)
    except Exception:
        return {}


def dump_pickle(url: str, data: Any) -> None:
    with open(url, 'wb') as file:
        file.write(pickle.dumps(data))


class ContentGraph(ABC):
    def __init__(self, repo_path: Path) -> None:
        self.packs_path: Path = repo_path / PACKS_FOLDER
        self.nodes: Dict[ContentTypes, List[Dict[str, Any]]] = load_pickle(NODES_PKL_PATH.as_posix())
        self.relationships: Dict[Tuple[ContentTypes, Rel, ContentTypes], List[Dict[str, Any]]] = \
            load_pickle(RELS_PKL_PATH.as_posix())

    def parse_packs(self, packs_paths: Iterator[Path]) -> None:
        """ Parses packs into nodes and relationships by given paths. """
        if self.nodes and self.relationships:
            print('Skipping parsing.')
            return
        pool = multiprocessing.Pool(processes=4)
        # pool = multiprocessing.Pool(processes=multiprocessing.cpu_count() - 1)
        for pack_nodes, pack_relationships in pool.map(PackSubGraphCreator.from_path, packs_paths):
            self.extend_graph_nodes_and_relationships(pack_nodes, pack_relationships)

    def extend_graph_nodes_and_relationships(
        self,
        pack_nodes: Dict[ContentTypes, List[Dict[str, Any]]],
        pack_relationships: Dict[Tuple[ContentTypes, Rel, ContentTypes], List[Dict[str, Any]]],
    ) -> None:
        for content_type, parsed_data in pack_nodes.items():
            self.nodes.setdefault(content_type, []).extend(parsed_data)

        for rel_key, parsed_data in pack_relationships.items():
            self.relationships.setdefault(rel_key, []).extend(parsed_data)

    def parse_repository(self) -> None:
        """ Parses all repository packs into nodes and relationships. """
        all_packs_paths = self.iter_packs()
        self.parse_packs(all_packs_paths)
        self.add_parsed_nodes_and_relationships_to_graph()
        self.create_pack_dependencies()

    @abstractmethod
    def create_pack_dependencies(self) -> None:
        pass

    def iter_packs(self) -> Iterator[Path]:
        for path in self.packs_path.iterdir():  # todo: handle repo path is invalid
            if path.is_dir() and not path.name.startswith('.'):
                yield path

    @abstractmethod
    def add_parsed_nodes_and_relationships_to_graph(self) -> None:
        pass

    def build_modified_packs_paths(self, packs: List[str]) -> Iterator[Path]:
        for pack_id in packs:
            pack_path = Path(self.packs_path / pack_id)
            if not pack_path.is_dir():
                raise Exception(f'Could not find path of pack {pack_id}.')
            yield pack_path

    def parse_modified_packs(self) -> None:
        packs = self.get_modified_packs()
        self.delete_modified_packs_from_graph(packs)
        packs_paths = self.build_modified_packs_paths(packs)
        self.parse_packs(packs_paths)
        self.add_parsed_nodes_and_relationships_to_graph()

    @abstractmethod
    def delete_modified_packs_from_graph(self, packs: List[str]) -> None:
        pass

    def get_modified_packs(self) -> List[str]:
        return []  # todo


class Neo4jContentGraph(ContentGraph):
    def __init__(
        self,
        repo_path: Path,
        database_uri: str,
        user: str = None,
        password: str = None,
        use_docker: bool = True,
        keep_service: bool = False,
        load_graph: bool = False,
        dump_on_exit: bool = False,
    ) -> None:
        super().__init__(repo_path)
        self.start_time = datetime.now()
        self.end_time = None
        auth: Optional[Tuple[str, str]] = (user, password) if user and password else None
        self.driver: neo4j.Neo4jDriver = neo4j.GraphDatabase.driver(database_uri, auth=auth)
        self.use_docker = use_docker
        self.keep_service = keep_service
        self.load_graph = load_graph
        self.dump_on_exit = dump_on_exit

    def __enter__(self):
        if self.load_graph:
            self.load()
        self.start_neo4j_service()
        return self

    def start_neo4j_service(self, ):
        if not self.use_docker:
            run_command(f'neo4j-admin set-initial-password {PASSWORD}', cwd=REPO_PATH / 'neo4j', is_silenced=False)
            run_command('neo4j start', cwd=REPO_PATH / 'neo4j', is_silenced=False)

        else:
            docker_client = docker.from_env()
            try:
                docker_client.containers.get('neo4j-content').remove(force=True)
            except Exception as e:
                logger.info(f'Could not remove neo4j container: {e}')
            # then we need to create a new one
            shutil.rmtree(REPO_PATH / 'neo4j' / 'data', ignore_errors=True)
            shutil.rmtree(REPO_PATH / 'neo4j' / 'import', ignore_errors=True)
            run_command('docker-compose up -d', cwd=REPO_PATH / 'neo4j', is_silenced=False)
        # health check to make sure that neo4j is up
        s = requests.Session()

        retries = Retry(
            total=10,
            backoff_factor=0.1
        )

        s.mount('http://localhost', HTTPAdapter(max_retries=retries))
        s.get('http://localhost:7474')

    def stop_neo4j_service(self, ):
        if not self.use_docker:
            run_command('neo4j stop', cwd=REPO_PATH / 'neo4j', is_silenced=False)
        else:
            run_command('docker-compose down', cwd=REPO_PATH / 'neo4j', is_silenced=False)

    def neo4j_admin_command(self, name: str, command: str):
        if not self.use_docker:
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
                                         volumes={f'{REPO_PATH}/neo4j/data': {'bind': '/data', 'mode': 'rw'},
                                                  f'{REPO_PATH}/neo4j/backups': {'bind': '/backups', 'mode': 'rw'}},

                                         command=f'{command}'
                                         )

    def dump(self):
        if self.use_docker:
            output = '/backups/content-graph.dump'
        else:
            (REPO_PATH / 'neo4j' / 'backups').mkdir(parents=True, exist_ok=True)
            output = (REPO_PATH / 'neo4j' / 'backups' / 'content-graph.dump').as_posix()
        self.neo4j_admin_command('dump', f'neo4j-admin dump --database=neo4j --to={output}')

    def load(self):
        if self.use_docker:
            shutil.rmtree(REPO_PATH / 'neo4j' / 'data', ignore_errors=True)
            output = '/backups/content-graph.dump'
        else:
            output = (REPO_PATH / 'neo4j' / 'backups' / 'content-graph.dump').as_posix()

        self.neo4j_admin_command('load', f'neo4j-admin load --from={output}')

    @staticmethod
    def create_nodes_keys(tx: neo4j.Transaction) -> None:
        queries: List[str] = []
        queries.extend(Neo4jQuery.create_nodes_keys())
        for query in queries:
            print('Running query:' + query)
            tx.run(query)

    @staticmethod
    def create_constraints(tx: neo4j.Transaction) -> None:
        queries: List[str] = []
        queries.extend(Neo4jQuery.create_nodes_props_uniqueness_constraints())
        # queries.extend(Neo4jQuery.create_nodes_props_existence_constraints())
        # queries.extend(Neo4jQuery.create_relationships_props_existence_constraints())
        for query in queries:
            print('Running query: ' + query)
            tx.run(query)

    def delete_modified_packs_from_graph(self, packs: List[str]) -> None:
        pass  # todo

    def add_parsed_nodes_and_relationships_to_graph(self) -> None:
        dump_pickle(NODES_PKL_PATH.as_posix(), self.nodes)
        dump_pickle(RELS_PKL_PATH.as_posix(), self.relationships)
        # init driver

        before_creating_nodes = datetime.now()
        print(f'Time since started: {(before_creating_nodes - self.start_time).total_seconds() / 60} minutes')

        with self.driver.session() as session:
            tx = session.begin_transaction()
            self.create_nodes_keys(tx)
            self.create_constraints(tx)
            tx.commit()
            tx.close()
            for content_type in ContentTypes.non_abstracts():  # todo: parallelize?
                if self.nodes.get(content_type):
                    session.write_transaction(self.create_nodes_by_type, content_type)
            for rel_key in self.relationships.keys():
                session.write_transaction(self.create_relationships_by_key, rel_key)

        after_creating_nodes = datetime.now()
        print(f'Time to create graph: {(after_creating_nodes - before_creating_nodes).total_seconds() / 60} minutes')
        print(f'Time since started: {(after_creating_nodes - self.start_time).total_seconds() / 60} minutes')

    def create_nodes_by_type(self, tx: neo4j.Transaction, content_type: ContentTypes) -> None:
        query = Neo4jQuery.create_nodes(content_type)
        tx.run(query, {'data': self.nodes.get(content_type)})
        print(f'Imported {content_type}')

    def create_relationships_by_key(
        self,
        tx: neo4j.Transaction,
        rel_key: Tuple[ContentTypes, Rel, ContentTypes],
    ) -> None:
        query = Neo4jQuery.create_relationships(*rel_key)
        tx.run(query, {'data': self.relationships.get(rel_key)})
        print(f'Imported {rel_key}')

    def create_pack_dependencies(self) -> None:
        with self.driver.session() as session:
            session.write_transaction(self.fix_marketplaces_properties)
            session.write_transaction(self.create_depencies_for_all_marketplaces)

    @staticmethod
    def fix_marketplaces_properties(tx: neo4j.Transaction) -> None:
        for property_name in MARKETPLACE_PROPERTIES.values():
            queries = Neo4jQuery.update_marketplace_property(property_name)
            for query in queries:
                tx.run(query)
        print('Fixed marketplaces properties.')

    @staticmethod
    def create_depencies_for_all_marketplaces(tx: neo4j.Transaction) -> None:
        for mp_property in MARKETPLACE_PROPERTIES.values():
            query = Neo4jQuery.create_dependencies_for_marketplace(mp_property)
            tx.run(query)
        print('Created dependencies between packs in all marketplaces.')

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        self.driver.close()
        if not self.keep_service:
            self.stop_neo4j_service()

        if self.dump_on_exit:
            self.dump()


def create_content_graph(use_docker: bool = True, keep_service: bool = False) -> None:
    with Neo4jContentGraph(REPO_PATH, DATABASE_URL, USERNAME, PASSWORD, use_docker, keep_service=keep_service, dump_on_exit=True) as content_graph:
        content_graph.parse_repository()


def load_content_graph(use_docker: bool = True, keep_service: bool = False, content_graph_path: Path = None) -> None:
    if content_graph_path and content_graph_path.is_file():
        shutil.copy(content_graph_path, REPO_PATH / 'neo4j' / 'backups' / 'content-graph.dump')

    with Neo4jContentGraph(REPO_PATH, DATABASE_URL, USERNAME, PASSWORD, use_docker, keep_service, load_graph=True):
        logger.info('Content Graph was loaded')