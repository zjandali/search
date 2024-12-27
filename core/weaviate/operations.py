
import weaviate

def search_qa(client, query, limit=10):
    ''' Search for the query using Weaviate's QA feature. Sort results by certainty.
        @params
        query: string to find similar documents
        client: the weaviate client object from calling weaviate_calls_dev.connect()
        limit: the number of results to get
        certainty: the cutoff below which we will not consider a result valid
        @returns dictionary with the query and the results, the results being a dictionary with
            the document, page, paragraph, and content
    '''
    ask = {
      "question": query,
      "properties": ["content"]
    }

    res = client\
        .query.get("Post", ["document","page","paragraph", "content",
                                    "_additional {certainty answer "
                                    "{ hasAnswer certainty startPosition endPosition}}"]).\
        with_ask(ask).with_limit(limit).do()


    answers = []

    if res['data']["Get"]["Post"]:
        for post in res["data"]["Get"]["Post"]:
            answers.append({"document": post['document'], "page": post['page'],
                            "paragraph": post['paragraph'], "content": post['content']})

    return answers




def import_data(client, d_f, batchsize=256):
    ''' Puts the data objects in d_f into weaviate.
        @params
        d_f: pandas dataframe which should have columns Document, Page, Paragraph,
        Text and optionally Titles (plural). Each row will go into
        weaviate as a separate data object.
        batchsize: The rows will be put into weaviate batchsize at a time. Higher numbers are more
            efficient, but if there is a timeout, lower the batchize.
        @returns None
    '''
    batch = weaviate.ObjectsBatchRequest()
    for i, row in d_f.iterrows():
        props = {
            "content": row["Text"],
            "document": row["Document"],
            "page": str(row["Page"]),
            "paragraph": str(row["Paragraph"]),
            "type": str(row["Type"]),
            "title": str(row["Title"]),
            "person": str(row["Person"]),
            "role": str(row["Role"]),
            "folder": str(row["Folder"])
        }
        if 'Titles' in d_f.columns:
            props["content"] = row['Titles'].strip() + '. ' + props["content"]
        batch.add(props, "Post")

        # when either batch size is reached or we are at the last object
        if (i !=0 and i % batchsize == 0) or i == len(d_f) - 1:
            # send off the batch
            client.batch.create(batch)

            # and reset for the next batch
            batch = weaviate.ObjectsBatchRequest()

def link_in_weaviate(client, link):
    """
    returns true if the passed in link is in weaviate
    """
    where_filter = {
        "path": ["document"],
        "operator": "Equal",
        "valueText": link
    }

    data = client.query.get("Post", ["document", "_additional {id}"]).with_where(where_filter).do()
    return len(data["data"]["Get"]["Post"]) != 0


def delete_link_data(client, links):
    ''' Delete all the Weaviate documents that were derived from link.
        @params
        link: a pdf or video link or path that had previously been used to insert documents
        @returns None
    '''
    for link in links:
        any_objects_left = True
        while any_objects_left:
            where_filter = {
                "path": ["document"],
                "operator": "Equal",
                "valueText": link
            }
            data = client.query.get("Post", ["document", "_additional {id}"]).\
                with_where(where_filter).do()
            if data["data"]["Get"]["Post"]:
                for post in data["data"]["Get"]["Post"]:
                    client.data_object.delete(post['_additional']['id'])
            else:
                any_objects_left = False


def search_for_questions(client, query, limit=10):
    ''' Search for the query using Weaviate's QA feature. Sort results by certainty.
        @params
        query: string to find similar documents
        client: the weaviate client object from calling weaviate_calls_dev.connect()
        limit: the number of results to get
        certainty: the cutoff below which we will not consider a result valid
        @returns dictionary with the query and the results, the results being a dictionary with
            the document, page, paragraph, and content
    '''
    ask = {
      "question": query,
      "properties": ["content"]
    }

    res = client\
        .query.get("Post", ["document","page","paragraph", "content",
                                    "_additional {certainty answer "
                                    "{ hasAnswer certainty startPosition endPosition}}"]).\
        with_ask(ask).with_limit(limit).do()

    answers = []

    if res["data"]["Get"]["Post"]:
        for post in res["data"]["Get"]["Post"]:
            answers.append({"document": post['document'], "page": post['page'],
                            "paragraph": post['paragraph'], "content": post['content']})

    return answers
