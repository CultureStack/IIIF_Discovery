from flask import request
import flask
import json
import urllib
from py2neo import Graph


def get_parts(graphdb, query_uri):
    '''
    Get a list of the parts that are hasPart of a particular URI.
    '''
    query_string = 'MATCH (item)-[:hasPart*1..]->(part) WHERE item.uri = "%s" RETURN part.uri' % query_uri.strip(
    )
    print query_string
    p = graphdb.data(query_string)
    parts = [x['part.uri'] for x in p]
    return parts


app = flask.Flask(__name__)


@app.route('/test/neo_parts', methods=['GET', 'POST'])
def neo_parts():
    query_uri = urllib.unquote_plus(request.args.get('uri'))
    g = Graph("http://neo4j:kocicka@localhost:7474/db/data/")
    q = get_parts(g, query_uri)
    r = json.dumps(q, indent=4)
    resp = flask.Response(r)
    return resp

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
