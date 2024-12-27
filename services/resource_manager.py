"""
Module to handle addition of various resource types to Weaviate.
Determines resource types, parses content, and uploads to the database.
"""
from processors.doc_parser import process_pdf
from processors.media_parser import process_video
from processors.table_parser import parse_csv
from core.weaviate import remove_resource_data

def add_resources_to_weaviate(client, links):
    """
    Identifies resource types from links and processes them accordingly.
    
    Args:
        client: Weaviate client instance.
        links (list): List of resource URLs or file paths.
    
    Returns:
        None
    """
    pdf_links = []
    video_links = []
    csv_files = []
    
    for link in links:
        # Define filter to check existing entries
        filter_query = {
            "path": ["document"],
            "operator": "Equal",
            "valueText": link
        }

        # Query Weaviate for existing resource
        data = client.query.get("Post", ["document", "_additional {id}"]) \
            .with_where(filter_query).do()

        # Categorize resource if not present
        if not data["data"]["Get"]["Post"]:
            if link.endswith('.pdf'):
                pdf_links.append(link)
            elif 'youtube.com' in link or 'youtu.be' in link:
                video_links.append(link)
            elif link.endswith('.csv'):
                csv_files.append(link)
            else:
                print(f'Unrecognized resource type: {link}')

    # Process and upload resources
    process_pdf(client, pdf_links)
    process_video(client, video_links)
    parse_csv(client, csv_files)



def delete_resources_from_weaviate(client, links):
    """
    Removes specified resources from the Weaviate database.
    
    Args:
        client: Weaviate client instance.
        links (list): List of resource URLs to delete.
    
    Returns:
        None
    """
    for link in links:
        remove_resource_data(client, link)