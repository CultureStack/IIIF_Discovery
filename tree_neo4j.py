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
    for key, value in dict.iteritems():
        identifier = value['data']['@id']
        if '@type' in value['data']:
            type = value['data']['@type']
        else:
            type = None
        if type:
            if 'manifest' in type.lower():
                parent = value['data']['path'][-2]
                object_node = Node('sc:Manifest', uri=identifier)
                parent_node = Node('sc:Collection', uri=parent)
                graphdb.merge(object_node)
                print 'Obj node'
                graphdb.merge(parent_node)
                print 'Parent node'
                graphdb.merge(Relationship(parent_node,
                                           'hasPart', object_node))
                print 'Relationship'
            elif 'collection' in type.lower():
                object_node = Node('sc:Collection', uri=identifier)
                graphdb.merge(object_node)
                print 'Obj node'
                if 'path' in value['data']:
                    parent = value['data']['path'][-2]
                    parent_node = Node('sc:Collection', uri=parent)
                    graphdb.merge(parent_node)
                    print 'Parent node'
                    graphdb.merge(Relationship(parent_node,
                                               'hasPart', object_node))
                    print 'Relationship'
                for item in value['children']:
                    dict_traverse(item, graphdb)
            else:
                print 'No idea what this is'
        else:
            parent = value['data']['path'][-2]
            object_node = Node('sc:Manifest', uri=identifier)

            parent_node = Node('sc:Collection', uri=parent)
            graphdb.merge(object_node)
            print 'Obj node'
            graphdb.merge(parent_node)
            print 'Parent node'
            graphdb.merge(Relationship(parent_node,
                                       'hasPart', object_node))
            print 'Relationship'


def main():
    g = Graph("http://neo4j:kocicka@localhost:7474/db/data/")
    source = json_loader('bnf.json')
    dict_traverse(source, g)


if __name__ == '__main__':
    main()
