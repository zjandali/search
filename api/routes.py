"""
Initialize and run the Semantic Data Search application.
"""
from flask import Flask, jsonify, request
from services.resource_manager import add_resources_to_weaviate, delete_resources_from_weaviate
from services.query_service import make_query
from processors.doc_parser import process_pdf
from processors.table_parser import parse_csv
from weaviate import establish_connection, retrieve_password, initialize_schema, link_in_weaviate

client = establish_connection()
app = Flask(__name__)

@app.route('/add_resources', methods=['POST'])
def handle_add_resources():
    """
    Endpoint to add resources to Weaviate.
    """
    data = request.get_json()
    response = {'links_added': [], 'error': 'None'}
    resource_types = ['note', 'post']
    added_links = {}
    request_fields = data.keys()
    
    if 'password' not in request_fields:
        response['error'] = 'PASSWORD REQUIRED IN REQUEST BODY'
    elif data['password'] != retrieve_password():
        response['error'] = 'INVALID PASSWORD'
    else:
        resource_type = data.get('Type')
        if resource_type == 'note':
            for link in data.get('links', []):
                if link_in_weaviate(client, link):
                    added_links[link] = 'ALREADY EXISTS'
                else:
                    add_resources_to_weaviate(client, data['links'])
                    added_links[link] = 'ADDED'
            response['links_added'] = added_links
        elif resource_type == 'post':
            required_fields = ['Topic', 'Title', 'Person', 'Role']
            missing = [field for field in required_fields if field not in request_fields]
            if missing:
                response['error'] = f'MISSING FIELDS: {", ".join(missing)}'
            else:
                add_resources_to_weaviate(client, data['links'])
        else:
            response['error'] = 'UNKNOWN RESOURCE TYPE'
    
    return jsonify(response)

@app.route('/del_resources', methods=['DELETE'])
def handle_delete_resources():
    """
    Endpoint to delete resources from Weaviate.
    """
    data = request.get_json()
    result = {'links_deleted': [], 'error': 'None'}
    
    if 'password' not in data:
        result['error'] = 'PASSWORD REQUIRED IN REQUEST BODY'
    elif data['password'] != retrieve_password():
        result['error'] = 'INVALID PASSWORD'
    else:
        links_to_remove = data.get('links', [])
        delete_resources_from_weaviate(client, links_to_remove)
        result['links_deleted'] = links_to_remove
    
    return jsonify(result)

@app.route('/reset', methods=['DELETE'])
def reset_weaviate_database():
    """
    Endpoint to reset the Weaviate database schema.
    """
    data = request.get_json()
    response = {'error': 'None'}
    
    if 'password' not in data:
        response['error'] = 'PASSWORD REQUIRED IN REQUEST BODY'
    elif data['password'] != retrieve_password():
        response['error'] = 'INVALID PASSWORD'
    else:
        initialize_schema(client)
    
    return jsonify(response)

@app.route('/query_qa', methods=['POST'])
def handle_query_qa():
    """
    Endpoint to perform QA-based queries on Weaviate.
    """
    data = request.get_json()
    query_text = data.get('query', '')
    limit = data.get('limit')
    
    if limit:
        results = query_qa(client, query_text, limit=limit)
    else:
        results = query_qa(client, query_text)
    
    return jsonify(results)

@app.route('/query_basic', methods=['POST'])
def handle_query_basic():
    """
    Endpoint to perform basic searches on Weaviate.
    """
    data = request.get_json()
    query_text = data.get('query', '')
    limit = data.get('limit')
    
    if limit:
        results = query_basic(client, query_text, limit=limit)
    else:
        results = query_basic(client, query_text)
    
    return jsonify(results)

@app.route('/parse_pdf', methods=['POST'])
def handle_parse_pdf():
    """
    Endpoint to parse and upload PDF files.
    """
    data = request.get_json()
    pdf_links = data.get('pdfs', [])
    splitting_method = data.get('splitting', 'naive')
    process_pdf(client, pdf_links, splitting_method)
    return {}

@app.route('/parse_csv', methods=['POST'])
def handle_parse_csv():
    """
    Endpoint to parse and upload CSV files.
    """
    data = request.get_json()
    csv_links = data.get('csv', [])
    process_csv(client, csv_links)
    return {}

if __name__ == '__main__':
    app.config["DEBUG"] = True
    app.run(port=3000)