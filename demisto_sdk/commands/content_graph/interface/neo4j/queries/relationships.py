import logging
from neo4j import Transaction
from typing import Any, Dict, List

from demisto_sdk.commands.content_graph.common import ContentTypes, Rel
from demisto_sdk.commands.content_graph.interface.neo4j.queries.common import run_query, labels_of


HAS_COMMAND_RELATIONSHIPS_QUERY = f"""
UNWIND $data AS rel_data

// Get all integrations with the specified node_id, fromversion and marketplaces fields
MATCH (integration:{ContentTypes.INTEGRATION}{{
    node_id: rel_data.source,
    fromversion: rel_data.source_fromversion,
    marketplaces: rel_data.source_marketplaces
}})

// Get or create a command with the given object_id
MERGE (cmd:{ContentTypes.COMMAND}{{
    object_id: rel_data.target
}})

// If created, add its node_id, name and marketplaces based on the integration's property
ON CREATE
    SET cmd:{labels_of(ContentTypes.COMMAND)},
        cmd.node_id = "{ContentTypes.COMMAND}:" + rel_data.target,
        cmd.marketplaces = rel_data.source_marketplaces,
        cmd.name = rel_data.name

// Otherwize, add the integration's marketplaces to its marketplaces property 
ON MATCH
    SET cmd.marketplaces = REDUCE(
        marketplaces = cmd.marketplaces, mp IN rel_data.source_marketplaces |
        CASE WHEN NOT mp IN cmd.marketplaces THEN marketplaces + mp ELSE marketplaces END
    )

// Create the relationship
MERGE (integration)-[r:{Rel.HAS_COMMAND}{{
    deprecated: rel_data.deprecated,
    description: rel_data.description
}}]->(cmd)

RETURN count(r) AS relationships_merged
"""

USES_RELATIONSHIPS_QUERY = f"""
UNWIND $data AS rel_data

// Get all content items with the specified node_id, fromversion and marketplaces fields
MATCH (content_item:{ContentTypes.BASE_CONTENT}{{
    node_id: rel_data.source,
    fromversion: rel_data.source_fromversion,
    marketplaces: rel_data.source_marketplaces
}})

// Get or create all dependencies with the given node_id
MERGE (dependency:{ContentTypes.BASE_CONTENT}{{
    node_id: rel_data.target
}})

// If created, mark "not in repository" (all repository nodes were created already)
ON CREATE
    SET dependency.not_in_repository = true

// Get or create the relationship and set its "mandatorily" field based on relationship data
MERGE (content_item)-[r:{Rel.USES}]->(dependency)
ON CREATE
    SET r.mandatorily = rel_data.mandatorily
ON MATCH
    SET r.mandatorily = r.mandatorily OR rel_data.mandatorily

RETURN count(r) AS relationships_merged
"""

USES_RELATIONSHIPS_QUERY_FOR_COMMAND_OR_SCRIPT = f"""
UNWIND $data AS rel_data

// Get all content items with the specified node_id, fromversion and marketplaces fields
MATCH (content_item:{ContentTypes.BASE_CONTENT}{{
    node_id: rel_data.source,
    fromversion: rel_data.source_fromversion,
    marketplaces: rel_data.source_marketplaces
}})

// Get or create all command or script dependencies with the given object_id
MERGE (dependency:{ContentTypes.COMMAND_OR_SCRIPT}{{
    object_id: rel_data.target
}})

// If created, mark "not in repository" (all repository nodes were created already)
ON CREATE
    SET dependency.not_in_repository = true

// Get or create the relationship and set its "mandatorily" field based on relationship data
MERGE (content_item)-[r:{Rel.USES}]->(dependency)
ON CREATE
    SET r.mandatorily = rel_data.mandatorily
ON MATCH
    SET r.mandatorily = r.mandatorily OR rel_data.mandatorily

RETURN count(r) AS relationships_merged
"""


IN_PACK_RELATIONSHIPS_QUERY = f"""
UNWIND $data AS rel_data

// Get the pack and the content item with the specified properties
MATCH (pack:{ContentTypes.PACK}{{node_id: rel_data.target}})
MATCH (content_item:{ContentTypes.BASE_CONTENT}{{
    node_id: rel_data.source,
    fromversion: rel_data.source_fromversion,
    marketplaces: rel_data.source_marketplaces
}})

// Get/create the relationship
MERGE (content_item)-[r:{Rel.IN_PACK}]->(pack)
RETURN count(r) AS relationships_merged
"""


TESTED_BY_RELATIONSHIPS_QUERY = f"""
UNWIND $data AS rel_data

// Get the content item with the specified properties
MATCH (content_item:{ContentTypes.BASE_CONTENT}{{
    node_id: rel_data.source,
    fromversion: rel_data.source_fromversion,
    marketplaces: rel_data.source_marketplaces
}})

// Get or create the test playbook with the given node_id
MERGE (tpb:{ContentTypes.TEST_PLAYBOOK}{{node_id: rel_data.target}})

// If created, mark "not in repository" (all repository nodes were created already)
ON CREATE
    SET tpb.not_in_repository = true

// Get/create the relationship
MERGE (content_item)-[r:{Rel.TESTED_BY}]->(tpb)
RETURN count(r) AS relationships_merged
"""


logger = logging.getLogger('demisto-sdk')


def create_relationships(
    tx: Transaction,
    relationships: Dict[Rel, List[Dict[str, Any]]],
) -> None:
    if relationships.get(Rel.HAS_COMMAND):
        data = relationships.pop(Rel.HAS_COMMAND)
        create_relationships_by_type(tx, Rel.HAS_COMMAND, data)

    for relationship, data in relationships.items():
        create_relationships_by_type(tx, relationship, data)


def create_relationships_by_type(
    tx: Transaction,
    relationship: Rel,
    data: List[Dict[str, Any]],
) -> None:
    if relationship == Rel.HAS_COMMAND:
        query = HAS_COMMAND_RELATIONSHIPS_QUERY
    elif relationship == Rel.USES:
        query = USES_RELATIONSHIPS_QUERY
    elif relationship == Rel.USES_COMMAND_OR_SCRIPT:
        query = USES_RELATIONSHIPS_QUERY_FOR_COMMAND_OR_SCRIPT
    elif relationship == Rel.IN_PACK:
        query = IN_PACK_RELATIONSHIPS_QUERY
    elif relationship == Rel.TESTED_BY:
        query = TESTED_BY_RELATIONSHIPS_QUERY
    else:
        # default query
        query = f"""
            UNWIND $data AS rel_data
            MATCH (source:{ContentTypes.BASE_CONTENT}{{node_id: rel_data.source}})
            MERGE (target:{ContentTypes.BASE_CONTENT}{{node_id: rel_data.target}})
            ON CREATE
                SET target.not_in_repository = true
            MERGE (source)-[r:{relationship}]->(target)
            RETURN count(r) AS relationships_merged
        """

    result = run_query(tx, query, data=data).single()
    merged_relationships_count: int = result['relationships_merged']
    logger.info(f'Merged {merged_relationships_count} relationships of type {relationship}.')


def get_relationships_by_type(tx: Transaction, rel: Rel):
    query = f"""
    MATCH (source)-[rel:{rel}]->(target) return source, rel, target
    """
    return run_query(tx, query).data()
