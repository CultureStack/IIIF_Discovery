'''
Module for working with IIIF collections.
'''
# import os
import urllib2
import validators
import json
from pyld import jsonld
from socket import error as SocketError
import errno
import time


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


def unlistify(candidate):
    '''
    Takes a single item list, and returns first item.
    '''
    if isinstance(candidate, list):
        try:
            if len(candidate) == 1:
                return candidate[0]
            else:
                raise ValueError('This list was longer than 1 item')
        except ValueError:
            print 'Unlistify expects single item lists'
    else:
        return candidate


class IIIF_Item():

    '''
    Basic methods for working with IIIF collections.
    '''

    def __init__(self, uri):
        self.uri = uri
        self.uri_validate()
        if self.uri_valid:
            self.uri_type()
        if self.request_type is not None:
            if ((self.request_type is 'http') or
                    (self.request_type is 'https')):
                self.source_data = self.uri_load()
            elif self.request_type is 'file':
                self.source_data = self.file_load()

    def uri_validate(self):
        '''
        Check if the request URI/URL is in a valid format.
        '''
        if self.uri is not None:
            self.uri_valid = validators.url(self.uri)
        else:
            self.uri_valid = False

    def file_load(self):
        '''
        Placeholder for method to load from a local file.
        '''
        pass

    def uri_type(self):
        '''
        Return the type of request to be made, so that
        the correct method for loading the file can be
        used.
        '''
        if self.uri.startswith('file://'):
            self.request_type = 'file'
        elif self.uri.startswith('http://'):
            self.request_type = 'http'
        elif self.uri.startswith('https://'):
            self.request_type = 'https'
        else:
            self.request_type = None

    def uri_load(self):
        '''
        Load the content of a url via urllib2.
        '''
        time.sleep(1)
        if self.uri is not None:
            try:
                req = urllib2.Request(self.uri)
                resp = urllib2.urlopen(req)
                return resp.read()
                # return resp.getcode()
            except urllib2.URLError as e:
                excType = e.__class__.__name__
                return excType
            except SocketError as e:
                if e.errno != errno.ECONNRESET:
                    raise  # Not error we are looking for
                pass  # Handle error here.

    def json_expand(self):
        '''
        Expand the JSON-LD using the context.
        '''
        if self.source_data is not None:
            self.expanded = unlistify(jsonld.expand(
                json.loads(self.source_data)))

    def iiif_type(self):
        '''
        return one word identifying the item as a collection,
        manifest, sequence, canvas, or range
        '''
        try:
            if unlistify(self.expanded['@type']).lower().endswith('#collection'):
                self.resource_type = 'collection'
            elif unlistify(self.expanded['@type']).lower().endswith('#manifest'):
                self.resource_type = 'manifest'
            elif unlistify(self.expanded['@type']).lower().endswith('#sequence'):
                self.resource_type = 'sequence'
            elif unlistify(self.expanded['@type']).lower().endswith('#range'):
                self.resource_type = 'range'
            elif unlistify(self.expanded['@type']).lower().endswith('#canvas'):
                self.resource_type = 'canvas'
            else:
                raise ValueError
        except ValueError:
            'The resource type is not one of Collection, \
            Manifest, Sequence, Canvas, or Range.'


class IIIF_Collection():

    '''
    Class for working with IIIF Collections.

    iiif_recurse works through a collection and grabs all of the manifests
    recursing down through any collections within collections.
    '''

    def __init__(self, uri):
        self.uri = uri
        self.master_manifest_list = []
        self.iiif_recurse(self.uri)
        self.running_list = []

    def iiif_recurse(self, resource_uri):
        try:
            source_data = json.loads(IIIF_Item(resource_uri).source_data)
            if 'collections' in source_data:
                collection_lists = get_recursively(json.loads(
                    IIIF_Item(resource_uri).source_data), 'collections')
                for collection_list in collection_lists:
                    for item in collection_list:
                        item_id = item['@id']
                        print 'Trying: ' + item_id
                        if 'manifests' in item:
                            for manifest in item['manifests']:
                                self.master_manifest_list.append(
                                    {'@id': manifest['@id'],
                                     '@type': 'sc:Manifest',
                                     'label': manifest['label']})
                        else:
                            self.iiif_recurse(item_id)
            elif 'manifests' in source_data:
                for manifest in source_data['manifests']:
                    self.master_manifest_list.append(
                        {'@id': manifest['@id'],
                         '@type': 'sc:Manifest',
                         'label': manifest['label']}
                    )
        except ValueError:
            print 'Could not load that collection as the URI did not return json'


class IIIF_Manifest(IIIF_Item):

    '''
    Class for working with IIIF Manifests. Subclasses IIIF_Item.
    '''

    def get_manifest_metadata(self):
        '''
        Extract the data from the metadata block, and the core data.
        '''
        # self.json_expand()
        self.manifest_dict = json.loads(self.source_data)
        core_fields = ['@id', '@type', 'label', 'description', 'thumbnail', 'attribution', 'logo', 'license']
        for field in core_fields:
            if field in self.manifest_dict:
                print self.manifest_dict[field]
                print '\n'

    def construct_json(self):
        '''
        Create an abbreviated form of the manifest for ingest into ElasticSearch
        or Solr in schemaless mode.

        ? expand fields using the context ?
        '''
        pass
