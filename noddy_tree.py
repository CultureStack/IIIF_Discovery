'''
peep peep
'''

import json
import requests
import collections

example_dict = {'key1': 'value1',
                'key2': 'value2',
                'key3': {'key3a': 'value3a'},
                'key4': {'key4a': {'key4aa': 'value4aa',
                                   'key4ab': 'value4ab',
                                   'key4ac': 'value1'},
                         'key4b': 'value4b'}
                }


def keypaths(nested):
    for key, value in nested.iteritems():
        if isinstance(value, collections.Mapping):
            for subkey, subvalue in keypaths(value):
                yield [key] + subkey, subvalue
        else:
            yield [key], value

reverse_dict = {}
for keypath, value in keypaths(example_dict):
    reverse_dict.setdefault(value, []).append(keypath)

print reverse_dict['value4ab']