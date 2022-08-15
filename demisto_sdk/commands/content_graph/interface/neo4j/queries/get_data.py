import logging
from typing import List
from common import run_query, Transaction
from demisto_sdk.commands.common.constants import MarketplaceVersions

from demisto_sdk.commands.content_graph.constants import ContentTypes, Relationship


logger = logging.getLogger('demisto-sdk')


def get_all_content_items(tx: Transaction, marketplace: MarketplaceVersions) -> List[dict]:
    query = f"""
        MATCH (p:{ContentTypes.PACK})<-[:{Relationship.IN_PACK}]-(c:{ContentTypes.BASE_CONTENT})
        WHERE "{marketplace}" IN p.marketplaces
        RETURN p, collect(c)
    """
    return run_query(tx, query).data()
