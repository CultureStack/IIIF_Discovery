'''
Test for grabbing a list of manifests, and then working through
retrieving and extracting data using the IIIF_Manifest class
in iiif_collections.
'''
import json
from iiif_collections import IIIF_Manifest

harvest_list = []

top_level_manifests = json.loads(open('master.json').read())

for top_level_collection in top_level_manifests:
	item = top_level_collection['manifests']
	if len(item)> 0:
		for manifest in item[:1]:
			harvest_list.append(manifest)

for harvest_manifest in harvest_list:
	manifest_item = IIIF_Manifest(harvest_manifest)
	manifest_item.get_manifest_metadata()
	# print json.dumps(json.loads(manifest_item.source_data), sort_keys=True,indent=4)
