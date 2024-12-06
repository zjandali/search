"""
{Description}
Takes a link and passes it through the appropriate parser before deleting it from the database,
currently weaviate cluster, through weaviate/weaviate_calls.py
"""
from sch_search.weaviate.weaviate_calls import delete_link_data

def delete_resources(client, links):
    """
    Deletes weaviate object sourced from links
    """
    for link in links:
        delete_link_data(client, link)
