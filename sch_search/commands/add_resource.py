""""
{Description}
Takes a link, decides what kind of resource, and passes it through the appropriate
parser before adding it to the database, currently weaviate cluster,
through weaviate/weaviate_calls.py
"""
from sch_search.parsers.pdf_parser import parse_pdf
from sch_search.parsers.video_parser import parse_video
from sch_search.parsers.csv_parser import parse_csv

def add_resources(client, links):
    ''' Figure out what type each resource is and add it to Weaviate using the appropriate
        parser.
        client: Weaviate client
        links: List of links or paths to resources
        Returns nothing.
    '''
    pdf_links = []
    video_links = []
    csvs = []

    for link in links:
        where_filter = {
            "path": ["document"],
            "operator": "Equal",
            "valueText": link
        }
        data = client.query.get("Post", ["document", "_additional {id}"]).\
            with_where(where_filter).do()
        if not data["data"]["Get"]["Post"]:
            if link[-4:] == '.pdf':
                pdf_links.append(link)
            elif 'youtube.com' in link or 'youtu.be' in link:
                video_links.append(link)
            elif link[-4:] == '.csv':
                csvs.append(link)
            else:
                print('not found')

    parse_pdf(client, pdf_links)
    parse_video(client, video_links)
    parse_csv(client, csvs)
