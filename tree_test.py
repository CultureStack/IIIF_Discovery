from collections import OrderedDict, defaultdict
from iiif_collections import IIIF_Item, get_recursively
import json
from treelib import Node, Tree
import urllib


class IIIF_Collection():

    '''
    Class for working with IIIF Collections.

    iiif_recurse works through a collection and grabs all of the manifests
    recursing down through any collections within collections.
    '''

    def __init__(self, uri):
        self.uri = uri
        self.master_manifest_list = []
        self.tree = Tree()
        self.iiif_recurse(self.uri)

    def iiif_recurse(self, resource_uri, parent_id=None):
        try:
            source_data = json.loads(IIIF_Item(resource_uri).source_data)
            # print source_data
            if parent_id:
                escaped_id = '/'.join([parent_id,
                                       urllib.quote_plus(resource_uri)])
                if not self.tree.get_node(escaped_id):
                    self.tree.create_node(
                        resource_uri,
                        escaped_id,
                        parent=parent_id)
            else:
                escaped_id = urllib.quote_plus(resource_uri)
                if not self.tree.get_node(escaped_id):
                    self.tree.create_node(
                        resource_uri,
                        escaped_id)
            if 'collections' in source_data:
                collection_lists = get_recursively(json.loads(
                    IIIF_Item(resource_uri).source_data), 'collections')
                for collection_list in collection_lists:
                    for item in collection_list:
                        # print item
                        item_id = item['@id']
                        escaped_item_id = '/'.join([escaped_id,
                                                    urllib.quote_plus(item_id)])
                        # print escaped_item_id
                        if not self.tree.get_node(escaped_item_id):
                            # print 'Creating a collection node'
                            self.tree.create_node(
                                item_id, escaped_item_id,
                                parent=escaped_id)
                        if 'manifests' in item:
                            for manifest in item['manifests']:
                                escaped_manifest_id = '/'.join(
                                    [escaped_item_id, urllib.quote_plus(manifest['@id'])])
                                # print escaped_manifest_id
                                if not self.tree.get_node(escaped_manifest_id):
                                    self.tree.create_node(
                                        manifest[
                                            '@id'], escaped_manifest_id,
                                        parent=escaped_item_id)
                                # print self.tree.get_node(escaped_manifest_id).identifier
                        else:
                            # print 'getting the collection: %s' % item_id 
                            self.iiif_recurse(item_id, parent_id=escaped_id)
            if 'manifests' in source_data:
                # print 'This bit it should be getting manifest'
                for manifest in source_data['manifests']:
                    # print manifest['@id']
                    escaped_manifest_id = '/'.join(
                        [escaped_id, urllib.quote_plus(manifest['@id'])])
                    if not self.tree.get_node(escaped_manifest_id):
                        self.tree.create_node(
                            manifest['@id'],
                            escaped_manifest_id,
                            parent=escaped_id)
        except ValueError:
            print 'Could not load that collection as\
            the URI did not return json'


scta = IIIF_Collection('http://scta.info/iiif/collection/scta')
scta.tree.show()
# print scta.tree.to_json(with_data=False)

# coll = IIIF_Collection('http://digital.library.villanova.edu/Collection/vudl:3/IIIF')
# coll.tree.show()
