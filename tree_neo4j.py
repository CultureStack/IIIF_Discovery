from py2neo import Relationship, Node, Graph
import json


def json_loader(file):
    with open(file, 'r') as f:
        text = f.read()
        return json.loads(text)


def insert_object(graph_db, id, type, label=None, description=None):
    graph_db.merge(Node(type, uri=id))


def create_relationship(graph_db, type, item1, item2):
    graph_db.merge(Relationship(item1, type, item2))


def dict_traverse(dict, graphdb):
    '''
    Needs work to handle ranges as a parent type.

    Possible that the data in the graph has to
    include this information gathered at harvest time.
    '''
    parent_types = {'sc:Collection': 'sc:Collection',
                    'sc:Manifest': 'sc:Collection',
                    'collection': 'sc:Collection',
                    'manifest': 'sc:Collection',
                    'sc:Sequence': 'sc:Manifest',
                    'sc:Canvas': 'sc:Sequence'}
    for key, value in dict.iteritems():
        identifier = value['data']['@id']
        if '@type' in value['data']:
            item_type = value['data']['@type']
            parent_type = parent_types.setdefault(item_type, None)
            if parent_type:
                object_node = Node(item_type, uri=identifier)
                graphdb.merge(object_node)
                print 'Obj node: %s' % identifier
                if 'path' in value['data']:
                    parent = value['data']['path'][-2]
                    parent_node = Node(parent_type, uri=parent)
                    graphdb.merge(parent_node)
                    print 'Parent node: %s' % parent
                    graphdb.merge(Relationship(parent_node,
                                               'hasPart', object_node))
                else:
                    print 'Root node: %s' % identifier
            else:
                print 'Cannot set parent type for: %s' % identifier
        else:
            print 'No type available for: %s' % identifier
        if 'children' in value:
            for item in value['children']:
                dict_traverse(item, graphdb)


def main():
    g = Graph("http://neo4j:kocicka@localhost:7474/db/data/")
    # g = Graph("http://neo4j:neo4j@localhost:7474/db/data/")
    source = json_loader('wellcome_light.json')
    dict_traverse(source, g)


if __name__ == '__main__':
    main()
