"""
This module processes links, determines the resource type, and parses the resources using 
appropriate parsers before adding them to the database. The current implementation uses 
a Weaviate cluster for storage, with interactions handled through weaviate/weaviate_calls.py.
"""

from sch_search.parsers.pdf_parser import parse_pdf
from sch_search.parsers.video_parser import parse_video
from sch_search.parsers.csv_parser import parse_csv

def add_resources(client, links):
    """
    Determines the type of each resource from the provided links and adds them to Weaviate 
    using the corresponding parser.

    Args:
        client: Weaviate client instance for database operations.
        links: List of links or paths to resources.

    Returns:
        None.
    """
    pdf_links = []
    video_links = []
    csvs = []

    for link in links:
        # Define a filter to check if the link already exists in the database
        where_filter = {
            "path": ["document"],
            "operator": "Equal",
            "valueText": link
        }

        # Query the database for existing entries
        data = client.query.get("Post", ["document", "_additional {id}"]) \
            .with_where(where_filter).do()

        # Classify the resource if not already present in the database
        if not data["data"]["Get"]["Post"]:
            if link.endswith('.pdf'):
                pdf_links.append(link)
            elif 'youtube.com' in link or 'youtu.be' in link:
                video_links.append(link)
            elif link.endswith('.csv'):
                csvs.append(link)
            else:
                print('Resource type not recognized:', link)

    # Parse and add resources to the database
    parse_pdf(client, pdf_links)
    parse_video(client, video_links)
    parse_csv(client, csvs)
