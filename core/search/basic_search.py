def search_basic(client, query, limit=10):
    """
    Performs a basic semantic search using Weaviate's near_text operator.
    
    Args:
        client: Weaviate client instance
        query (str): Search query text
        limit (int): Maximum number of results to return (default: 10)
    
    Returns:
        list: List of dictionaries containing matching documents with their metadata
    """
    near_vec = {"concepts": [query]}
    
    res = client.query.get("Post", [
        "content",
        "document", 
        "page",
        "paragraph",
        "_additional {certainty}"
    ]).with_near_text(near_vec).with_limit(limit).do()
    
    answers = []
    for post in res["data"]["Get"]["Post"]:
        answers.append({
            "document": post['document'],
            "page": post['page'],
            "paragraph": post['paragraph'],
            "content": post['content']
        })
    
    return answers 