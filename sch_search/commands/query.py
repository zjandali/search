"""
{Description}
Takes a query, number of results to return, and dictionary of parameters.
Queries database, currently weaviate, through weaviate/weaviate_calls.py
{License_info}
Scholarhub, Inc. 2021
"""
from sch_search.weaviate.weaviate_calls import search_qa

def make_query(client, query):
    """
    Searches weaviate given a query
    """
    return search_qa(client, query)
