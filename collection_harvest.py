'''
Quick and dirty code to take a top level collection of collections,
iterate through the collections, following any link to collections
within those collections, and compiling a list of manifests.

Dumps the list of manifests to a json file.

'''
import iiif_collections
import json

top_list = []
master_list = []

# top_level_collections = json.loads(iiif_collections.IIIF_Item('https://raw.githubusercontent.com/ryanfb/iiif-universe/gh-pages/iiif-universe.json').source_data)
collection_json = open('iiif-universe-medium.json').read()
top_level_collections = json.loads(collection_json)
for top_level_collection in top_level_collections['collections']:
    print 'Working on: ' + top_level_collection['label']
    top_list.append(
        {'@context':
         'http://iiif.io/api/presentation/2/context.json',
         '@id': top_level_collection['@id'],
         '@type': 'sc:Collection',
         'label': top_level_collection['label'],
         'manifests': iiif_collections.IIIF_Collection(
             top_level_collection['@id']).master_manifest_list}
    )

master_list.append(
    {'@context':
     'http://iiif.io/api/presentation/2/context.json',
     '@id': 'https://raw.githubusercontent.com/CultureStack/IIIF_Discovery/master/master.json',
     'label': 'Medium Universe Harvest',
     '@type': 'sc:Collection',
     'description': 'Harvest from IIIF Universe,\
     not including Internet Archive.',
     'collections': top_list})
json.dump(master_list[0], open('master.json', 'wb'), sort_keys=True, indent=4)
