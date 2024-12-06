
from sch_search.weaviate.weaviate_calls import search_qa

def make_query(client, query):
    """
    Searches weaviate given a query
    """
    return search_qa(client, query)
