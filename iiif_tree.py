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



def txt_to_ordereddict(text):
    '''
    Turn JSON (as text) into an ordered dict.
    '''
    j = json.loads(text, object_pairs_hook=OrderedDict)
    return j


class IIIF_Collection():

    '''
    Class for working with IIIF Collections.

    iiif_recurse works through a collection and grabs all of the manifests
    recursing down through any collections within collections.
    '''

    def __init__(self, uri):
        self.uri = uri
        print self.uri
        try:
            data_dict = txt_to_ordereddict(uri_to_text(self.uri))
            print data_dict
        except:
            print 'Something went wrong.'


# IIIF_Collection(uri='http://scta.info/iiif/collection/scta')
IIIF_Collection(uri='file:///Users/mmcg/Documents/Work/Github/IIIF_Discovery/scta.json')
