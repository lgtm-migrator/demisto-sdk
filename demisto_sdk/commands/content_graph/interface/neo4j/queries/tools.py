import logging
from pathlib import Path
from typing import List

from neo4j import Transaction

from demisto_sdk.commands.content_graph.interface.neo4j.queries.common import run_query
from demisto_sdk.commands.content_graph.interface.neo4j.queries.constraints import \
    create_constraints, drop_constraints

logger = logging.getLogger('demisto-sdk')

REPO_NAME = Path.cwd().name  # todo: shou
EXPORT_ALL_QUERY = f'call apoc.export.csv.all("{REPO_NAME}.csv", {{bulkImport: true}})'


def export_to_csv(
    tx: Transaction,
) -> None:
    run_query(tx, EXPORT_ALL_QUERY)


def get_nodes_files_to_import(import_path: Path):
    nodes_files: List[str] = []
    for file in import_path.iterdir():
        filename = file.name
        if '.nodes.' in filename:
            nodes_files.append(f'{{fileName: "file:/{filename}", labels: []}}')
    return f'{", ".join(nodes_files)}'


def get_relationships_files_to_import(import_path: Path):
    relationships_files: List[str] = []
    for file in import_path.iterdir():
        filename = file.name
        if '.relationships.' in filename:
            relationships_files.append(f'{{fileName: "file:/{filename}", type: null}}')
    return f'{", ".join(relationships_files)}'


def pre_import_write_queries(
    tx: Transaction,
) -> None:
    pass


def pre_import_schema_queries(
    tx: Transaction,
) -> None:
    drop_constraints(tx)


def import_csv(
    tx: Transaction,
    import_path: Path,
) -> None:
    nodes_files = get_nodes_files_to_import(import_path)
    relationships_files = get_relationships_files_to_import(import_path)
    run_query(tx, f'CALL apoc.import.csv([{nodes_files}], [{relationships_files}], {{}})')


def post_import_write_queries(
    tx: Transaction,
) -> None:
    remove_unused_properties(tx)
    fix_description_property(tx)
    handle_duplicates(tx)


def post_import_schema_queries(tx: Transaction) -> None:
    create_constraints(tx)


def remove_unused_properties(tx: Transaction) -> None:
    run_query(tx, 'MATCH (n) REMOVE n.__csv_id')
    run_query(tx, 'MATCH ()-[r]->() REMOVE r.__csv_type')


def fix_description_property(tx: Transaction) -> None:
    run_query(tx, """MATCH ()-[r:HAS_COMMAND]->()
SET r.description =
CASE
  WHEN r["description\r"] IS NULL THEN r.description
  ELSE r["description\r"]
END
WITH r
CALL apoc.create.removeRelProperties(r, ["description\r"])
YIELD rel
RETURN *""")


def handle_duplicates(tx: Transaction) -> None:
    merge_duplicate_commands(tx)
    merge_duplicate_content_items(tx)


def merge_duplicate_commands(tx: Transaction) -> None:
    run_query(tx, """MATCH (c:Command)
WITH c.object_id as object_id, collect(c) as cmds
CALL apoc.refactor.mergeNodes(cmds, {properties: "combine", mergeRels: true}) YIELD node
RETURN node
""")


def merge_duplicate_content_items(tx: Transaction) -> None:
    run_query(tx, """MATCH (n:BaseContent{in_repository: false, is_server_item: false})
MATCH (m:BaseContent{object_id: n.object_id, content_type: n.content_type, in_repository: true})
WITH m, n
CALL apoc.refactor.mergeNodes([m, n], {properties: "discard", mergeRels: true}) YIELD node
RETURN node
""")
