import weaviate
import os

def establish_connection():
    """
    Establishes connection to Weaviate instance
    """
    client = weaviate.Client(
        url="http://localhost:8080",  # Default Weaviate URL when running locally
    )
    return client

def retrieve_password():
    """
    Retrieves Weaviate API key from environment variable
    """
    return os.getenv('WEAVIATE_API_KEY', 'your-default-key')