"""
Weaviate schema definitions and initialization functions.
Defines the data structure for the vector database.
"""

def get_default_schema():
    """
    Returns the default Weaviate schema configuration.
    Defines the Post class and its properties for storing various resource types.
    
    Returns:
        dict: Schema configuration dictionary
    """
    return {
        "classes": [{
            "class": "Post",
            "properties": [
                {
                    "name": "content",
                    "dataType": ["text"],
                    "description": "Main content text of the resource"
                },
                {
                    "name": "document",
                    "dataType": ["text"],
                    "description": "Source document identifier or URL"
                },
                {
                    "name": "page",
                    "dataType": ["text"],
                    "description": "Page number within document"
                },
                {
                    "name": "paragraph",
                    "dataType": ["text"],
                    "description": "Paragraph identifier within page"
                },
                {
                    "name": "type",
                    "dataType": ["text"],
                    "description": "Resource type (pdf, video, csv, etc.)"
                },
                {
                    "name": "title",
                    "dataType": ["text"],
                    "description": "Title of the resource"
                },
                {
                    "name": "person",
                    "dataType": ["text"],
                    "description": "Associated person (author, speaker, etc.)"
                },
                {
                    "name": "role",
                    "dataType": ["text"],
                    "description": "Role of the associated person"
                },
                {
                    "name": "folder",
                    "dataType": ["text"],
                    "description": "Organizational folder or category"
                }
            ],
            "vectorizer": "text2vec-transformers",
            "moduleConfig": {
                "text2vec-transformers": {
                    "vectorizeClassName": False
                }
            }
        }]
    }

def init_schema(client):
    """
    Initializes the Weaviate schema.
    If schema already exists, it will be deleted and recreated.
    
    Args:
        client: Weaviate client instance
    
    Returns:
        None
    """
    # Delete existing schema if it exists
    client.schema.delete_all()
    
    # Create new schema
    schema = get_default_schema()
    client.schema.create(schema) 