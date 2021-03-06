import json
from treelib import Tree
import requests
import validators
from collections import OrderedDict
import urllib
import urlparse

'''
Read a IIIF Collection and generate a treelib tree from it,
which can be rendered as JSON, saved as a standard dict,
or passed out to another service such as a graph databaase,
RDBMS, or key-value store.
'''


def uri_validate(uri):
    '''
    Check if the request URI/URL is in a valid format.
    '''
    if uri is not None:
        if validators.url(uri):
            return True
        else:
            return False


def uri_to_text(uri):
    '''
    Get a text file from a URI, can be http(s) or file.
    '''
    if uri.startswith('file://'):
        f = urllib.url2pathname(urlparse.urlparse(uri).path)
        with open(f) as file:
            got = file.read()
    elif uri.startswith(('http://', 'https://')):
        if uri_validate(uri):
            got = requests.get(uri).text
    else:
        got = None
    return got


def txt_to_dict(text, ordered=False):
    '''
    Turn JSON (as text) into a dict, ordered or not.
    '''
    if ordered:
        j = json.loads(text, object_pairs_hook=OrderedDict)
    else:
        j = json.loads(text)
    return j


class IIIF_Object():

    '''
    Class for working with IIIF objects

    '''

    def __init__(self, uri):
        self.uri = uri
        self.identifier = self.uri
        print 'Identifier %s' % self.identifier
        try:
            text = uri_to_text(self.uri)
            if text:
                self.source_dict = txt_to_dict(text)
            if self.source_dict:
                self.base_data(ns=False)
        except:
            # put some better error handling here.
            print 'Something went wrong.'

    def base_data(self, ns=False):
        '''
        Extract the core IIIF data fields out.
        '''

        core = ['@id', '@type', '@context', 'label', 'description',
                'width', 'height']
        self.data = {}
        for f in core:
            if f in self.source_dict:
                if ns:
                    if ':' in self.source_dict[f]:
                        self.data[f] = self.source_dict[f].split(':')[1]
                    else:
                        self.data[f] = self.source_dict[f]
                else:
                    self.data[f] = self.source_dict[f]


def base_data(source_dict, ns=False):
    '''
    Extract the core IIIF data fields out.

    if ns is set to True, the fields will
    have their namespace stripped out (crudely).

    N.B. the namespace split doesn't work with
    items that use Arks as the ID has a colon in
    it.
    '''

    core = ['@id', '@type', '@context', 'label',
            'description', 'width', 'height']
    data = {}
    for f in core:
        if f in source_dict:
            if ns:
                if ':' in source_dict[f]:
                    if not f == '@id':
                        data[f] = source_dict[f].split(':')[1]
                else:
                    data[f] = source_dict[f]
            else:
                data[f] = source_dict[f]
    return data


def sanitise_uri(uri):
    '''
    Currently uses URL escaping, but could be
    base64 encoding, some other two way function,
    or a simple replace of / with _ or similar.
    '''
    return urllib.quote_plus(uri)


def unsanitise_uri(uri):
    '''
    Function to unsanitise a uri, should be
    the inverse of sanitise_uri.
    '''
    return urllib.unquote(uri)


def de_nid(nid, delimiter):
    '''
    Turn a treelib nid (node id) into a list that can be stored
    and used to create graphs, or ElasticSearch path hierarchies.
    '''
    nid_list = [unsanitise_uri(x) for x in nid.split(delimiter)]
    return nid_list


def iiif_recurse(uri, tr=None, parent_nid=None,
                 separator='/', parent_type=None):
    '''
    Treelib nodes have a tag (human readable), and a nid (node id).

    Sanitised uris are used in the nids, throughout, concatenated
    with the parent id, with a separator, so the path segments can
    be recreated.

    Comments: Nid and denid adds an extra level of list handling, as it joins
    and the splits. Might be better to create the path (no processing)
    and then create the nid.
    '''
    try:
        print 'URI: %s' % uri
        obj = IIIF_Object(uri)
        if not tr:
            tr = Tree()
        if parent_nid:
            root_nid = separator.join([parent_nid, sanitise_uri(uri)])
            if parent_type:
                obj.data['parent_type'] = parent_type
            if not tr.get_node(root_nid):
                tr.create_node(uri, root_nid, parent=parent_nid, data=obj.data)
        else:
            root_nid = sanitise_uri(uri)
            tr.create_node(uri, root_nid, data=obj.data)
        recursion_lists = [
            'members', 'collections', 'manifests', 'sequences', 'canvases']
        dereferenceable = ['sc:Collection', 'sc:Manifest']
        if obj.source_dict:
            dict_parse(obj.source_dict, root_nid, tr, separator,
                       recursion_lists, dereferenceable)
    except:
        raise
    return tr


def dict_parse(dict, root_nid, tree, separator, recursion_lists,
               dereferenceable, parent_type=None):
    '''
    Read a Python dictionary containing a IIIF object or part of
    one.

    Recurse down through the object, generating tree entries.tree

    If the item is of a dereferenceable type, try to follow the
    and recurse into that object, but if not, just keep recursing
    down through the dict (from the JSON) in order to handle any
    inline content.
    '''
    implicit_types = {'collections': 'sc:Collection',
                      'manifests': 'sc:Manifest',
                      'sequences': 'sc:Sequence',
                      'canvases': 'sc:Canvas'}
    for r in recursion_lists:
        if r in dict:
            obj = dict[r]
            implicit_type = implicit_types.setdefault(r, None)
            if '@type' in dict:
                parent_type = dict['@type']
                print 'parent type: %s' % parent_type
            # count = -1
            for item in obj:
                #
                # Not using the ID generation.
                #
                # count += 1
                # if '@id' not in item:
                #     '''
                #     Create a placeholder ID by adding a running count
                #     to the parent id, to handle, e.g. image annotations
                #     that may not have an @id
                #     '''
                #     item['@id'] = '/'.join([de_nid(root_nid, separator)[-1],
                #                             r,
                #                             str(count)])
                item_id = sanitise_uri(item['@id'])
                item_nid = separator.join([root_nid,
                                           item_id])
                item_data = None
                item_data = base_data(item)
                if parent_type:
                    item_data['parent_type'] = parent_type
                if '@type' not in item:
                    item['@type'] = implicit_type
                    item_data['@type'] = implicit_type
                item_data['path'] = de_nid(item_nid,
                                           separator)
                if not tree.get_node(item_nid):
                    print 'Creating node: %s' % item['@id']
                    tree.create_node(
                        item['@id'], item_nid,
                        parent=root_nid, data=item_data)
                if (('@type' in item) and
                        (item['@type'] in dereferenceable)):
                    try:
                        iiif_recurse(item['@id'], tree, root_nid,
                                     parent_type=parent_type)
                    except:
                        print 'Could not dereference uri: %s' % item['@id']
                        dict_parse(
                            item, item_nid, tree, separator,
                            recursion_lists, dereferenceable,
                            parent_type=parent_type
                        )
                else:
                    dict_parse(
                        item, item_nid, tree, separator,
                        recursion_lists, dereferenceable,
                        parent_type=parent_type
                    )


tree = iiif_recurse(
    uri='http://gallica.bnf.fr/iiif/ark:/12148/bpt6k10413011/manifest.json')
tree.show()
with open('man_test.json', 'w') as f:
    json.dump(tree.to_dict(with_data=True), f, indent=4)
