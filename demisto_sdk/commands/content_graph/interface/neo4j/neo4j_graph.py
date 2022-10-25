import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import neo4j

import demisto_sdk.commands.content_graph.neo4j_service as neo4j_service
from demisto_sdk.commands.common.constants import MarketplaceVersions
from demisto_sdk.commands.content_graph.common import (NEO4J_DATABASE_URL,
                                                       NEO4J_IMPORT_PATH,
                                                       NEO4J_PASSWORD,
                                                       NEO4J_USERNAME,
                                                       ContentType,
                                                       Relationship)
from demisto_sdk.commands.content_graph.interface.graph import \
    ContentGraphInterface
from demisto_sdk.commands.content_graph.interface.neo4j.import_utils import (
    clean_import_dir_before_export,
    fix_csv_files_after_export,
    prepare_csv_files_for_import
)
from demisto_sdk.commands.content_graph.interface.neo4j.queries.constraints import \
    create_constraints
from demisto_sdk.commands.content_graph.interface.neo4j.queries.indexes import \
    create_indexes
from demisto_sdk.commands.content_graph.interface.neo4j.queries.nodes import (
    create_nodes, create_server_nodes, delete_all_graph_nodes, delete_packs_and_their_entities, duplicates_exist,
    get_all_integrations_with_commands, get_nodes_by_type,
    get_packs_content_items, search_nodes)
from demisto_sdk.commands.content_graph.interface.neo4j.queries.relationships import (
    create_relationships, create_server_commands_relationships, get_relationships_by_type)
from demisto_sdk.commands.content_graph.interface.neo4j.queries.tools import (
    export_to_csv,
    import_csv,
    post_import_schema_queries,
    post_import_write_queries,
    pre_import_schema_queries,
    # pre_import_write_queries
)

logger = logging.getLogger('demisto-sdk')


class Neo4jContentGraphInterface(ContentGraphInterface):
    def __init__(
        self,
        start_service: bool = False,
        use_docker: bool = False,
        output_file: Path = None,
    ) -> None:
        self.driver: neo4j.Neo4jDriver = neo4j.GraphDatabase.driver(
            NEO4J_DATABASE_URL,
            auth=(NEO4J_USERNAME, NEO4J_PASSWORD),
        )
        if start_service:
            neo4j_service.start(use_docker)
        self.output_file = output_file
        self.use_docker = use_docker

    def __enter__(self) -> 'Neo4jContentGraphInterface':
        return self

    def __exit__(self, *args) -> None:
        if self.output_file:
            neo4j_service.dump(self.output_file, self.use_docker)
            logger.info(f'Dumped graph to file: {self.output_file}')
        self.driver.close()

    def close(self) -> None:
        self.driver.close()

    def create_indexes_and_constraints(self) -> None:
        with self.driver.session() as session:
            session.write_transaction(create_indexes)
            session.write_transaction(create_constraints)

    def create_server_content_items(self) -> None:
        with self.driver.session() as session:
            session.write_transaction(create_server_nodes)
            session.write_transaction(create_server_commands_relationships)

    def create_nodes(self, nodes: Dict[ContentType, List[Dict[str, Any]]]) -> None:
        with self.driver.session() as session:
            session.write_transaction(create_nodes, nodes)

    def validate_graph(self) -> None:
        with self.driver.session() as session:
            if session.read_transaction(duplicates_exist):
                raise Exception('Duplicates found in graph.')

    def create_relationships(self, relationships: Dict[Relationship, List[Dict[str, Any]]]) -> None:
        with self.driver.session() as session:
            session.write_transaction(create_relationships, relationships)

    def get_packs_content_items(self, marketplace: MarketplaceVersions):
        with self.driver.session() as session:
            return session.read_transaction(get_packs_content_items, marketplace)

    def get_all_integrations_with_commands(self):
        with self.driver.session() as session:
            return session.read_transaction(get_all_integrations_with_commands)

    def clean_graph(self):
        with self.driver.session() as session:
            session.write_transaction(delete_all_graph_nodes)

    def delete_packs(self, packs_to_delete: List[str]) -> None:
        if packs_to_delete:
            with self.driver.session() as session:
                session.write_transaction(delete_packs_and_their_entities, packs_to_delete)

    def get_nodes_by_type(self, content_type: ContentType) -> Any:
        with self.driver.session() as session:
            return session.read_transaction(get_nodes_by_type, content_type)

    def search_nodes(
        self,
        content_type: Optional[ContentType] = None,
        **properties
    ) -> Any:
        with self.driver.session() as session:
            return session.read_transaction(search_nodes, content_type, **properties)

    def get_single_node(
        self,
        content_type: Optional[ContentType] = None,
        **properties
    ) -> Any:
        with self.driver.session() as session:
            return session.read_transaction(search_nodes, content_type, single_result=True, **properties)

    def get_relationships_by_type(self, relationship: Relationship) -> Any:
        with self.driver.session() as session:
            return session.read_transaction(get_relationships_by_type, relationship)

    def import_graphs(self, external_import_paths: List[Path]) -> None:
        import_paths = [NEO4J_IMPORT_PATH] + external_import_paths
        for idx, import_path in enumerate(import_paths, 1):
            prepare_csv_files_for_import(import_path, prefix=str(idx))
        with self.driver.session() as session:
            # session.write_transaction(pre_import_write_queries)
            session.write_transaction(pre_import_schema_queries)
            session.write_transaction(import_csv, NEO4J_IMPORT_PATH)
            session.write_transaction(post_import_write_queries)
            session.write_transaction(post_import_schema_queries)

    def export_graph(self) -> None:
        clean_import_dir_before_export()
        with self.driver.session() as session:
            session.write_transaction(export_to_csv)
        fix_csv_files_after_export()

    def run_single_query(self, query: str, **kwargs) -> neo4j.Result:
        def q(tx: neo4j.Transaction, **kwargs) -> Any:
            return tx.run(query, **kwargs).data()

        with self.driver.session() as session:
            return session.read_transaction(q, **kwargs)
