"""
{Description}
Take any dev commands from resource handler and forward them to a database, currently
to weaviate through weaviate/weaviate_calls.py.
{License_info}
Scholarhub, Inc. 2021
Author: Sarah Bhaskaran, Logan Hollmer
Maintainer: Sarah Bhaskaran
"""
from sch_search.weaviate.weaviate_calls_dev import init_weaviate_schema

def reset(client):
    """
    Removes all objects from weaviate
    """
    init_weaviate_schema(client)
