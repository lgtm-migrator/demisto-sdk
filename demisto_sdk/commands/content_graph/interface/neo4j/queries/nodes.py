import logging
from neo4j import Transaction
from typing import Any, Dict, List, Optional
from demisto_sdk.commands.common.constants import MarketplaceVersions

from demisto_sdk.commands.content_graph.common import ContentTypes, Rel
from demisto_sdk.commands.content_graph.interface.neo4j.queries.common import run_query, versioned, intersects


logger = logging.getLogger('demisto-sdk')


CREATE_NODES_BY_TYPE_TEMPLATE = """
UNWIND $data AS node_data
CREATE (n:{labels}{{id: node_data.id}})
SET n += node_data
RETURN count(n) AS nodes_created
"""

FIND_DUPLICATES = f"""
MATCH (a:{ContentTypes.BASE_CONTENT})
MATCH (b:{ContentTypes.BASE_CONTENT}{'{node_id: a.node_id}'})
WHERE
    id(a) <> id(b)
AND
    {intersects('a.marketplaces', 'b.marketplaces')}
AND
    {versioned('a.toversion')} >= {versioned('b.fromversion')}
AND
    {versioned('b.toversion')} >= {versioned('a.fromversion')}
RETURN count(b) > 0 AS found_duplicates
"""


def create_nodes(
    tx: Transaction,
    nodes: Dict[ContentTypes, List[Dict[str, Any]]],
) -> None:
    for content_type, data in nodes.items():
        create_nodes_by_type(tx, content_type, data)


def duplicates_exist(tx) -> bool:
    result = run_query(tx, FIND_DUPLICATES).single()
    return result['found_duplicates']


def create_nodes_by_type(
    tx: Transaction,
    content_type: ContentTypes,
    data: List[Dict[str, Any]],
) -> None:
    labels: str = ':'.join(content_type.labels)
    query = CREATE_NODES_BY_TYPE_TEMPLATE.format(labels=labels)
    result = run_query(tx, query, data=data).single()
    nodes_count: int = result['nodes_created']
    logger.info(f'Created {nodes_count} nodes of type {content_type}.')


def get_packs_content_items(
    tx: Transaction,
    marketplace: MarketplaceVersions,
):
    query = f"""
    MATCH (p:{ContentTypes.PACK})<-[:{Rel.IN_PACK}]-(c:{ContentTypes.BASE_CONTENT})
    WHERE '{marketplace}' IN p.marketplaces
    RETURN p AS pack, collect(c) AS content_items
    """
    return run_query(tx, query).data()


def get_all_integrations_with_commands(
    tx: Transaction
):
    query = f"""
    MATCH (i:{ContentTypes.INTEGRATION})-[r:{Rel.HAS_COMMAND}]->(c:{ContentTypes.COMMAND})
    WITH i, {{name: c.name, description: r.description, deprecated: r.deprecated}} AS command_data
    RETURN i.object_id AS integration_id, collect(command_data) AS commands
    """
    return run_query(tx, query).data()


def get_nodes_by_type(tx: Transaction, content_type: ContentTypes):
    query = f"""
    MATCH (node:{content_type}) return node
    """
    return run_query(tx, query).data()


def search_nodes(
    tx: Transaction,
    content_type: Optional[ContentTypes] = None,
    single_result: bool = False,
    **properties
):
    if not content_type and properties:
        content_type = ContentTypes.BASE_CONTENT
    content_type_str = f':{content_type}' if content_type else ''
    params_str = ', '.join(f'{k}: "{v}"' for k, v in properties.items())
    params_str = f'{{{params_str}}}' if params_str else ''
    query = f"""
    MATCH (node{content_type_str}{params_str}) return node
    """
    if single_result:
        return run_query(tx, query).single()['node']
    return run_query(tx, query).data()


def delete_all_graph_nodes(
    tx: Transaction
) -> None:
    query = f"""
    MATCH (n)
    DETACH DELETE n
    """
    run_query(tx, query)
