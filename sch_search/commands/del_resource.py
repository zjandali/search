"""
This module processes links and deletes their associated data from the database. 
The current implementation uses a Weaviate cluster, with interactions handled through 
weaviate/weaviate_calls.py.
"""

from sch_search.weaviate.weaviate_calls import delete_link_data

def delete_resources(client, links):
    """
    Deletes Weaviate objects associated with the provided links.

    Args:
        client: Weaviate client instance for database operations.
        links: List of links representing the resources to delete.

    Returns:
        None.
    """
    for link in links:
        delete_link_data(client, link)
