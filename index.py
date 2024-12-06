"""
Starts sch_search application
"""
from flask import jsonify, Flask, request
from sch_search.commands import add_resource, del_resource
from sch_search.weaviate.weaviate_calls_dev import connect, get_pass, init_weaviate_schema
from sch_search.weaviate.weaviate_calls import search_qa, search_basic, link_in_weaviate
from sch_search.parsers.pdf_parser import parse_pdf
from sch_search.parsers.csv_parser import parse_csv


client = connect()
app = Flask(__name__)


@app.route('/add_resources', methods={'POST'})
def resource_parser_res():
    '''
    handles 'resource_parser' request
    adds resources to weaviate
    '''
    data = request.get_json()
    res = {'links added': [], 'error': 'None'}
    types = ['note', 'post']
    links_to_be_added = {}
    fields = data.keys()
    if 'password' not in fields:
        res['error'] = 'MUST INCLUDE PASSWORD IN JSON REQUEST BODY'
    elif data['password'] != get_pass():
        res['error'] = 'INVALID PASSWORD'#make type a post
    else:
        type = data['Type']
        if type == 'note':
            for link in data['links']:
                if link_in_weaviate(client, link):
                    links_to_be_added[link] = 'FILE ALREADY ADDED'
                else:
                    add_resource.add_resources(client, data['links'])
                    links_to_be_added[link] = 'ADDED'
            res['links added'] = links_to_be_added
        elif type == 'post':
            if 'Topic' not in fields:
                res['error'] = 'NO TOPIC GIVEN'
            elif 'Title' not in fields:
                res['error'] = 'NO TITLE GIVEN'
            elif 'Person' not in fields:
                res['error'] = 'NO PERSON LISTED'
            elif 'Role' not in fields:
                res['error'] = "NO ROLE LISTED"
            else:
                add_resource.add_resources(client, data['links'])

    return jsonify(res)


@app.route('/del_resources', methods={'DELETE'})
def del_resource_res():
    '''
    handles 'del_resources' request
    deletes weaviate objects that were generated from the
    resource provided in the request
    '''
    data = request.get_json()
    res = {'links deleted': [], 'error': 'None'}
    if 'password' not in data.keys():
        res['error'] = 'MUST INCLUDE PASSWORD IN JSON REQUEST BODY'
    elif data['password'] != get_pass():
        res['error'] = 'INVALID PASSWORD'
    else:
        del_resource.delete_link_data(client, data['links'])
        for link in data['links']:
            res['links deleted'].append(link)
    return jsonify(res)


@app.route('/reset', methods={'DELETE'})
def reset_weaviate():
    '''
    handles 'reset' request
    removes all data from weaviate
    '''
    data = request.get_json()
    res = {'error': 'None'}
    if 'password' not in data.keys():
        res['error'] = 'MUST INCLUDE PASSWORD IN JSON REQUEST BODY'
    elif data['password'] != get_pass():
        res['error'] = 'INVALID PASSWORD'
    else:
        init_weaviate_schema(client)
    return jsonify(res)


@app.route('/query_qa', methods={'POST'})
def query_qa_res():
    '''
    handles 'query_qa' request
    queries weaviate_qa for data from the query
    provided in the request
    '''
    data = request.get_json()
    if 'limit' in data.keys():
        res = search_qa(client, data['query'], limit=data['limit'])
    else:
        res = search_qa(client, data['query'])
    return jsonify(res)


@app.route('/query_basic', methods={'POST'})
def query_basic_res():
    '''
    handles 'query_basic' request
    queries weaviate_basic for data from the query
    provided in the request
    '''
    data = request.get_json()
    if 'limit' in data.keys():
        res = search_basic(client, data['query'], limit=data['limit'])
    else:
        res = search_basic(client, data['query'])
    return jsonify(res)


@app.route('/parse_pdf', methods={'POST'})
def parse_pdf_request():
    data = request.get_json() #link to pdf
    pdfs = data['pdfs']
    splitting = data['splitting']
    parse_pdf(client, pdfs, splitting)
    return {}

@app.route('/parse_csv', methods={'POST'})
def parse_csv_request():
    """
    Parses the csv
    """
    data = request.get_json()  # link to pdf
    csv = data['csv']
    parse_csv(client, [csv])
    return {}







if __name__ == '__main__':
    app.config["DEBUG"] = True
    app.run(port=3000)
