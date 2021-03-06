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


def get_recursively(search_dict, field):
    """
    Takes a dict with nested lists and dicts,
    and searches all dicts for a key of the field
    provided.
    """
    fields_found = []

    for key, value in search_dict.iteritems():

        if key == field:
            fields_found.append(value)

        elif isinstance(value, dict):
            results = get_recursively(value, field)
            for result in results:
                fields_found.append(result)

        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    more_results = get_recursively(item, field)
                    for another_result in more_results:
                        fields_found.append(another_result)

    return fields_found


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
        try:
            text = uri_to_text(self.uri)
            if text:
                self.source_dict = txt_to_dict(text)
            if self.source_dict:
                self.base_data(ns=True)
        except:
            # put some better error handling here.
            print 'Something went wrong.'

    def base_data(self, ns):
        '''
        Extract the core IIIF data fields out.

        if ns is set to True, the fields will
        have their namespace stripped out (crudely).
        '''

        core = ['@id', '@type', '@context', 'label', 'description']
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

    core = ['@id', '@type', '@context', 'label', 'description']
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


def iiif_recurse(uri, tr=None, parent_nid=None, separator='/'):
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
        obj = IIIF_Object(uri)
        if not tr:
            tr = Tree()
        if parent_nid:
            root_nid = separator.join([parent_nid, sanitise_uri(uri)])
            if not tr.get_node(root_nid):
                tr.create_node(uri, root_nid, parent=parent_nid, data=obj.data)
                # function here to pass to exteral db
        else:
            root_nid = sanitise_uri(uri)
            tr.create_node(uri, root_nid, data=obj.data)
            # function here to pass to exteral db
        # is it recursing too much here?
        if obj.source_dict:
            print 'Parsing: %s' % obj.identifier
            if 'manifests' in obj.source_dict:
                for manifest in obj.source_dict['manifests']:
                    manifest_id = sanitise_uri(manifest['@id'])
                    manifest_nid = separator.join([root_nid, manifest_id])
                    manifest_data = None
                    manifest_data = base_data(manifest)
                    manifest_data['path'] = de_nid(manifest_nid, separator)
                    if not tr.get_node(manifest_nid):
                        tr.create_node(
                            manifest['@id'], manifest_nid,
                            parent=root_nid, data=manifest_data)
                        # function here to pass to exteral db
            if 'collections' in obj.source_dict:
                collection_lists = get_recursively(
                    obj.source_dict, 'collections')
                for collection_list in collection_lists:
                    for item in collection_list:
                        coll_id = sanitise_uri(item['@id'])
                        coll_nid = separator.join([root_nid, coll_id])
                        coll_data = None
                        coll_data = base_data(item)
                        coll_data['path'] = de_nid(coll_nid, separator)
                        if not tr.get_node(coll_nid):
                            tr.create_node(
                                item['@id'],
                                coll_nid,
                                parent=root_nid,
                                data=coll_data
                            )
                            # function here to pass to exteral db
                        if 'manifests' in item:
                            for manifest in item['manifests']:
                                manifest_id = sanitise_uri(manifest['@id'])
                                manifest_nid = separator.join(
                                    [coll_nid, manifest_id]
                                )
                                manifest_data = None
                                manifest_data = base_data(manifest)
                                manifest_data['path'] = de_nid(
                                    manifest_nid, separator
                                )
                                if not tr.get_node(manifest_nid):
                                    tr.create_node(
                                        manifest['@id'],
                                        manifest_nid,
                                        parent=coll_nid,
                                        data=manifest_data
                                    )
                                    # function here to pass to exteral db
                        else:
                            iiif_recurse(item['@id'], tr, root_nid)
    except:
        pass
    return tr


# tree = iiif_recurse(uri='http://wellcomelibrary.org/service/collections/')
# tree = iiif_recurse(
#     uri="file:////Users/matt.mcgrattan/Documents/Github/IIIF_Discovery/iiif-universe-small.json")
tree = iiif_recurse(uri='http://biblissima.fr/iiif/collection/gallica-bnf/arsenal-library/')
# tree.show()
with open('bnf_manifests.json', 'w') as f:
    json.dump(tree.to_dict(with_data=True), f, indent=4)
