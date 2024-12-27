
import weaviate


def get_pass():
    """
    gets the password for devs
    """
    return PASSWORD

def connect():
    """
    establishes connection to weaviate client
    """
    return weaviate.Client("http://localhost:8080/")

def init_weaviate_schema(client):
    """
    a simple schema containing just a single class for our posts
    """
    schema = {
        "classes": [{
                "class": "Post",
                "properties": [
                    {
                        "name": "content",
                        "dataType": ["text"]
                    },
                    {
                        "name": "document",
                        "dataType": ["text"]
                    },
                    {
                        "name": "page",
                        "dataType": ["text"]
                    },
                    {
                        "name": "paragraph",
                        "dataType": ["text"]
                    },
                    {
                        "name": "type",
                        "dataType": ["text"]
                    },
                    {
                        "name": "title",
                        "dataType": ["text"]
                    },
                    {
                        "name": "person",
                        "dataType": ["text"]
                    },
                    {
                        "name": "role",
                        "dataType": ["text"]
                    },
                    {
                        "name": "folder",
                        "dataType": ["text"]
                    }
                    ]
        }]
    }

    # cleanup from previous runs
    client.schema.delete_all()

    client.schema.create(schema)

    return schema
