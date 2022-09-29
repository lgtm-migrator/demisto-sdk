import csv
import logging
import shutil
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import List

from neo4j import Transaction

from demisto_sdk.commands.content_graph.interface.neo4j.queries.common import run_query

logger = logging.getLogger('demisto-sdk')


EXPORT_ALL_QUERY = 'call apoc.export.csv.all("content.csv", {bulkImport: true})'


def export_to_csv(
    tx: Transaction,
) -> None:
    run_query(tx, EXPORT_ALL_QUERY)


def get_nodes_files_to_import(import_path: Path):
    nodes_files: List[str] = []
    for file in import_path.iterdir():
        filename = file.name
        if 'content.nodes' in filename:
            nodes_files.append(f'{{fileName: "file:/{filename}", labels: []}}')
    return f'{", ".join(nodes_files)}'


def get_relationships_files_to_import(import_path: Path):
    relationships_files: List[str] = []
    for file in import_path.iterdir():
        filename = file.name
        if 'content.relationships' in filename:
            relationships_files.append(f'{{fileName: "file:/{filename}", type: null}}')
    return f'{", ".join(relationships_files)}'


def import_csv(
    tx: Transaction,
    import_path: Path,
) -> None:
    nodes_files = get_nodes_files_to_import(import_path)
    relationships_files = get_relationships_files_to_import(import_path)
    query = f'CALL apoc.import.csv([{nodes_files}], [{relationships_files}], {{}})'
    run_query(tx, query)
