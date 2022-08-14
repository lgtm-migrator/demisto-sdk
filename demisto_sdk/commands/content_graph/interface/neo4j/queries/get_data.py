import logging
from common import run_query, Transaction, Result

logger = logging.getLogger('demisto-sdk')


def get_all_pack_names(tx: Transaction, marketplace) -> Result:
    query = f"""
        MATCH (p:Pack)
        WHERE {marketplace} in p.marketplaces
        RETURN p.id as id, p.name as name, p.version as version, p.marketplace as marketplace
    """
    return run_query(tx, query)
